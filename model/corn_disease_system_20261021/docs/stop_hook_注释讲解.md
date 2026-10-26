# Stop Hook 代码注释讲解

> 对应源码：`src/llm_client.py`（第 65-67、70-173、287、355-373、412-423、459、475、515、520-548 行）  
> 前端事件消费：`frontend/src/views/bigScreen/Layout.vue` 第 1344-1351 行



---

## 0. 先建立心智模型：钩子挂在 agent loop 的哪个位置

`stream_ask_agnes()` 本质是一个「模型 ⇄ 工具」的循环，Stop Hook 只挂在**循环唯一的出口**上：

```
        用户提问
           │
           ▼
   ┌───────────────────────────┐
   │ 请求模型（带 tools）        │◄──────────────┐
   └───────────────────────────┘               │
           │                                   │
           ├── 模型要调工具 ──► 执行 web_search ─┤ 回填 tool 结果
           │                                   │
           └── 模型不调工具了                     │
                   │                           │
                   ▼                           │
        ★ Stop Hook（回合结束钩子）★             │
                   │                           │
        ┌──────────┴──────────┐                │
        │                     │                │
   放行 allow            block + reason        │
        │                     │                │
        ▼                     └── 注入反馈 ─────┘
   输出 done，结束          （最多 MAX_STOP_HOOK_BLOCKS 次）
```

关键点：**钩子不是「停止按钮」，而是「停止前的最后一道关卡」**——它不打断工具执行，而是在模型已经决定不再调工具、准备收尾时介入，判定这一轮回答能不能就这么交出去。

---

## 1. 常量：拦截上限（对应官方 `stop_hook_active` 保护）

```python
# web_search 工具循环上限：到达上限后收走工具，强制模型直接给出最终回答
MAX_TOOL_ROUNDS = 6

# Stop Hook 拦截上限：达到上限后强制放行结束，防止「打回重答」无限循环
# （等价于 Claude Code hooks 中 stop_hook_active 标志的保护语义）
MAX_STOP_HOOK_BLOCKS = 2
```

**为什么必须有这个常量**：hook 是「可以否决停止」的，如果 hook 每次都返回 block，agent 永远停不下来。官方用 `stop_hook_active` 标志做这件事，这里用计数实现——第 3 次 block 请求会被忽略并强制放行。`MAX_TOOL_ROUNDS` 管的是「工具循环」，`MAX_STOP_HOOK_BLOCKS` 管的是「打回重答」，两个上限各管一段，互不干扰。

---

## 2. 内置钩子：`default_stop_hook`（第 82-93 行）

```python
async def default_stop_hook(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """内置 Stop Hook：植保问答最终回答的质量门禁"""
    # payload 是钩子的唯一入参，由调用方组装（见第 5 节），字段：
    #   stop_hook_active : bool  本轮之前是否已经被拦截过（官方同名字段的语义）
    #   message          : str   用户原始提问
    #   reply            : str   本轮模型已流式输出的回答全文（已拼接完成）
    #   tool_rounds      : int   本轮共执行了几轮工具（0 表示没联网，纯知识作答）
    #   context          : dict  大田感知上下文（病害名/置信度/受损率/处方）
    reply = (payload.get("reply") or "").strip()   # 去空白：纯空格等同于空回答

    # 门禁 1：空回答。模型偶尔会只吐一个空 delta 就结束，此时必须打回，
    # 否则前端会留下一条空气泡，用户以为系统卡死。
    if not reply:
        return {"decision": "block", "reason": "本轮回答为空，请直接给出针对用户问题的完整专业回答"}

    # 门禁 2：过短回答。15 字是经验阈值——低于这个长度基本不可能包含
    # 「诊断依据 + 药剂 + 用法」这类植保答案的必要要素。
    if len(reply) < 15:
        return {"decision": "block", "reason": "回答过于简短，缺少植保专业要点，请补充诊断依据与防治处置建议"}

    # 门禁 3：把接口报错当成答案吐给用户。只在「短文本 + 含报错关键词」时判定，
    # 因为长回答里正常提到 "HTTP"（比如讲解 API 对接）不该被误杀。
    err_markers = ["HTTP", "API", "接口异常", "请求失败", "超时", "未知错误"]
    if len(reply) < 60 and any(m in reply for m in err_markers):
        return {"decision": "block", "reason": "回答疑似接口报错信息，请忽略报错并直接给出专业植保建议"}

    # 返回 None 表示放行——这是最常用的出口，绝大多数正常回答走这条路径，
    # 所以默认钩子必须「宽进」，不能把正常回答卡住。
    return None
```

