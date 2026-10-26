"""大田数字农业系统 —— 高可用网页搜索引擎工具 (web_search) v3

架构（引擎全链国内直连，无需 API Key、无需代理）:
1. 主引擎：360 搜索（www.so.com）——结果 h3 的 data-mdurl 属性直接携带真实 URL，
   标题/摘要结构稳定，实测对中文农业行情内容召回最佳且时效新；
2. 次引擎：搜狗（www.sogou.com）——vrwrap 块 + h3 直链，微信公号内容时效性强；
3. 兜底引擎：百度移动端爬虫——JS 壳页面无链接，但正文摘要可提取（来源标注为快照）；
4. 可选引擎：DDGS 元搜索（聚合 Bing/Google 等境外引擎）——仅当配置了代理时自动
   附加尝试，未配置代理时完全跳过，不构成依赖；
5. 错误显式化（对齐 Claude Code 契约）：全部引擎失败返回 "Web search error: ..."
   并附各引擎错误摘要，杜绝静默失效；确无结果返回友好提示；
6. 强制溯源：每条结果带「来源: URL」，输出末尾附加 MANDATORY Sources 指令。

配置（configs/config.yaml → search: 节）:
  backends: ["so360", "sogou", "baidu_mobile"]   # 降级链，可增删或调序
  proxy: ""                                       # 留空=纯国内直连；配置后自动附加 DDGS
  max_results: 5
"""
from __future__ import annotations

import asyncio
import html as _html
import logging
import os
import re
import urllib.parse
from typing import Any, Awaitable, Callable, Dict, List

import httpx

logger = logging.getLogger("corn_system.web_search")

DEFAULT_BACKENDS = ["so360", "sogou", "baidu_mobile"]
DEFAULT_MAX_RESULTS = 5
ENGINE_TIMEOUT = 8.0  # 单引擎 HTTP 超时（秒）

_UA_PC = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}
_UA_MOBILE = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    ),
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 模块级配置缓存（首次调用时从 config.yaml 读取一次）
_cfg_cache: Dict[str, Any] | None = None


def _load_search_config() -> Dict[str, Any]:
    """从 configs/config.yaml 读取 search: 配置节；失败则用默认值。"""
    global _cfg_cache
    if _cfg_cache is not None:
        return _cfg_cache
    cfg: Dict[str, Any] = {
        "backends": list(DEFAULT_BACKENDS),
        "proxy": "",
        "max_results": DEFAULT_MAX_RESULTS,
    }
    try:
        import sys as _sys
        from pathlib import Path as _Path
        root = _Path(__file__).resolve().parent.parent
        _sys.path.insert(0, str(root))
        from src.config import load_config  # noqa: E402
        sec = (load_config() or {}).get("search", {}) or {}
        if sec.get("backends"):
            cfg["backends"] = [str(b) for b in sec["backends"]]
        if sec.get("proxy") is not None:
            cfg["proxy"] = str(sec["proxy"])
        if sec.get("max_results"):
            cfg["max_results"] = int(sec["max_results"])
    except Exception as e:  # 配置缺失不阻塞搜索
        logger.warning(f"读取 search 配置失败，使用默认值: {e}")
    # 环境变量最高优先级；SEARCH_PROXY=off 表示禁用代理直连
    env_proxy = os.environ.get("SEARCH_PROXY")
    if env_proxy is not None:
        cfg["proxy"] = "" if env_proxy.lower() == "off" else env_proxy
    _cfg_cache = cfg
    return cfg


def _strip_tags(raw: str) -> str:
    """去 HTML 标签 + 还原实体（&nbsp; &amp; 等），压缩空白"""
    text = re.sub(r"<[^>]+>", "", raw)
    text = _html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


# ══════════════════════ 主引擎：360 搜索（www.so.com） ══════════════════════

