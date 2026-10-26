"""大田数字农业系统 —— 高可用网页搜索引擎工具 (web_search) v2

架构（对齐 Claude Code WebSearchTool 的设计契约）:
1. 引擎：DDGS 元搜索（https://github.com/deepserap/ddgs，AGPL 开源、零 API Key），
   聚合 Bing / Google / Yahoo 等真实搜索引擎，结果自带 title + url，无需解析页面结构；
2. 网络层：国内直连无法访问境外引擎，通过本地代理访问（默认 http://127.0.0.1:7897，
   可在 configs/config.yaml 的 search.proxy 配置，或设 SEARCH_PROXY 环境变量覆盖）；
3. 后端降级链：bing → google → yahoo，任一命中即返回（中文农业内容 bing 召回最佳）；
4. 双重兜底：DDGS 全部失败时回落到百度移动端爬虫（本地启发式，无代理也可用）；
5. 错误显式化（Claude Code 契约）：搜索失败返回 "Web search error: ..." 前缀，
   让大模型明确知道"搜索挂了"而不是拿到空结果凭旧知识硬答（杜绝静默失效）；
6. 强制溯源：每条结果带「来源: URL」，输出末尾附加 MANDATORY Sources 指令，
   与 llm_client 工具描述的硬要求呼应。
"""
from __future__ import annotations

import asyncio
import logging
import os
import re
import urllib.parse
from typing import Any, Dict, List

import httpx

logger = logging.getLogger("corn_system.web_search")

# ── 默认配置（可被 configs/config.yaml 的 search: 节覆盖）──
DEFAULT_PROXY = "http://127.0.0.1:7897"
DEFAULT_BACKENDS = ("bing", "google", "yahoo")  # 中文农业内容: bing 召回最好
DEFAULT_MAX_RESULTS = 5
SEARCH_TIMEOUT = 15.0  # DDGS 单后端超时（秒）

# 模块级配置缓存（首次调用时从 config.yaml 读取一次）
_cfg_cache: Dict[str, Any] | None = None


def _load_search_config() -> Dict[str, Any]:
    """从 configs/config.yaml 读取 search: 配置节；失败则用默认值。"""
    global _cfg_cache
    if _cfg_cache is not None:
        return _cfg_cache
    cfg: Dict[str, Any] = {
        "proxy": DEFAULT_PROXY,
        "backends": list(DEFAULT_BACKENDS),
        "max_results": DEFAULT_MAX_RESULTS,
    }
    try:
        import sys as _sys
        from pathlib import Path as _Path
        root = _Path(__file__).resolve().parent.parent
        _sys.path.insert(0, str(root))
        from src.config import load_config  # noqa: E402
        sec = (load_config() or {}).get("search", {}) or {}
        if sec.get("proxy") is not None:
            cfg["proxy"] = str(sec["proxy"])
        if sec.get("backends"):
            cfg["backends"] = [str(b) for b in sec["backends"]]
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


# ════════════════════════════ 主引擎：DDGS ════════════════════════════

def _ddgs_search_sync(query: str, backends: List[str], proxy: str,
                      max_results: int) -> List[Dict[str, str]]:
    """DDGS 同步搜索：按后端降级链逐个尝试，返回 [{title, snippet, url}]。

    DDGS 的 HTTP 客户端（primp）不走系统代理，必须显式传 proxy。
    所有后端都抛异常 → 抛出 RuntimeError（调用方据此区分"失败"与"无结果"）。
    """
    from ddgs import DDGS

    last_err: Exception | None = None
    for backend in backends:
        try:
            d = DDGS(proxy=proxy or None, timeout=SEARCH_TIMEOUT)
            raw = d.text(query, max_results=max_results, backend=backend)
            results = []
            for r in raw or []:
                url = r.get("href") or r.get("url") or ""
                title = (r.get("title") or "").strip()
                snippet = (r.get("body") or "").strip()
                if not (url and (title or snippet)):
                    continue
                results.append({"title": title, "snippet": snippet[:280], "url": url})
            if results:
                return results
            # 该后端连通但无结果 → 尝试下一个
        except Exception as e:
            last_err = e
            logger.warning(f"DDGS 后端 {backend} 失败: {e}")
    if last_err is not None:
        raise RuntimeError(f"所有 DDGS 后端失败，最后错误: {last_err}")
    return []