**设计取舍**：内置钩子刻意做成「轻量门禁」而不是「质量评分」。因为钩子在主链路上是**同步阻塞**的，做重活（再调一次大模型打分）会把用户可感知的响应时间拉长，得不偿失。重活应该放在离线评估或自定义钩子里按需开启。

---

## 3. 决策归一化：`_decide_stop`（第 96-126 行）

```python
async def _decide_stop(
    stop_hook: Optional[Callable[[Dict[str, Any]], Any]],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """执行 Stop Hook 并将其返回值归一化为 {"decision": "allow"|"block", "reason": ...}

    hook 未提供时使用 default_stop_hook；hook 自身抛异常时安全放行（不阻塞主流程）。
    """
    # ① 钩子缺省：没传就用内置门禁，保证「不配置也有保护」
    fn = stop_hook or default_stop_hook
    try:
        # ② 同时兼容协程钩子和普通函数钩子：
        #    - 声明成 async def 的直接 await
        #    - 普通函数如果返回了 coroutine（比如 lambda 里套了 async 调用），再 await 一次
        #    这样业务侧写同步校验（读个配置、查个词表）时不用被迫改成 async。
        if asyncio.iscoroutinefunction(fn):
            result = await fn(payload)
        else:
            result = fn(payload)
            if asyncio.iscoroutine(result):
                result = await result
    except Exception as e:
        # ③ 关键容错：钩子是「旁路增强」，它自己崩了绝不能拖垮主问答链路，
        #    所以异常一律降级为放行。这与官方「hook 无法运行时按非阻塞处理」的思路一致。
        logger.warning(f"Stop Hook 执行异常，默认放行结束: {e}")
        return {"decision": "allow"}

    # ④ 返回值归一化：把「多种宽松写法」收敛成唯一的内部契约，
    #    调用方（流式/非流式两处）只需要判断 decision 字段，不用关心钩子怎么写的。
    if result is None or result is True:
        return {"decision": "allow"}          # 不表态 / 显式放行
    if result is False:
        return {"decision": "block", "reason": "回答未通过停止校验"}   # 布尔式否决
    if isinstance(result, str):
        return {"decision": "block", "reason": result}                 # 字符串即理由
    if isinstance(result, dict):
        if result.get("decision") == "block":
            # 官方风格写法：{"decision": "block", "reason": "..."}
            # reason 兜底防止钩子只给 decision 不给理由，导致模型收到空反馈而原地打转
            return {"decision": "block", "reason": str(result.get("reason") or "回答未通过停止校验")}
        return {"decision": "allow"}      # {"decision": "allow"} 或其他字段 → 放行
    return {"decision": "allow"}          # 未知类型一律放行（宁可少拦，不可误拦）
```

**为什么要单独抽这一层**：流式和非流式两条路径都要调钩子，如果各自解析返回值，两处逻辑迟早会漂移。抽成 `_decide_stop` 后，钩子的返回值契约只有一份定义。

---

## 4. 非流式路径：`_stop_hook_finalize_nonstream`（第 129-173 行）

