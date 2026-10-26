# AI 植保问答助手 vs Claude Code 源码：差距分析

> 对比对象：`D:\Bohe\claude code 源码\claude-code`（含 `claude-code-system-prompts` 共 176 个提示词片段）
> 被对比对象：`D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021`（问答侧：`src/llm_client.py` + `src/web_search.py`）
> 结论：**问答链路的差距不在"能不能答"，而在"答得可不可信、可不可控、可不可维护"。** 视觉识别侧反而做得比多数同类项目扎实，不在本次差距范围内。

---

## 一、总览对照表

| # | 维度 | Claude Code 的实现（文件:行） | 当前植保助手 | 影响 | 优先级 |
|---|---|---|---|---|---|
| 1 | 输出截断恢复 | `query.ts:168` `MAX_OUTPUT_TOKENS_RECOVERY_LIMIT=3`，命中后注入"Resume directly — no apology, no recap"续写 | `max_tokens=1024`，完全不看 `finish_reason` | 回答在句中戛然而止，用户以为系统坏了 | **P0** |
| 2 | 检索可溯源 | `WebSearchTool/prompt.ts` 强制 `Sources:` + markdown 链接 | `web_search.py:70-93` 只返回摘要文本，**无 URL** | 行情/政策类回答无法核实，专业场景是硬伤 | **P0** |
| 3 | 时效上下文 | `prompts.ts:460` 注入日期；工具描述注入当前年月 | `ROLE_INSTRUCTION` 纯静态，模型不知今夕何年 | 防治窗口期、用药时令判断失真 | **P0** |
| 4 | 请求中止 | 全链路 `AbortController`（`QueryEngine.ts:187/1163`） | 前端 `fetch` 无 `signal`，后端不查断连 | 关掉面板仍在烧 token | **P0** |
| 5 | 失败重试 | `api_retry` 事件 + 指数退避（`QueryEngine.ts:950-953`） | 单个 `except` 直接掉本地兜底 | 瞬时 502 就降级成模板话术 | **P1** |
| 6 | 上下文压缩 | 五层：snip → microcompact → collapse → autocompact → reactive | `history[-6:]` 按条数一刀切 | 长对话丢关键信息或超限 | **P1** |
| 7 | 工具并发 | `StreamingToolExecutor` 边收边执行，并发上限 10 | 整轮结束才串行执行 | 加第 2、3 个工具后延迟叠加 | **P2** |
| 8 | 回合结束钩子 | `query/stopHooks.ts`：block / preventContinuation + 旁路任务（记忆提取、会话摘要） | 只有 block/allow，无旁路任务 | 无法沉淀会话记忆、无法硬终止 | **P1** |
| 9 | 成本与可观测 | `cost-tracker.ts`、`queryCheckpoint`、`logEvent` | 流式路径不统计 usage，靠根目录 `diag_*.py` 手工复现 | 线上问题无法定位、成本不可控 | **P1** |
| 10 | 提示词工程 | `constants/prompts.ts:560-577` 静态段 + 缓存边界 + 动态段注册表 | 一个字符串常量，改一字全量变更 | 无法缓存、无法分场景装配 | **P2** |
| 11 | 工具描述规范 | 何时用/何时不用/强制引用/年份纠正/示例 | 只有"何时该调"，无强制约束 | 模型遵守度低 | **P2** |
| 12 | 回答质量评测 | 有验证型子 agent 与评测脚本 | 只有视觉模型 benchmark，问答零回归测试 | 改 prompt 全靠肉眼 | **P1** |

---

## 二、P0：直接影响农户看到的东西

### 2.1 回答被硬截断，且没有任何恢复机制

**人家怎么做的**——`query.ts` 把"输出超限"当成一种可恢复的循环状态，而不是终态：

