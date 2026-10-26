"""Agnes 大语言模型客户端与植保智能专家问答系统。

模型: agnes-3.0-flash
接口规范: OpenAI 兼容 Chat Completions API
特性:
1. 原生支持 Server-Sent Events (SSE) 逐字流式响应 (Stream Output);
2. 集成 web_search 工具调用 (Tool Calling)：当问题超出模型训练数据（如实时行情、农业新闻政策、非本地病害等）时自动触发联网搜索并结合最新信息回答;
3. 融合视觉感知（ResNet50-CBAM 识别结果）、病斑损伤评级、示范区微气候等多源感知上下文;
4. 支持多轮对话历史上下文跟踪;
5. 毫秒级离线专家知识库自动兜底，确保大屏 100% 高可用;
6. Stop Hook（回合结束钩子）：模型完成一轮回答、agent loop 即将停止时触发，可校验最终回答质量
   并决定「放行结束」或「携带反馈打回重答」（语义对齐 Claude Code hooks 的 Stop 事件），
   内置 MAX_STOP_HOOK_BLOCKS 拦截上限防止无限循环（等价于 stop_hook_active 保护）。
"""
from __future__ import annotations

import asyncio
import json
import logging
import os
import re
from datetime import datetime
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional
import httpx

from src.knowledge_base import get_knowledge
from src.web_search import web_search

logger = logging.getLogger("corn_system.llm")

# 默认配置（可通过 config.yaml 覆盖）
DEFAULT_BASE_URL = "https://apihub.agnes-ai.cn/v1"
DEFAULT_API_KEY = os.environ.get("AGNES_API_KEY", "")
DEFAULT_MODEL = "agnes-3.0-flash"
DEFAULT_TIMEOUT = 45.0

# 专家智能体 System 前置设定
ROLE_INSTRUCTION = """你是国家大田数字农业应用创新基地与中国农科院植保所联合研发的「玉米病害精准识别与飞防植保专家大模型」（内核驱动：Agnes-3.0-Flash）。
你配备了通用的实时互联网检索工具 web_search。

【核心专业领域与知识边界判定】:
1. 专业领域核心知识（直接作答）：你精通玉米大斑病、南方锈病、灰斑病及健康长势的病理特征、病斑诊断鉴别要点、致病菌特征、推荐杀菌剂化学防治处方（如苯醚甲环唑、戊唑醇、嘧菌酯等及科学轮换用药）、以及大田无人机飞防作业参数（高度、航速、喷液量、雾滴粒径）和大田微气候防治窗口期。对于这类稳定不变的病理与农艺知识，直接给出结构清晰、权威专业的解答即可，无需检索。
2. 必须检索的情形（优先级高于上一条）：当用户明确要求「查一下 / 搜一下 / 联网 / 上网查 / 检索」时，或问题涉及具体年份与地区的实时行情价格、最新农业政策与新闻公告、当年发布的病虫害预报与防治指导意见时，必须先调用 web_search 拿到真实资料再作答。用户已经明确要求检索时，不得直接作答，也不得声称「我已检索」而未实际调用工具。
3. 工具调用纪律：需要检索就直接调用工具，禁止输出任何文本形式的工具调用（如 <web_search>…</web_search>、<tool_call>…</tool_call>、query: xxx 这类伪代码），那会被判为无效输出。同时禁止旁白式预告（如「好的，收到」「我将为您检索」「正在搜索，请稍候」）——要么直接给答案，要么直接调用工具。
4. 引用溯源：回答中引用了联网检索到的外部事实时，必须在末尾列出「来源：」小节并附 markdown 链接，严禁省略或编造链接。检索失败时如实说明「当前检索不可用」，不得凭旧记忆伪装成检索结果。
5. 回答排版规范：使用清晰自然的 Markdown 格式（适当加粗要点、小标题、分点条目），语言简练专业。"""

# web_search 工具规范声明
WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "联网检索实时互联网信息，返回带标题、摘要与来源 URL 的搜索结果。"
                       "【何时必须调用】① 用户明确要求查一下/搜一下/联网/上网查/检索；"
                       "② 询问实时农产品行情价格、粮价期货；③ 询问最新农业政策、补贴、公告、新闻；"
                       "④ 询问当年或特定年份发布的病虫害预报、防治指导意见。以上情形必须先调用本工具再作答。"
                       "【何时不必调用】玉米病害病理特征、农药用法用量、飞防作业参数等稳定农艺知识，直接作答即可。"
                       "【输出要求】检索结果每条均带「来源」URL：回答引用外部事实时，必须在末尾列出「来源：」小节并附 markdown 链接，严禁省略或编造。"
                       "搜索词必须包含具体年份与地区（如「2026 山东 玉米 收购价」），不要用模糊的时间词。",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "提炼用户问题的核心搜索词，须包含年份与地区",
                }
            },
            "required": ["query"],
        },
    },
}

# web_search 工具循环上限：到达上限后收走工具，强制模型直接给出最终回答
MAX_TOOL_ROUNDS = 6

# Stop Hook 拦截上限：达到上限后强制放行结束，防止「打回重答」无限循环
# （等价于 Claude Code hooks 中 stop_hook_active 标志的保护语义）
MAX_STOP_HOOK_BLOCKS = 2