```python
async def _stop_hook_finalize_nonstream(
    client: "httpx.AsyncClient",      # 复用外层已建好的连接，避免重复握手
    url: str,
    headers: Dict[str, str],
    api_messages: List[Dict[str, Any]],   # 就地追加，保持对话历史连续
    reply_text: str,                       # 待校验的候选回答
    *,
    model: str,
    temperature: float,
    max_tokens: int,
    stop_hook: Optional[Callable[[Dict[str, Any]], Any]],
    message: str,
    context: Optional[Dict[str, Any]],
    tool_rounds: int,
) -> str:
    """非流式路径的 Stop Hook：回合结束质量门禁，被拦截时携带反馈重答一次"""
    payload = {
        "stop_hook_active": False,   # 非流式只重答一次，天然不存在无限打回问题
        "message": message,
        "reply": reply_text,
        "tool_rounds": tool_rounds,  # 1=走了工具检索；0=直接作答
        "context": context,
    }
    decision = await _decide_stop(stop_hook, payload)
    if decision.get("decision") != "block":
        return reply_text            # 放行：原样返回，零额外开销

    # ── 以下是「打回重答」分支 ──
    reason = decision.get("reason", "")
    logger.info(f"Stop Hook 拦截非流式回答，携带反馈重答一次: {reason}")

    # 关键三步：把「被打回的回答」当成 assistant 历史 + 把「打回理由」当成 user 消息。
    # 这样模型看到的是一段正常的对话延续，而不是一个突兀的指令，重答质量明显更稳。
    api_messages.append({"role": "assistant", "content": reply_text})
    api_messages.append({"role": "user", "content": f"[stop_hook 反馈] {reason}"})

    try:
        # 注意：重答请求不再携带 tools —— 此时该收集的信息已经收集完，
        # 继续放开工具容易让模型又去联网，把一次修正变成一次新的检索。
        resp = await client.post(url, headers=headers, json={
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if resp.status_code == 200:
            fixed = resp.json()["choices"][0]["message"]["content"]
            if fixed:
                return fixed         # 重答成功：用新回答替换
    except Exception as e:
        # 重答失败不能把用户晾着：降级沿用原回答，至少还有内容可看
        logger.warning(f"Stop Hook 重答请求失败，沿用原回答: {e}")
    return reply_text
```

---

## 5. 流式主路径：钩子挂载点（第 520-548 行）

这是本次改动的**核心**——原来这里只有一句 `break`，现在变成了决策点。

```python
# 本轮无工具调用 → 模型已完成本轮回答，agent loop 即将停止：
# 触发 Stop Hook（回合结束钩子）决定「放行结束」还是「携带反馈打回重答」
if not (is_tool and tool_calls_acc):        # 本轮没有任何 tool_calls，说明模型要收尾了
    hook_payload = {
        # 官方同名字段：告诉钩子「本轮之前是否已经被拦过一次」，
        # 钩子可据此自行决定要不要放宽标准（比如第二次就不再挑剔格式）
        "stop_hook_active": stop_hook_blocks > 0,
        "message": message,                 # 用户原始提问
        "reply": round_content,             # ★ 本轮累积的完整回答（第 515 行逐片累加）
        "tool_rounds": round_idx,           # 已消耗的工具轮数
        "context": context,                 # 大田感知上下文
    }
    decision = await _decide_stop(stop_hook, hook_payload)

    # ── 分支 A：钩子否决 + 还有拦截额度 → 打回重答 ──
    if decision.get("decision") == "block" and stop_hook_blocks < MAX_STOP_HOOK_BLOCKS:
        stop_hook_blocks += 1               # 消耗一次额度（防死循环的关键）
        reason = decision.get("reason", "")
        logger.info(f"Stop Hook 拦截本轮结束(第{stop_hook_blocks}/{MAX_STOP_HOOK_BLOCKS}次): {reason}")

        # 通知前端：这次不是结束，是「打回重答」，UI 需要给用户一个交代，
        # 否则用户会看到文字停住却没有结束标志，误以为连接断了。
        yield f"data: {json.dumps({'type': 'stop_hook', 'action': 'block', 'reason': reason}, ensure_ascii=False)}\n\n"

        # 已流出的部分回答写入对话历史（content 为空时传 None，避免产生空 assistant 消息），
        # 再以 user 消息注入 hook 反馈，模型据此继续完善
        api_messages.append({"role": "assistant", "content": round_content or None})
        api_messages.append({"role": "user", "content": f"[stop_hook 反馈] {reason}"})
        round_idx += 1
        continue                            # ★ 不 break：回到 while 顶部再请求一次模型

    # ── 分支 B：钩子要求拦截但额度已用完 → 强制放行 ──
    if decision.get("decision") == "block":
        # 已达拦截上限，强制放行结束，保证必然终止（stop_hook_active 保护语义）
        logger.info("Stop Hook 再次拦截已达上限，强制放行结束")

    # ── 分支 C：钩子放行（或额度耗尽）→ 通知前端并退出循环 ──
    yield f"data: {json.dumps({'type': 'stop_hook', 'action': 'allow'}, ensure_ascii=False)}\n\n"
    break
```