```ts
const MAX_OUTPUT_TOKENS_RECOVERY_LIMIT = 3          // query.ts:168

if (maxOutputTokensRecoveryCount < MAX_OUTPUT_TOKENS_RECOVERY_LIMIT) {
  const recoveryMessage = createUserMessage({
    content:
      `Output token limit hit. Resume directly — no apology, no recap of what you were doing. ` +
      `Pick up mid-thought if that is where the cut happened. Break remaining work into smaller pieces.`,
    isMeta: true,
  })
  // 带着 recoveryMessage 回到循环顶部继续生成
  state = next
  continue
}
```

注意两处细节：①先尝试**升级上限**（`max_output_tokens_escalate`，`query.ts:1228`）再走续写；②续写指令明确禁止"抱歉/复述"，避免续写开头出现废话。

**你现在是什么样**——`stream_ask_agnes` 只读 `delta.content`，`finish_reason` 从头到尾没被检查过（`llm_client.py:500-520` 附近），`max_tokens` 固定 1024（`configs/config.yaml` `llm.max_tokens`）。一旦答案超过 1024 token，SSE 流会"自然结束"，前端收到 `done`，用户看到的是半句话，且**没有任何错误提示**。

**怎么补**（最小改动，约 20 行）：

```python
# 在 stream 循环里捕获 finish_reason
finish_reason = choices[0].get("finish_reason")

# 本轮结束后判断是否需要续写
if finish_reason == "length" and resume_count < 3:
    api_messages.append({"role": "assistant", "content": round_content})
    api_messages.append({"role": "user", "content":
        "输出被长度限制截断。直接从中断处继续，不要道歉、不要复述已写内容，必要时拆成更短的段落。"})
    resume_count += 1
    yield f"data: {json.dumps({'type': 'truncated', 'action': 'resume'}, ensure_ascii=False)}\n\n"
    continue
```

顺带把 `max_tokens` 提到 2048~3072——1024 对"诊断依据+药剂+飞防参数"这种结构化回答本来就偏紧。

---

### 2.2 搜索工具不返回来源，回答无法溯源

**人家怎么做的**——把"必须给来源"写进**工具描述**（模型对工具描述里的硬要求遵守度最高）：

```markdown
CRITICAL REQUIREMENT - You MUST follow this:
  - After answering the user's question, you MUST include a "Sources:" section at the end of your response
  - In the list, list all relevant URLs from the search results as markdown hyperlinks: [Title](URL)
  - This is MANDATORY - never skip including sources in your response
IMPORTANT - Use the correct year in search queries:
  - The current month is ${currentMonthYear}. You MUST use this year when searching...
```
（`tools/WebSearchTool/prompt.ts`）

**你现在是什么样**——`src/web_search.py:70-93`：

```python
lines = [f"【互联网最新搜索检索结果（关键词: {q}）】"]
for i, s in enumerate(snippets, 1):
    lines.append(f"{i}. {s}")     # ← 只有摘要，URL 在解析时被 re.sub 剥掉了
```

三个连带问题：
1. **无链接** → 回答里的行情数字、补贴政策农户无法核对，专业可信度打折。
2. **前端文案不实** → `Layout.vue:732` 写的是"已检索**知网植保库**"，实际是百度移动端 + 搜狗抓取。这是给客户看的大屏，文案和实现不一致比功能缺失更伤。
3. **抓取结果无质量信号** → 没有来源域名、没有时间戳，模型无法判断"这是三天前的还是三年前的行情"。

**怎么补**：

```python
# search_baidu_mobile 里保留链接
for m in re.finditer(r'<article[^>]*>(.*?)</article>', text, re.DOTALL):
    art_html = m.group(1)
    url_match = re.search(r'href="(https?://[^"]+)"', art_html)
    title_match = re.search(r'<h3[^>]*>(.*?)</h3>', art_html, re.DOTALL)
    # ...拼成 {title, url, snippet} 三元组，输出时带上 URL
```

然后在 `WEB_SEARCH_TOOL.description` 里加一句硬约束："检索结果含 URL，最终回答涉及外部事实时必须在末尾列出「来源：」并附链接。"前端标签同步改成"已联网检索（百度/搜狗）"。