# 截断续写上限：回答被 max_tokens 截断（finish_reason=length）时，自动注入
# 「从中断处继续」指令的最多次数（对齐 Claude Code 的 MAX_OUTPUT_TOKENS_RECOVERY_LIMIT）
MAX_RESUME_ROUNDS = 3


# 强制工具调用（对齐 Claude Code `tool_choice: {type:'tool', name:'web_search'}`，
# 见 tools/WebSearchTool/WebSearchTool.ts:281）：用户明确要求检索时不允许模型拒绝调用
FORCE_SEARCH_CHOICE = {"type": "function", "function": {"name": "web_search"}}

# 用户显式要求联网检索的动作词（排除「检查/调查/审核」这类非检索语义的「查」）
_SEARCH_INTENT_RE = re.compile(r"(?<![检调审核复抽])(查一?下|查查|查下|搜一?下|搜搜|去查|去搜|帮我查|帮我搜)|联网|上网|检索|搜索")
# 强外部事实主题：命中即视为需要实时外部信息，首轮强制检索
_EXTERNAL_TOPIC_KEYWORDS = ("价格", "行情", "收购", "粮价", "多少钱", "期货", "政策", "补贴", "新闻", "公告", "通报")


def wants_search(message: str) -> bool:
    """判断用户是否显式要求/隐含需要联网检索。

    只用于「是否首轮强制调用工具」，不影响工具是否声明——工具始终声明，
    最终调不调由模型决定（Claude Code 从不按关键词裁剪工具声明，见 query.ts:674）。
    """
    if not message:
        return False
    return bool(_SEARCH_INTENT_RE.search(message)) or any(k in message for k in _EXTERNAL_TOPIC_KEYWORDS)


def _extract_pseudo_query(block: str) -> str:
    """从文本形态的伪工具调用块里抽出检索词"""
    text = re.sub(r"</?[^>]+>", " ", block or "")
    m = re.search(r'["\']?query["\']?\s*[:=]\s*["\']?([^"\'\n}]+)', text, re.I)
    if m and m.group(1).strip():
        return m.group(1).strip()[:120]
    for line in text.splitlines():
        line = line.strip(" \t,;，；")
        if len(line) >= 2:
            return line[:120]
    return ""


class PseudoToolCallGuard:
    """拦截正文里伪装成文本的工具调用，并回收其中的检索词。

    背景：OpenAI 兼容网关降级、或模型拿不到原生 tools 声明时，模型会把工具调用
    写成正文 `<web_search>query: xxx</web_search>`。这类文本会被原样流给用户，
    变成"嘴上说检索、实际没检索"的假动作。本拦截器做三件事：
      1. 流式安全：标记可能被拆进多个 delta，维护未决缓冲区，只有确认尾部不再是
         标记前缀时才放行，避免把半个 `<web_search` 吐给用户；
      2. 捕获：命中开标记后停止放行，直到闭合标记，抽出检索词存到 self.query；
      3. 复用：调用方看到 self.query 非空，就把它当成一次真实工具调用来执行检索。
    """

    OPENERS = ("<web_search", "<tool_call", "<function_call", "<function=", "<invoke", "<antml:invoke")
    CLOSERS = ("</web_search>", "</tool_call>", "</function_call>", "</invoke>", "</antml:invoke>")

    def __init__(self) -> None:
        self._buf = ""        # 未决缓冲区（可能构成标记前缀的尾部）
        self._capture: Optional[str] = None  # 进入捕获模式后的原文
        self.query: Optional[str] = None     # 捕获到的检索词；非 None 表示命中伪工具调用

    def feed(self, piece: str) -> str:
        """喂入一个流式分片，返回可立即安全推送的文本"""
        if not piece:
            return ""
        self._buf += piece

        if self._capture is not None:
            self._capture += self._buf
            self._buf = ""
            return self._close_if_found()

        low = self._buf.lower()
        hit = -1
        for marker in self.OPENERS:
            i = low.find(marker)
            if i != -1 and (hit == -1 or i < hit):
                hit = i
        if hit != -1:
            safe = self._buf[:hit]
            self._capture = self._buf[hit:]
            self._buf = ""
            return safe + self._close_if_found()

        # 未命中标记：把可能是标记前缀的尾部留下，其余放行
        keep = 0
        low_tail = self._buf.lower()
        for marker in self.OPENERS:
            for k in range(min(len(marker) - 1, len(self._buf)), 0, -1):
                if low_tail.endswith(marker[:k]):
                    keep = max(keep, k)
                    break
        if keep:
            safe, self._buf = self._buf[:-keep], self._buf[-keep:]
            return safe
        safe, self._buf = self._buf, ""
        return safe

    def _close_if_found(self) -> str:
        """捕获模式下检查闭合标记；命中则解析检索词并把闭合后的内容重新走一遍 feed"""
        assert self._capture is not None
        low = self._capture.lower()
        for closer in self.CLOSERS:
            i = low.find(closer)
            if i != -1:
                block = self._capture[:i]
                rest = self._capture[i + len(closer):]
                self._capture = None
                q = _extract_pseudo_query(block)
                if q and not self.query:
                    self.query = q
                return self.feed(rest) if rest else ""
        return ""

    def flush(self) -> str:
        """流结束时收尾：未闭合的捕获块也按伪调用处理，剩余缓冲一律放行"""
        tail = self._buf
        self._buf = ""
        if self._capture is not None:
            block, self._capture = self._capture, None
            q = _extract_pseudo_query(block)
            if q and not self.query:
                self.query = q
            return tail
        return tail