**三个容易踩的坑，这里都规避了**：

| 坑        | 规避方式                                                           |
| -------- | -------------------------------------------------------------- |
| 打回后死循环   | `stop_hook_blocks < MAX_STOP_HOOK_BLOCKS` 硬闸，最多打回 2 次          |
| 打回后历史错乱  | 必须把已输出的回答补进 `api_messages` 当 assistant 消息，否则下一轮模型会「不知道自己刚说过什么」 |
| 打回后工具又乱调 | 打回时 `round_idx += 1`，继续吃 `MAX_TOOL_ROUNDS` 预算；额度耗尽后工具自然被收走     |

配套的两行小改动（回答累积）：

```python
# 第 475 行：每轮开始前清空，保证 reply 只统计「本轮」而不是整段会话
round_content = ""  # 累积本轮流式回答全文，供 Stop Hook 校验

# 第 515 行：每个 delta 分片都追加，流式输出与校验用同一份文本
round_content += content_piece
```

---

## 6. 前端消费：`Layout.vue` 第 1344-1351 行

```js
} else if (evt.type === 'stop_hook') {
  // Stop Hook（回合结束钩子）：block=回答被打回重答，allow=校验通过即将结束
  // block 时复用 toolStatus 这条状态提示位，用户看到的是「正在重整回答」而不是「卡住了」；
  // allow 时清空提示，紧接着会收到 done 事件收尾。
  toolStatus.value = evt.action === 'block'
    ? '回答未通过停止校验，正在重新组织更完整的回答...'
    : ''
}
```

---

## 7. 怎么接入自定义钩子（不改源码）

`stream_ask_agnes()` / `ask_agnes()` 都新增了 `stop_hook` 参数，传一个函数即可覆盖内置门禁：

```python
# 例：处方合规校验——回答里出现高毒农药就打回
BANNED = ["甲胺磷", "对硫磷", "克百威"]

async def prescription_guard(payload):
    reply = payload["reply"]
    hit = [p for p in BANNED if p in reply]
    if hit:
        return {"decision": "block", "reason": f"回答包含禁用高毒农药 {hit}，请改为推荐低毒合规药剂"}
    if payload["tool_rounds"] == 0 and "价格" in payload["message"]:
        return {"decision": "block", "reason": "该问题涉及实时行情，应先调用 web_search 再作答"}
    return None   # 放行

generator = stream_ask_agnes(message=msg, context=req.context, stop_hook=prescription_guard)
```


````

钩子返回值支持四种写法，等价效果：

```python
return None                                  # 放行
return False                                 # 拦截（通用理由）
return "缺少防治药剂，请补充"                  # 拦截（自定义理由）
return {"decision": "block", "reason": "..."} # 拦截（官方风格）
````

---

## 8. 一句话总结

Stop Hook 在这个项目里承担的角色是：**在 agent loop 唯一的收尾出口上，对「即将交付给农户的最终回答」做一次同步体检**——通过就放行，不合格就带着具体缺陷打回给模型重写，同时用次数上限保证一定会结束。它校验的是「回答质量」，不是「工具执行」；工具执行完只是**触发时机**，不是钩子的职责边界。