---

### 2.3 模型不知道"今天几号、什么节气"

**人家怎么做的**——环境信息是系统提示词的**动态段**，每轮可刷新：

```ts
// prompts.ts:499
systemPromptSection('env_info_simple', () =>
  computeSimpleEnvInfo(model, additionalWorkingDirectories),
)
// prompts.ts:452 简化模式下也至少给：CWD + Date
`You are Claude Code...\n\nCWD: ${getCwd()}\nDate: ${getSessionStartDate()}`
```

**你现在是什么样**——`ROLE_INSTRUCTION`（`llm_client.py:32-38`）是一个写死的常量，里面没有日期、没有地域、没有作物生育期。对一个**防治窗口期高度依赖时令**的农业助手，这是结构性缺失：同样问"现在能不能打药"，7 月和 10 月的正确答案完全不同，而模型只能靠猜。

**怎么补**：

```python
def build_env_block(context=None) -> str:
    now = datetime.now()
    # 简易节气/生育期推断（可按需换成农历库）
    season = "夏玉米生长季" if 6 <= now.month <= 9 else "秋收/冬闲期"
    return (
        f"\n【当前环境】\n"
        f"• 日期：{now:%Y年%m月%d日}（第{now.isocalendar().week}周）\n"
        f"• 季节判断：{season}\n"
        f"• 示范区：{context.get('region', '黄淮海夏玉米区') if context else '黄淮海夏玉米区'}\n"
        f"• 涉及实时行情/政策/用药时，搜索词必须带上 {now.year} 年\n"
    )
```

---

### 2.4 用户关掉面板，后端还在跑

**人家怎么做的**——`AbortController` 贯穿全链路：`QueryEngine.ts:187` 持有、`:1163` `abort()`、`toolExecution.ts:415` 每次工具执行前检查 `signal.aborted`、`query.ts:1062` 返回 `reason: 'aborted_streaming'`。

**你现在是什么样**——`Layout.vue:1305`：

```js
const response = await fetch('/api/screen/chat/stream', { method: 'POST', ... })
// ↑ 没有 signal，没有任何取消入口
```

后端 `bigscreen_api.py:459` 把生成器交给 `StreamingResponse` 后也不再管连接是否还活着。结果是：用户关掉灵动岛、或者刷新页面，服务端仍在跑完整个工具循环 + 3 次 stop hook 重答。

**怎么补**：

```js
// 前端
let chatAbort = null
const response = await fetch(url, { ..., signal: (chatAbort = new AbortController()).signal })
// closeIsland() 里：chatAbort?.abort()

// 后端：生成器内加断连检查点
async def stream_ask_agnes(..., request=None):
    if request and await request.is_disconnected():
        logger.info("客户端已断开，终止生成")
        return
```

---

## 三、P1：架构健壮性

### 3.1 没有重试，一次抖动就掉兜底

Claude Code 把重试做成**可观测的流事件**（`QueryEngine.ts:950-953` 推送 `api_retry` + `attempt` + `retryInMs`），前端能显示"第 2 次重试，1.5s 后"。你现在是 `llm_client.py:429` 一个 `except Exception` 直接进本地知识库——**网络瞬断和模型真挂了被同等对待**，而兜底返回的是模板话术，用户会明显感到"AI 变笨了"。

补法：对 429/5xx/`httpx.TimeoutException` 做 2~3 次指数退避（0.8s/1.6s/3.2s），兜底只作为最后一次失败后的出口，并推 `{'type':'retry','attempt':n}` 事件让前端显示。

### 3.2 上下文只按"最近 6 条"截断

Claude Code 有完整压缩栈（`services/compact/`：snip → microcompact → collapse → autocompact → reactive compact），且压缩失败有 `hasAttemptedReactiveCompact` 防死循环（`query.ts:1296-1302` 的注释解释得很清楚：不保留这个 guard 会导致 compact → 仍超长 → 报错 → stop hook 打回 → compact 的无限循环）。