# ─────────────────────────────────────────────────────────────────────────────
# Stop Hook（回合结束钩子）
# 语义对齐 Claude Code hooks 的 Stop 事件：当模型完成一轮回答、agent loop 即将
# 停止时触发。hook 收到本轮上下文（用户提问、最终回答、工具轮数等），可返回：
#   • None / True  → 放行，正常结束本轮；
#   • False        → 拦截，使用通用理由打回重答；
#   • str          → 拦截，以该字符串作为反馈理由打回重答；
#   • dict         → {"decision": "block", "reason": "..."} 拦截并注入反馈；
#                     其他/{"decision": "allow"} 放行。
# 拦截时会把已生成的回答写入历史，再以 user 消息注入「[stop_hook 反馈]」，模型
# 据此继续完善回答；累计拦截 MAX_STOP_HOOK_BLOCKS 次后强制放行，保证必然终止。
# ─────────────────────────────────────────────────────────────────────────────
async def default_stop_hook(payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """内置 Stop Hook：植保问答最终回答的质量门禁"""
    reply = (payload.get("reply") or "").strip()
    if not reply:
        return {"decision": "block", "reason": "本轮回答为空，请直接给出针对用户问题的完整专业回答"}
    if len(reply) < 15:
        return {"decision": "block", "reason": "回答过于简短，缺少植保专业要点，请补充诊断依据与防治处置建议"}
    # 疑似把接口报错/占位文本当成回答吐给用户（短文本且含报错关键词时打回）
    err_markers = ["HTTP", "API", "接口异常", "请求失败", "超时", "未知错误"]
    if len(reply) < 60 and any(m in reply for m in err_markers):
        return {"decision": "block", "reason": "回答疑似接口报错信息，请忽略报错并直接给出专业植保建议"}
    return None


async def _decide_stop(
    stop_hook: Optional[Callable[[Dict[str, Any]], Any]],
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """执行 Stop Hook 并将其返回值归一化为 {"decision": "allow"|"block", "reason": ...}

    hook 未提供时使用 default_stop_hook；hook 自身抛异常时安全放行（不阻塞主流程）。
    """
    fn = stop_hook or default_stop_hook
    try:
        if asyncio.iscoroutinefunction(fn):
            result = await fn(payload)
        else:
            result = fn(payload)
            if asyncio.iscoroutine(result):
                result = await result
    except Exception as e:
        logger.warning(f"Stop Hook 执行异常，默认放行结束: {e}")
        return {"decision": "allow"}

    if result is None or result is True:
        return {"decision": "allow"}
    if result is False:
        return {"decision": "block", "reason": "回答未通过停止校验"}
    if isinstance(result, str):
        return {"decision": "block", "reason": result}
    if isinstance(result, dict):
        if result.get("decision") == "block":
            return {"decision": "block", "reason": str(result.get("reason") or "回答未通过停止校验")}
        return {"decision": "allow"}
    return {"decision": "allow"}


async def _resume_if_truncated_nonstream(
    client: "httpx.AsyncClient",
    url: str,
    headers: Dict[str, str],
    api_messages: List[Dict[str, Any]],
    reply_text: str,
    finish_reason: Optional[str],
    *,
    model: str,
    temperature: float,
    max_tokens: int,
) -> str:
    """非流式路径的截断恢复：finish_reason=length 时注入续写指令补全一次"""
    if finish_reason != "length":
        return reply_text
    logger.info("非流式回答被 max_tokens 截断，注入续写指令补全一次")
    api_messages.append({"role": "assistant", "content": reply_text})
    api_messages.append({"role": "user", "content":
        "输出被长度限制截断。直接从中断处继续，不要道歉、不要复述已写内容。"})
    try:
        resp = await client.post(url, headers=headers, json={
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if resp.status_code == 200:
            more = resp.json()["choices"][0]["message"]["content"]
            if more:
                return reply_text + more
    except Exception as e:
        logger.warning(f"续写请求失败，沿用原回答: {e}")
    return reply_text


async def _stop_hook_finalize_nonstream(
    client: "httpx.AsyncClient",
    url: str,
    headers: Dict[str, str],
    api_messages: List[Dict[str, Any]],
    reply_text: str,
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
        "stop_hook_active": False,
        "message": message,
        "reply": reply_text,
        "tool_rounds": tool_rounds,
        "context": context,
    }
    decision = await _decide_stop(stop_hook, payload)
    if decision.get("decision") != "block":
        return reply_text

    reason = decision.get("reason", "")
    logger.info(f"Stop Hook 拦截非流式回答，携带反馈重答一次: {reason}")
    api_messages.append({"role": "assistant", "content": reply_text})
    api_messages.append({"role": "user", "content": f"[stop_hook 反馈] {reason}"})
    try:
        resp = await client.post(url, headers=headers, json={
            "model": model,
            "messages": api_messages,
            "temperature": temperature,
            "max_tokens": max_tokens,
        })
        if resp.status_code == 200:
            fixed = resp.json()["choices"][0]["message"]["content"]
            if fixed:
                return fixed
    except Exception as e:
        logger.warning(f"Stop Hook 重答请求失败，沿用原回答: {e}")
    return reply_text


def build_context_block(context: Optional[Dict[str, Any]] = None) -> str:
    """将大田感知现场数据格式化为上下文文本块（无 context 时返回空串）"""
    if not context:
        return ""
    ctx_lines = ["\n【当前大田示范区实时检测感知现场数据】:"]
    if context.get("diseaseName"):
        ctx_lines.append(f"• 视觉模型诊断病害: {context.get('diseaseName')}")
    if context.get("confidence"):
        ctx_lines.append(f"• 诊断置信度: {context.get('confidence')}%")
    if context.get("severity"):
        ctx_lines.append(f"• 侵染严重程度评级: {context.get('severity')}")
    if context.get("damageRate"):
        ctx_lines.append(f"• 叶面积受损率: {context.get('damageRate')}%")
    if context.get("prescription"):
        ctx_lines.append(f"• 系统预置处方建议: {context.get('prescription')}")
    # 微气候传感器遥测（气温/湿度/光照）按要求不注入大模型，仅保留视觉诊断结论
    return "\n".join(ctx_lines)


def build_env_block(context: Optional[Dict[str, Any]] = None) -> str:
    """构建当前日期/农时/产区环境块，注入 system 提示词。

    病害防治窗口期、用药时机高度依赖时令——模型必须知道「今天几号」才能给出
    与季节匹配的建议（例如 10 月谈"抢在雨前施药"与 7 月完全不同）。
    """
    now = datetime.now()
    month = now.month
    if 4 <= month <= 5:
        season = "春播与苗期管理期"
    elif 6 <= month <= 9:
        season = "夏玉米生长关键期（拔节-大喇叭口-灌浆）"
    elif 10 <= month <= 11:
        season = "秋收与冬小麦适期播种期"
    else:
        season = "冬闲与备耕期"
    region = (context or {}).get("region") or "黄淮海夏玉米示范区"
    return (
        f"\n【当前环境信息】（由系统注入，供时令判断用）:\n"
        f"• 今天日期: {now:%Y年%m月%d日}（第{now.isocalendar().week}周）\n"
        f"• 农时阶段: {season}\n"
        f"• 示范区域: {region}\n"
        f"• 涉及实时行情、政策、病虫害动态时，搜索词必须带上 {now.year} 年与具体地区\n"
    )


def build_augmented_prompt(message: str, context: Optional[Dict[str, Any]] = None) -> str:
    """将专家设定、大田感知现场数据与当前用户提问融合为完整 Prompt"""
    parts = [ROLE_INSTRUCTION, build_env_block(context)]

    ctx_block = build_context_block(context)
    if ctx_block:
        parts.append(ctx_block)

    parts.append(f"\n【农户与机手咨询问题】:\n{message}")
    return "\n\n".join(parts)


def fallback_expert_reply(msg: str, context: Optional[Dict[str, Any]] = None) -> str:
    """当网络不可达或超时时的本地专家规则知识库平滑兜底"""
    ctx = context or {}
    cur_disease = ctx.get("diseaseName", "")

    if "大斑病" in msg or ("大斑" in msg and "玉米" in msg):
        kb = get_knowledge("Blight")
        symp = kb["symptoms"][0] if kb.get("symptoms") else "长梭形灰褐色大斑"
        chem = kb["control"]["chemical"][1] if kb.get("control", {}).get("chemical") else "苯醚甲环唑/嘧菌酯"
        return (
            f"【玉米大斑病专家防治指导】\n"
            f"• 病原特征：{kb['pathogen']}。\n"
            f"• 核心诊断要点：{symp}。\n"
            f"• 推荐药剂：{chem}；早见病斑早统防，选用耐雨水冲刷剂型。\n"
            f"• 飞防作业建议：无人机作业高度距冠层 2.0~2.5m，行速 5m/s，添加抗蒸发助剂。"
        )
    elif "锈病" in msg or "南方锈病" in msg or "普通锈病" in msg:
        kb = get_knowledge("Common_Rust")
        symp = kb["symptoms"][0] if kb.get("symptoms") else "两面散生黄褐色夏孢子堆"
        chem = kb["control"]["chemical"][0] if kb.get("control", {}).get("chemical") else "戊唑醇/苯醚甲环唑"
        return (
            f"【玉米锈病专家防治指导】\n"
            f"• 病原特征：{kb['pathogen']}。\n"
            f"• 核心诊断要点：{symp}，孢子靠气流快速扩散。\n"
            f"• 推荐药剂：{chem}；可复配磷酸二氢钾提升叶片抗逆能力。\n"
            f"• 飞防要点：暴发初期立即开展大面积统防统治，确保叶片正反面受药均匀。"
        )
    elif "灰斑病" in msg or "灰斑" in msg:
        kb = get_knowledge("Gray_Leaf_Spot")
        symp = kb["symptoms"][0] if kb.get("symptoms") else "受叶脉限制的长方形灰褐色病斑"
        chem = kb["control"]["chemical"][0] if kb.get("control", {}).get("chemical") else "氟硅唑或嘧菌酯"
        return (
            f"【玉米灰斑病专家防治指导】\n"
            f"• 病原特征：{kb['pathogen']}。\n"
            f"• 核心诊断要点：{symp}。\n"
            f"• 飞防处方：{chem}；无人机压低下压风场，重点穿透至玉米中下部功能叶。"
        )
    elif any(k in msg for k in ["无人机", "飞防", "参数", "机型"]):
        return (
            "【植保无人机大田飞防标准作业规范】\n"
            "1. 推荐机型：大疆 T50/T60、极飞 P100 Pro 等多旋翼大载重农业无人机；\n"
            "2. 相对作业高度：玉米冠层上方 2.0–2.5 米；\n"
            "3. 飞行速度：4.8–5.2 m/s，有效喷幅 6.0–7.0 米；\n"
            "4. 亩施药液量：1.6–2.0 L/亩；\n"
            "5. 雾化粒径：120–140 μm，务必添加植物油类飞防助剂，避开正午强光高温。"
        )
    elif any(k in msg for k in ["配方", "药剂", "用药", "买什么药", "配比"]):
        return (
            "【大田玉米病害化学防治与轮换用药原则】\n"
            "1. 严格轮换：三唑类（如戊唑醇、苯醚甲环唑）与甲氧基丙烯酸酯类（如嘧菌酯、吡唑醚菌酯）交替使用；\n"
            "2. 科学混配：可加入芸苔素内酯或磷酸二氢钾，提高叶片光合作用修复速度；\n"
            "3. 施药时段：选择清晨露水干后或傍晚 16:30 以后施药，避开高温强光。"
        )
    elif cur_disease:
        return (
            f"根据系统当前的叶片感知结果，样本检测为「{cur_disease}」。\n"
            f"严重程度评估为：{ctx.get('severity', '发病期')}，受损率约为 {ctx.get('damageRate', 0)}%。\n"
            f"针对该病斑，建议按以下方案处置：{ctx.get('prescription', '选用对路杀菌剂进行精准防治。')}\n"
            f"您可以进一步询问该病害的病原菌、飞防无人机作业参数或轮换药剂。"
        )
    else:
        return (
            "您好！我是大田玉米叶部病害智能诊断与飞防专家助手 🌽\n"
            "您可以随时上传大田玉米叶片照片进行秒级识别，也可以就以下内容向我提问：\n"
            "• 玉米大斑病、南方锈病、灰斑病的识别与用药处方\n"
            "• 植保无人机飞防作业参数（高度、速度、雾滴粒径）\n"
            "• 大田高湿凝露气象下的真菌孢子预警与综合防治策略"
        )


async def ask_agnes(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str = DEFAULT_API_KEY,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    stop_hook: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> Dict[str, Any]:
    """向 Agnes-3.0-Flash 大模型发起单次非流式请求（兼容旧接口）"""
    augmented_prompt = build_augmented_prompt(message, context)

    api_messages = []
    if history:
        for item in history[-6:]:
            role = item.get("role")
            text = item.get("content") or item.get("text", "")
            if not text:
                continue
            if role in ("user", "human"):
                api_messages.append({"role": "user", "content": text})
            elif role in ("ai", "assistant"):
                api_messages.append({"role": "assistant", "content": text})

    api_messages.append({"role": "user", "content": augmented_prompt})

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": model,
        "messages": api_messages,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "tools": [WEB_SEARCH_TOOL],
        # 用户明确要求检索时强制调用（与流式路径同一语义）
        "tool_choice": FORCE_SEARCH_CHOICE if wants_search(message) else "auto",
    }

    try:
        custom_timeout = httpx.Timeout(timeout=timeout, connect=8.0, read=timeout)
        async with httpx.AsyncClient(trust_env=False, timeout=custom_timeout) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                data = response.json()
                choice = data["choices"][0]

                # 处理非流式模式下的 tool_call
                if choice.get("finish_reason") == "tool_calls" and choice.get("message", {}).get("tool_calls"):
                    tool_call = choice["message"]["tool_calls"][0]
                    try:
                        fn_args = json.loads(tool_call["function"]["arguments"])
                    except Exception:
                        fn_args = {"query": message}
                    search_query = fn_args.get("query", message)
                    search_results = await web_search(search_query)

                    api_messages.append(choice["message"])
                    api_messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.get("id", "call_web_search_01"),
                        "content": search_results,
                    })

                    resp2 = await client.post(url, headers=headers, json={
                        "model": model,
                        "messages": api_messages,
                        "temperature": temperature,
                        "max_tokens": max_tokens,
                    })
                    if resp2.status_code == 200:
                        data2 = resp2.json()
                        choice2 = data2["choices"][0]
                        reply_text = choice2["message"]["content"]
                        # 截断恢复：先补全，再过 Stop Hook
                        reply_text = await _resume_if_truncated_nonstream(
                            client, url, headers, api_messages, reply_text,
                            choice2.get("finish_reason"),
                            model=model, temperature=temperature, max_tokens=max_tokens,
                        )
                        # Stop Hook：工具执行完毕、回合即将结束时校验最终回答
                        reply_text = await _stop_hook_finalize_nonstream(
                            client, url, headers, api_messages, reply_text,
                            model=model, temperature=temperature, max_tokens=max_tokens,
                            stop_hook=stop_hook, message=message, context=context, tool_rounds=1,
                        )
                        return {
                            "reply": reply_text,
                            "model": model,
                            "source": "agnes-ai+web_search",
                            "search_query": search_query,
                            "usage": data2.get("usage", {}),
                        }

                reply = choice["message"]["content"]
                # 截断恢复：先补全，再过 Stop Hook
                reply = await _resume_if_truncated_nonstream(
                    client, url, headers, api_messages, reply,
                    choice.get("finish_reason"),
                    model=model, temperature=temperature, max_tokens=max_tokens,
                )
                # Stop Hook：回合即将结束时校验最终回答
                reply = await _stop_hook_finalize_nonstream(
                    client, url, headers, api_messages, reply,
                    model=model, temperature=temperature, max_tokens=max_tokens,
                    stop_hook=stop_hook, message=message, context=context, tool_rounds=0,
                )
                return {
                    "reply": reply,
                    "model": model,
                    "source": "agnes-ai",
                    "usage": data.get("usage", {}),
                }
            else:
                logger.warning(f"Agnes 接口响应非 200: {response.status_code}")
                fallback = fallback_expert_reply(message, context)
                return {
                    "reply": fallback,
                    "model": model,
                    "source": "fallback",
                    "warning": f"HTTP {response.status_code}",
                }
    except Exception as e:
        err_msg = str(e).encode("utf-8", "ignore").decode("utf-8")
        logger.warning(f"调用 Agnes API 发生网络异常，已自动启用专家知识库兜底: {err_msg}")
        fallback = fallback_expert_reply(message, context)
        return {
            "reply": fallback,
            "model": model,
            "source": "fallback",
            "warning": err_msg,
        }


async def stream_ask_agnes(
    message: str,
    context: Optional[Dict[str, Any]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    base_url: str = DEFAULT_BASE_URL,
    api_key: str = DEFAULT_API_KEY,
    model: str = DEFAULT_MODEL,
    timeout: float = DEFAULT_TIMEOUT,
    temperature: float = 0.3,
    max_tokens: int = 2048,
    stop_hook: Optional[Callable[[Dict[str, Any]], Any]] = None,
) -> AsyncGenerator[str, None]:
    """
    极速流畅流式响应 (Fast & Smooth SSE Stream)：
    1. 多轮上下文：system(专家设定+感知现场数据) + history(最近6轮) + 本轮问题，按标准 messages 结构包装；
    2. 首选单次原生流式请求，消灭旧逻辑中非流式预请求丢弃造成的两倍等待延迟；
    3. web_search 工具循环：模型每轮请求工具即执行检索并回填结果，循环往复直到模型给出最终回答
       （上限 MAX_TOOL_ROUNDS 轮，到达上限后收走工具强制直接作答，保证必然终止）；
    4. Stop Hook（回合结束钩子）：模型不再请求工具、本轮回答流式输出完毕、agent loop 即将停止时触发。
       默认执行 default_stop_hook 质量门禁：允许放行结束，或携带反馈打回重答（前端收到
       type='stop_hook' 事件）。累计拦截 MAX_STOP_HOOK_BLOCKS 次后强制放行，保证必然终止。
       可通过 stop_hook 参数注入自定义钩子（返回 None/True/False/str/dict，见 _decide_stop）；
    5. 异常与离线兜底：毫秒级切换本地植保知识库，并通过平滑微步模拟自然打字机流式输出，杜绝瞬间暴冲。
    """
    # ── 多轮 messages 组装：system 包装专家设定与感知上下文，history 保持原 role ──
    ctx_block = build_context_block(context)
    system_content = f"{ROLE_INSTRUCTION}\n{build_env_block(context)}"
    if ctx_block:
        system_content = f"{system_content}\n{ctx_block}"

    api_messages: List[Dict[str, Any]] = [{"role": "system", "content": system_content}]
    if history:
        for item in history[-6:]:
            role = item.get("role")
            text = item.get("content") or item.get("text", "")
            if not text:
                continue
            if role in ("user", "human"):
                api_messages.append({"role": "user", "content": text})
            elif role in ("ai", "assistant"):
                api_messages.append({"role": "assistant", "content": text})

    api_messages.append({"role": "user", "content": message})

    url = f"{base_url.rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    try:
        custom_timeout = httpx.Timeout(timeout=timeout, connect=8.0, read=timeout)
        async with httpx.AsyncClient(trust_env=False, timeout=custom_timeout) as client:
            # 工具始终声明（对齐 Claude Code query.ts:674：工具列表从不按关键词裁剪）。
            # 关键词只决定「首轮是否强制调用」，不决定「工具是否存在」。
            # 旧逻辑用关键词门控 tools 数组，导致用户说「你先去查呀」时模型压根没拿到
            # 工具定义，只能把调用写成正文伪代码 —— 于是出现「嘴上说检索、实际没检索」。
            force_search = wants_search(message)
            force_downgraded = False  # 网关不支持强制 tool_choice 时降级标记

            # ── 工具循环：模型每轮请求工具 → 执行检索 → 回填结果继续，直到直接作答或达上限 ──
            round_idx = 0
            stop_hook_blocks = 0  # Stop Hook 已拦截次数（stop_hook_active 保护计数）
            resume_count = 0      # 截断续写已用次数
            reply_acc = ""        # 跨轮累积的完整回答（供 Stop Hook 校验全貌）
            while True:
                stream_payload = {
                    "model": model,
                    "messages": api_messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens,
                    "stream": True,
                }
                # 尚有剩余工具轮次就始终声明工具；到达上限后收走工具，强制模型本轮直接作答
                if round_idx < MAX_TOOL_ROUNDS:
                    stream_payload["tools"] = [WEB_SEARCH_TOOL]
                    # 用户明确要求检索 → 首轮强制调用，模型无权拒绝
                    # （对齐 Claude Code tool_choice: {type:'tool', name:'web_search'}）
                    stream_payload["tool_choice"] = (
                        FORCE_SEARCH_CHOICE
                        if (force_search and round_idx == 0 and not force_downgraded)
                        else "auto"
                    )

                tool_calls_acc: Dict[int, Dict[str, Any]] = {}
                is_tool = False
                round_content = ""  # 累积本轮流式回答全文，供 Stop Hook 校验
                finish_reason = None  # 本轮结束原因：None/stop/length/tool_calls
                guard = PseudoToolCallGuard()  # 拦截正文里的伪工具调用

                async with client.stream("POST", url, headers=headers, json=stream_payload) as stream_resp:
                    if stream_resp.status_code != 200:
                        # 部分 OpenAI 兼容网关不支持强制 tool_choice，会直接 400/422：
                        # 降级为 auto 重试一次，避免整轮掉进离线兜底
                        if stream_resp.status_code in (400, 422) and not force_downgraded \
                                and stream_payload.get("tool_choice") == FORCE_SEARCH_CHOICE:
                            force_downgraded = True
                            logger.warning("网关拒绝强制 tool_choice，降级为 auto 重试")
                            continue
                        raise RuntimeError(f"Stream HTTP {stream_resp.status_code}")

                    async for line in stream_resp.aiter_lines():
                        if not line:
                            continue
                        if line.startswith("data: ") and not line.endswith("[DONE]"):
                            chunk_raw = line[6:].strip()
                            try:
                                chunk_json = json.loads(chunk_raw)
                                choices = chunk_json.get("choices")
                                if not choices:
                                    continue
                                delta = choices[0].get("delta", {})
                                if choices[0].get("finish_reason"):
                                    finish_reason = choices[0]["finish_reason"]

                                # 判定是否触发 tool_calls
                                if "tool_calls" in delta and delta["tool_calls"]:
                                    is_tool = True
                                    for tc in delta["tool_calls"]:
                                        idx = tc.get("index", 0)
                                        if idx not in tool_calls_acc:
                                            tool_calls_acc[idx] = {
                                                "id": tc.get("id", ""),
                                                "name": tc.get("function", {}).get("name", ""),
                                                "arguments": "",
                                            }
                                        if tc.get("id"):
                                            tool_calls_acc[idx]["id"] = tc["id"]
                                        if tc.get("function", {}).get("name"):
                                            tool_calls_acc[idx]["name"] = tc["function"]["name"]
                                        if tc.get("function", {}).get("arguments"):
                                            tool_calls_acc[idx]["arguments"] += tc["function"]["arguments"]
                                    continue

                                # 正常内容流式推送（先过伪工具调用拦截器）
                                content_piece = delta.get("content", "")
                                if content_piece:
                                    safe_piece = guard.feed(content_piece)
                                    if safe_piece:
                                        round_content += safe_piece
                                        yield f"data: {json.dumps({'type': 'delta', 'content': safe_piece}, ensure_ascii=False)}\n\n"
                            except Exception:
                                continue

                    # 流结束：冲刷拦截器剩余文本（未闭合的伪工具调用块也在此被回收）
                    tail_piece = guard.flush()
                    if tail_piece:
                        round_content += tail_piece
                        yield f"data: {json.dumps({'type': 'delta', 'content': tail_piece}, ensure_ascii=False)}\n\n"

                # ── 伪工具调用修复：模型把调用写成了正文而非原生 tool_calls ──
                # 拦截器已把那段伪代码从用户可见文本中摘掉，这里补成一次真实检索，
                # 让「说查却没查」变成「真的查了」。Claude Code 不需要这层兜底——它的上游
                # 必定返回原生 tool_use 块；OpenAI 兼容网关降级/模型未拿到 tools 时才需要。
                if guard.query and not (is_tool and tool_calls_acc) and round_idx < MAX_TOOL_ROUNDS:
                    pseudo_q = guard.query
                    pseudo_id = f"call_pseudo_{round_idx}"
                    logger.warning(f"检测到文本形态的伪工具调用，已转为真实检索: {pseudo_q}")
                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': 'web_search', 'query': pseudo_q}, ensure_ascii=False)}\n\n"
                    pseudo_results = await web_search(pseudo_q)
                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': 'web_search', 'message': '检索完成，大模型正在组织回答...'}, ensure_ascii=False)}\n\n"
                    api_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": pseudo_id,
                            "type": "function",
                            "function": {
                                "name": "web_search",
                                "arguments": json.dumps({"query": pseudo_q}, ensure_ascii=False),
                            },
                        }],
                    })
                    api_messages.append({"role": "tool", "tool_call_id": pseudo_id, "content": pseudo_results})
                    round_idx += 1
                    continue

                # 本轮无工具调用 → 模型已完成本轮回答，agent loop 即将停止：
                # ① 若被 max_tokens 截断 → 注入续写指令继续生成（先于 Stop Hook）
                # ② 正常结束 → 触发 Stop Hook（回合结束钩子）决定「放行」还是「打回重答」
                if not (is_tool and tool_calls_acc):
                    reply_acc += round_content  # 累积跨轮全文（含续写片段），供 Stop Hook 校验

                    # ── 截断恢复：对齐 Claude Code「Resume directly — no apology, no recap」──
                    if finish_reason == "length" and resume_count < MAX_RESUME_ROUNDS:
                        resume_count += 1
                        logger.info(f"回答被 max_tokens 截断，注入续写指令继续生成(第{resume_count}/{MAX_RESUME_ROUNDS}次)")
                        yield f"data: {json.dumps({'type': 'truncated', 'action': 'resume', 'round': resume_count}, ensure_ascii=False)}\n\n"
                        api_messages.append({"role": "assistant", "content": round_content or None})
                        api_messages.append({"role": "user", "content":
                            "输出被长度限制截断。直接从中断处继续，不要道歉、不要复述已写内容，必要时拆成更短的段落。"})
                        round_idx += 1
                        continue
                    if finish_reason == "length":
                        # 续写额度耗尽仍有截断：放行（内容已尽力补全），并在结尾告知用户
                        logger.warning(f"截断续写已达上限({MAX_RESUME_ROUNDS}次)，回答仍被截断，强制放行")
                        yield f"data: {json.dumps({'type': 'truncated', 'action': 'incomplete'}, ensure_ascii=False)}\n\n"

                    hook_payload = {
                        "stop_hook_active": stop_hook_blocks > 0,  # 已拦截过则置位，防止 hook 无限打回
                        "message": message,
                        "reply": reply_acc,
                        "tool_rounds": round_idx,
                        "context": context,
                    }
                    decision = await _decide_stop(stop_hook, hook_payload)

                    if decision.get("decision") == "block" and stop_hook_blocks < MAX_STOP_HOOK_BLOCKS:
                        stop_hook_blocks += 1
                        reason = decision.get("reason", "")
                        logger.info(f"Stop Hook 拦截本轮结束(第{stop_hook_blocks}/{MAX_STOP_HOOK_BLOCKS}次): {reason}")
                        yield f"data: {json.dumps({'type': 'stop_hook', 'action': 'block', 'reason': reason}, ensure_ascii=False)}\n\n"
                        # 已流出的部分回答写入对话历史，再以 user 消息注入 hook 反馈，模型据此继续完善
                        api_messages.append({"role": "assistant", "content": reply_acc or None})
                        api_messages.append({"role": "user", "content": f"[stop_hook 反馈] {reason}"})
                        round_idx += 1
                        continue

                    if decision.get("decision") == "block":
                        # 已达拦截上限，强制放行结束，保证必然终止（stop_hook_active 保护语义）
                        logger.info("Stop Hook 再次拦截已达上限，强制放行结束")

                    yield f"data: {json.dumps({'type': 'stop_hook', 'action': 'allow'}, ensure_ascii=False)}\n\n"
                    break

                # 执行本轮全部工具调用：一条 assistant 消息携带所有 tool_calls，再逐条回填 tool 结果
                assistant_tool_calls = []
                tool_results = []
                for idx in sorted(tool_calls_acc):
                    tc = tool_calls_acc[idx]
                    tool_id = tc.get("id") or f"call_web_search_{round_idx}_{idx}"
                    tool_name = tc.get("name") or "web_search"
                    args_str = tc.get("arguments", "")
                    try:
                        fn_args = json.loads(args_str)
                    except Exception:
                        fn_args = {"query": message}
                    search_query = fn_args.get("query", message)

                    yield f"data: {json.dumps({'type': 'tool_call', 'tool': tool_name, 'query': search_query}, ensure_ascii=False)}\n\n"

                    # 服务端执行真实网页检索
                    search_results = await web_search(search_query)

                    yield f"data: {json.dumps({'type': 'tool_result', 'tool': tool_name, 'message': '检索完成，大模型正在组织回答...'}, ensure_ascii=False)}\n\n"

                    assistant_tool_calls.append({
                        "id": tool_id,
                        "type": "function",
                        "function": {"name": tool_name, "arguments": args_str or json.dumps({"query": search_query})},
                    })
                    tool_results.append({"tool_call_id": tool_id, "content": search_results})

                api_messages.append({
                    "role": "assistant",
                    "content": None,
                    "tool_calls": assistant_tool_calls,
                })
                api_messages.extend({"role": "tool", **res} for res in tool_results)

                round_idx += 1

            # 完成标识
            yield f"data: {json.dumps({'type': 'done', 'model': model, 'source': 'agnes-ai'}, ensure_ascii=False)}\n\n"

    except Exception as e:
        logger.warning(f"流式请求异常或超时，启用本地兜底: {e}")
        fallback_text = fallback_expert_reply(message, context)
        # 兜底平滑分片输出，每片 2~4 个字，带 20ms 延时模拟自然的流式打字
        chunk_size = 3
        for i in range(0, len(fallback_text), chunk_size):
            piece = fallback_text[i:i + chunk_size]
            yield f"data: {json.dumps({'type': 'delta', 'content': piece}, ensure_ascii=False)}\n\n"
            await asyncio.sleep(0.02)
        yield f"data: {json.dumps({'type': 'done', 'model': model, 'source': 'fallback'}, ensure_ascii=False)}\n\n"