async def _engine_so360(query: str, max_results: int) -> List[Dict[str, str]]:
    """360 搜索：结果块 <li class="res-list">，h3 链接的 data-mdurl/data-url
    属性直接携带真实 URL（无需跳转解析），摘要位于 <p class="res-desc">。"""
    url = f"https://www.so.com/s?q={urllib.parse.quote_plus(query)}&rn=10"
    async with httpx.AsyncClient(follow_redirects=True, timeout=ENGINE_TIMEOUT) as client:
        resp = await client.get(url, headers=_UA_PC)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        page = resp.text

    results: List[Dict[str, str]] = []
    blocks = re.split(r'<li class="res-list', page)[1:]
    for b in blocks:
        am = re.search(r'<h3[^>]*>\s*<a([^>]*)>(.*?)</a>', b, re.DOTALL)
        if not am:
            continue
        attrs, title_html = am.groups()
        title = _strip_tags(title_html)
        if len(title) < 4:
            continue
        # 真实 URL 优先级：data-mdurl / data-url（360 直接标注原始站点）> href
        um = re.search(r'data-mdurl="(https?://[^"]+)"', attrs) \
            or re.search(r'data-url="(https?://[^"]+)"', attrs) \
            or re.search(r'href="(https?://[^"]+)"', attrs)
        if not um:
            continue
        real_url = _html.unescape(um.group(1))
        # 过滤 360 自有跳转/推广域（无 data-mdurl 时 href 是 so.com/link 跳转器）
        if re.search(r"so\.com/link|e\.so\.com", real_url):
            continue
        pm = re.search(r'<p class="res-desc[^"]*"[^>]*>(.*?)</p>', b, re.DOTALL)
        snippet = _strip_tags(pm.group(1))[:280] if pm else title
        results.append({"title": title[:80], "snippet": snippet, "url": real_url})
        if len(results) >= max_results:
            break
    return results


# ══════════════════════ 次引擎：搜狗（www.sogou.com） ══════════════════════

async def _engine_sogou(query: str, max_results: int) -> List[Dict[str, str]]:
    """搜狗搜索：<div class="vrwrap"> 块，h3 链接多为直链（含微信公众号文章，
    时效性强），摘要位于 class 含 space-txt 的段落。"""
    url = f"https://www.sogou.com/web?query={urllib.parse.quote_plus(query)}"
    async with httpx.AsyncClient(follow_redirects=True, timeout=ENGINE_TIMEOUT) as client:
        resp = await client.get(url, headers=_UA_PC)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        page = resp.text

    results: List[Dict[str, str]] = []
    blocks = re.split(r'<div class="vrwrap', page)[1:]
    for b in blocks:
        m = re.search(r'<h3[^>]*>\s*<a[^>]*href="([^"]+)"[^>]*>(.*?)</a>', b, re.DOTALL)
        if not m:
            continue
        href, title_html = m.groups()
        title = _strip_tags(title_html)
        if len(title) < 4:
            continue
        # 搜狗站内跳转 → 补全域名；真实 URL 由跳转重定向或直链获得
        if href.startswith("/link"):
            href = "https://www.sogou.com" + href
        href = _html.unescape(href)
        sm = re.search(r'class="[^"]*space-txt[^"]*"[^>]*>(.*?)</', b, re.DOTALL)
        snippet = _strip_tags(sm.group(1))[:260] if sm else title
        results.append({"title": title[:80], "snippet": snippet, "url": href})
        if len(results) >= max_results:
            break
    return results


# ══════════════════════ 兜底引擎：百度移动端 ══════════════════════

# 百度页面内嵌 JSON 数据 blob 的噪声片段，命中即视为脏文本丢弃
_JUNK_PAT = re.compile(r"not_struct|isSingleLine|pageStyleUpgrade|\"hasBottom\"")


async def _engine_baidu_mobile(query: str, max_results: int) -> List[Dict[str, str]]:
    """百度移动端兜底：对爬虫是 JS 壳（通常无链接），但正文摘要可提取；
    来源 URL 取不到时置空，输出层标注为「快照」而非伪造来源。"""
    url = f"https://m.baidu.com/s?word={urllib.parse.quote(query)}"
    results: List[Dict[str, str]] = []
    async with httpx.AsyncClient(follow_redirects=True, timeout=ENGINE_TIMEOUT) as client:
        resp = await client.get(url, headers=_UA_MOBILE)
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code}")
        page = resp.text

    for art in re.findall(r"<article[^>]*>(.*?)</article>", page, re.DOTALL):
        clean = _strip_tags(art)
        if _JUNK_PAT.search(clean) or len(clean) < 25:
            continue
        if clean.startswith(("大家还在搜", "百度APP", "热搜")):
            continue
        # 块内若有真实外链（百度改版不定期恢复）则提取，否则置空
        lm = re.search(r'href="(https?://(?!m\.baidu|www\.baidu|mbd\.baidu|baijiahao)[^"]+)"', art)
        results.append({
            "title": clean[:40],
            "snippet": clean[:260],
            "url": lm.group(1) if lm else "",
        })
        if len(results) >= max_results:
            break
    return results