你现在 `llm_client.py:299-308` 是 `history[-6:]`：**按条数不按 token**。一条飞防参数长回答可能就 800 token，6 条直接 5000+；反过来 6 条短问答又浪费预算。而且旧上下文是"整条丢弃"而非摘要，用户第 7 轮问"刚才说的那个药能混配吗"，模型已经忘了。

补法（不必上五层）：估算 token（字符数/1.6 近似）→ 超过 3000 时，把最早的若干轮交给模型做一次 200 字摘要，替换为一条 `{"role":"user","content":"[历史摘要] ..."}`。这是"两层压缩"，投入半天，收益立竿见影。

### 3.3 Stop Hook 只做了一半

对照 `query/stopHooks.ts`，你的实现缺三块：

1. **`preventContinuation` 语义**（`stopHooks.ts:269-280`）：Claude Code 区分「打回重答（block）」和「彻底终止（preventContinuation + stopReason）」。你只有 block/allow，遇到"这个话题不该继续"（比如用户问违规用药）无法硬停。
2. **回合结束的旁路任务**（`stopHooks.ts:136-157`）：它在 turn 结束时 fire-and-forget 跑 prompt 建议、记忆提取、autoDream。你的 hook 是纯阻塞门禁，回合结束后什么也不沉淀——**这就是为什么你的助手没有跨会话记忆**。
3. **错误消息要跳过 hook**（`query.ts:1272-1276`）：

```ts
// Skip stop hooks when the last message is an API error...
// The model never produced a real response — hooks evaluating it create a death spiral:
// error → hook blocking → retry → error → …
if (lastMessage?.isApiErrorMessage) { void executeStopFailureHooks(...); return }
```

你目前用"短文本 + 含报错关键词"的启发式来近似这个判断（`default_stop_hook` 第 90-92 行），能挡住大部分情况，但不如直接给错误回答打标记来得干净。

### 3.4 没有成本与可观测性

Claude Code 有 `cost-tracker.ts`、`costHook.ts`、`queryCheckpoint` 分段计时、`logEvent` 埋点。你的流式路径**完全不统计 usage**（`stream_options.include_usage` 没开），线上出了问题只能靠根目录那堆 `diag_chat_timing.py`、`diag_tool_retest.py` 手工复现。

补法：①请求体加 `stream_options: {"include_usage": True}`，累计 `prompt_tokens/completion_tokens`；②每轮结束落一条结构化日志（`session_id, rounds, tools_used, stop_hook_blocks, tokens, latency_ms`）。这是后续做质量分析和成本控制的唯一依据。

---

## 四、P2：工程化与提示词

### 4.1 提示词是"一坨"，人家是"乐高 + 缓存边界"

```ts
// prompts.ts:560-577
return [
  // --- Static content (cacheable) ---
  getSimpleIntroSection(outputStyleConfig),
  getSimpleSystemSection(),
  getSimpleDoingTasksSection(),
  getActionsSection(),
  getUsingYourToolsSection(enabledTools),
  getSimpleToneAndStyleSection(),
  getOutputEfficiencySection(),
  // === BOUNDARY MARKER - DO NOT MOVE OR REMOVE ===
  ...(shouldUseGlobalCacheScope() ? [SYSTEM_PROMPT_DYNAMIC_BOUNDARY] : []),
  // --- Dynamic content (registry-managed) ---
  ...resolvedDynamicSections,
]
```

两个关键设计：**静态段在前、动态段在后，中间放缓存边界标记**（prompt cache 按前缀命中，动态内容放后面才不会让整段缓存失效）；**每个动态段用 `systemPromptSection(name, fn)` 注册**，可单独失效、单独测试。配合 `claude-code-system-prompts/system-prompts/` 下 176 个独立片段文件，改一句话不会牵动全局。