async def search_ddgs(query: str, max_results: int) -> List[Dict[str, str]]:
    """DDGS 异步包装：线程池执行同步请求，不阻塞 SSE 事件循环。"""
    cfg = _load_search_config()
    return await asyncio.to_thread(
        _ddgs_search_sync, query, cfg["backends"], cfg["proxy"], max_results
    )


# ═══════════════════════ 兜底引擎：百度移动端爬虫 ═══════════════════════

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}

# 百度页面内嵌 JSON 数据 blob 的噪声片段，命中即视为脏文本丢弃
_JUNK_PAT = re.compile(r"not_struct|isSingleLine|pageStyleUpgrade|\"hasBottom\"")


def _clean_html(html: str) -> str:
    """剥离 script/style/标签，压缩空白，返回纯文本摘要"""
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", "", html).strip()
    return re.sub(r"\s+", " ", clean)


def _first_external_link(html: str) -> str:
    """取片段中第一个非百度/搜狗自有域的 http(s) 链接作为来源"""
    links = re.findall(r'href="(https?://[^"]+)"', html)
    for url in links:
        if not re.search(r"(?:baidu\.com|sogou\.com|baidustatic|bdstatic)", url):
            return url
    return ""


async def search_baidu_mobile(query: str, max_results: int = 4,
                              timeout: float = 6.0) -> List[Dict[str, str]]:
    """百度移动端爬虫兜底（无代理网络下的最后手段；结果质量不稳定）"""
    url = f"https://m.baidu.com/s?word={urllib.parse.quote(query)}"
    results: List[Dict[str, str]] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                articles = re.findall(r"<article[^>]*>(.*?)</article>", resp.text, re.DOTALL)
                for art in articles:
                    clean = _clean_html(art)
                    # 过滤内嵌 JSON 噪声与百度的导航/热搜壳
                    if _JUNK_PAT.search(clean) or len(clean) < 25:
                        continue
                    if clean.startswith(("大家还在搜", "百度APP", "热搜")):
                        continue
                    results.append({
                        "title": clean[:40],
                        "snippet": clean[:260],
                        "url": _first_external_link(art),
                    })
                    if len(results) >= max_results:
                        break
    except Exception as e:
        logger.warning(f"Baidu 移动端兜底搜索异常: {e}")
    return results


# ════════════════════════════ 统一入口 ════════════════════════════

async def web_search(query: str, max_results: int | None = None) -> str:
    """统一入口：联网搜索指定关键词，返回带来源 URL 的结构化文本结果。

    错误契约（对齐 Claude Code）：
    - 引擎失败 → 返回 "Web search error: ..."，模型可明确告知用户检索不可用；
    - 引擎正常但确无结果 → 返回友好提示，模型可凭领域知识作答并说明来源局限。
    """
    q = query.strip()
    if not q:
        return "搜索关键词为空。"

    cfg = _load_search_config()
    n = max_results or cfg["max_results"]

    # ① 主引擎：DDGS 元搜索（bing/google/yahoo 降级链）
    try:
        results = await search_ddgs(q, n)
    except Exception as e:
        logger.warning(f"DDGS 主引擎失败，转百度兜底: {e}")
        results = []

    # ② 兜底引擎：百度移动端爬虫
    if not results:
        results = await search_baidu_mobile(q, max_results=n)

    # ③ 双双失败：显式错误（模型可感知搜索不可用，而非"没搜到"）
    if not results:
        return (
            f"Web search error: 联网检索不可用（主引擎与兜底引擎均失败），"
            f"请基于自身专业知识谨慎作答，并明确告知用户本次未能联网核实。查询词: {q}"
        )

    # 结构化输出 + Claude Code 式强制溯源指令
    lines = [f"【互联网最新搜索结果（关键词: {q}）】"]
    for i, r in enumerate(results, 1):
        title = r.get("title") or r["snippet"][:40]
        lines.append(f"{i}. {title}")
        if r.get("snippet") and r["snippet"] != title:
            lines.append(f"   摘要: {r['snippet']}")
        if r.get("url"):
            lines.append(f"   来源: {r['url']}")
    lines.append(
        "提示：回答引用以上外部事实时，必须在末尾以「来源：」小节列出对应链接，"
        "格式：[标题](URL)。"
    )
    return "\n".join(lines)