# ══════════════════ 可选引擎：DDGS（仅配置代理时启用） ══════════════════

async def _engine_ddgs(query: str, max_results: int, proxy: str) -> List[Dict[str, str]]:
    """DDGS 元搜索（境外引擎聚合）。依赖：pip install ddgs + 可用代理。
    未安装或不可达时抛异常，由上层降级，不影响主链路。"""

    def _sync() -> List[Dict[str, str]]:
        from ddgs import DDGS  # 延迟导入：未安装时主链路不受影响
        d = DDGS(proxy=proxy, timeout=15.0)
        raw = d.text(query, max_results=max_results)
        out = []
        for r in raw or []:
            u = r.get("href") or r.get("url") or ""
            t = (r.get("title") or "").strip()
            s = (r.get("body") or "").strip()
            if u and (t or s):
                out.append({"title": t[:80], "snippet": s[:280], "url": u})
        return out

    return await asyncio.to_thread(_sync)


_ENGINES: Dict[str, Callable[[str, int], Awaitable[List[Dict[str, str]]]]] = {
    "so360": _engine_so360,
    "sogou": _engine_sogou,
    "baidu_mobile": _engine_baidu_mobile,
}


# ════════════════════════════ 统一入口 ════════════════════════════

async def web_search(query: str, max_results: int | None = None) -> str:
    """统一入口：联网搜索指定关键词，返回带来源 URL 的结构化文本结果。

    错误契约（对齐 Claude Code）：
    - 全部引擎失败 → 返回 "Web search error: ..."，模型可明确告知用户检索不可用；
    - 引擎正常但确无结果 → 返回友好提示，模型可凭领域知识作答并说明来源局限。
    """
    q = query.strip()
    if not q:
        return "搜索关键词为空。"

    cfg = _load_search_config()
    n = max_results or cfg["max_results"]

    results: List[Dict[str, str]] = []
    errors: List[str] = []

    # 按配置的降级链依次尝试（全部为国内直连引擎）
    for name in cfg["backends"]:
        if len(results) >= n:
            break
        engine = _ENGINES.get(name)
        if engine is None:
            errors.append(f"{name}: 未知引擎")
            continue
        try:
            results = await engine(q, n)
            if results:
                logger.info(f"web_search 引擎 {name} 命中 {len(results)} 条")
                break
        except Exception as e:
            errors.append(f"{name}: {type(e).__name__}")
            logger.warning(f"web_search 引擎 {name} 失败: {e}")

    # 可选：配置了代理时附加 DDGS 尝试（未配置则完全跳过，零依赖）
    if not results and cfg.get("proxy"):
        try:
            results = await _engine_ddgs(q, n, cfg["proxy"])
        except Exception as e:
            errors.append(f"ddgs: {type(e).__name__}")
            logger.warning(f"web_search 引擎 ddgs 失败: {e}")

    if not results:
        if errors:
            return (
                f"Web search error: 联网检索不可用（{'; '.join(errors)}），"
                f"请基于自身专业知识谨慎作答，并明确告知用户本次未能联网核实。查询词: {q}"
            )
        return f"互联网公开检索未找到与「{q}」直接相关的有效事实信息，建议结合常规农事规程咨询。"

    # 结构化输出 + Claude Code 式强制溯源指令
    lines = [f"【互联网最新搜索结果（关键词: {q}）】"]
    for i, r in enumerate(results, 1):
        title = r.get("title") or r["snippet"][:40]
        lines.append(f"{i}. {title}")
        if r.get("snippet") and r["snippet"] != title:
            lines.append(f"   摘要: {r['snippet']}")
        if r.get("url"):
            lines.append(f"   来源: {r['url']}")
        else:
            lines.append("   来源: 搜索引擎快照（未能解析原始链接，引用时请注明）")
    lines.append(
        "提示：回答引用以上外部事实时，必须在末尾以「来源：」小节列出对应链接，"
        "格式：[标题](URL)。"
    )
    return "\n".join(lines)