你的 `ROLE_INSTRUCTION` 是单个字符串常量。建议拆成 5 段：`base`（身份+边界）、`diagnosis`（诊断话术）、`prescription`（用药规范）、`flight`（飞防参数）、`external`（外部事实+引用要求），按意图选装。既降低维护成本，也为将来接支持 `cache_control` 的 API 留好结构。

### 4.2 工具描述缺"可执行约束"

对照 `WEB_SEARCH_TOOL` 与 Claude Code 的 `getWebSearchPrompt()`：

| 要素 | Claude Code | 你的 |
|---|---|---|
| 何时用 | ✅ | ✅（写得还挺好） |
| 何时**不**用 | ✅ 明确列出 | ⚠️ 有但较笼统 |
| 输出格式强制要求 | ✅ 必须 Sources | ❌ 无 |
| 参数级注意事项 | ✅ 年份/域名过滤 | ❌ 无 |
| 示例 | ✅ 给了格式示例 | ❌ 无 |

建议补两句就够：「检索结果包含 URL 时，最终回答末尾必须列出『来源：』并附链接」「查询词必须包含年份和地区，例如『2026 年 山东 玉米 收购价』」。

### 4.3 问答质量没有回归测试

`scripts/benchmark.py`、`model_compare.py` 都在测视觉模型；问答侧改完 prompt 只能人工点几下看效果。建议建一个 20~30 条的"金标准集"，每条标注：**必须出现的关键词**（药剂名/参数值）、**是否应触发搜索**、**禁止出现的内容**（高毒农药）。跑批对比准确率，这才敢持续改 prompt。

---

## 五、不该照搬的部分（重要）

诚实地说，Claude Code 是**命令行编码 agent**，很多机制对"农业问答大屏"是过度设计：

| 机制 | 为什么不建议照搬 |
|---|---|
| 权限模式 + 审批弹窗（`utils/permissions/`） | 你只有一个只读搜索工具，没有任何破坏性操作，加权限门纯属给用户添步骤 |
| 子 agent / 团队协作 / worktree / vim / IDE 桥接 | 编码场景专属，农业问答用不上 |
| 五层压缩栈 | 单轮问答 + 6 条历史，做到"token 估算 + 摘要"两层就够，五层维护成本远超收益 |
| 176 个提示词片段 | 拆 5~6 段足够，再多就是给自己找麻烦 |
| 完整的 hook 事件矩阵（PreToolUse/PostToolUse/SessionStart…） | 你只有 1 个工具，PreToolUse/PostToolUse 的边际价值极低；Stop hook 已是最有价值的一个 |

---

## 六、落地顺序建议

**第一批（1~2 天，全部是 P0）**
1. `max_tokens` 提到 2048 + 检测 `finish_reason=length` 续写（§2.1）
2. 搜索保留 URL + 工具描述加强制引用 + 修掉"知网"文案（§2.2）
3. 系统提示注入日期/季节/产区（§2.3）
4. 前端 AbortController + 后端断连检查（§2.4）

**第二批（2~3 天，P1）**
5. 指数退避重试 + `api_retry` 事件（§3.1）
6. 两层上下文压缩（§3.2）
7. Stop Hook 补 `preventContinuation` + 回合结束异步落会话摘要（§3.3）
8. usage 统计 + 每轮结构化日志（§3.4）

**第三批（按需，P2）**
9. 提示词拆分与场景装配（§4.1）
10. 工具描述补约束（§4.2）
11. 20~30 条金标准问答回归集（§4.3）

---

## 七、一句话总结

**你的助手是"能跑通的 demo 级 agent"，Claude Code 是"可运维的产品级 agent"。** 两者的差距不在模型能力，而在于：**输出是否保证完整（截断恢复）、答案是否可核实（来源引用）、运行是否可控（中止/重试/预算）、问题是否可定位（成本与日志）、提示词是否可维护（分层与评测）。** 这五件事补齐，就跨过了 demo 到产品的门槛；至于子 agent、权限系统、五层压缩这些，留给真正需要的场景。
