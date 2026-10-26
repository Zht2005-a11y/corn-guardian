"""大田数字农业系统 —— 高可用通用网页搜索引擎工具 (web_search)

特性:
1. 采用轻量移动端爬虫聚合（优先百度移动端，辅以备选解析）；
2. 自动剔除广告、JS、样式，提取高价值农情资讯与实时行情摘要；
3. 每条结果保留来源 URL，供大模型在回答中引用（可溯源，拒绝"听说"式回答）；
4. 超时保护与异常安全，保证在无外网或网络波动时优雅降级。
"""
from __future__ import annotations

import logging
import re
import urllib.parse
from typing import List, Dict, Any
import httpx

logger = logging.getLogger("corn_system.web_search")

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/122.0.0.0 Mobile Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "zh-CN,zh;q=0.9",
}


def _clean_html(html: str) -> str:
    """剥离 script/style/标签，压缩空白，返回纯文本摘要"""
    html = re.sub(r"<script.*?</script>", "", html, flags=re.DOTALL)
    html = re.sub(r"<style.*?</style>", "", html, flags=re.DOTALL)
    clean = re.sub(r"<[^>]+>", "", html).strip()
    return re.sub(r"\s+", " ", clean)


def _first_external_link(html: str) -> str:
    """取片段中第一个非百度/搜狗自有域的 http(s) 链接作为来源；退而求其次取第一个链接"""
    links = re.findall(r'href="(https?://[^"]+)"', html)
    for url in links:
        if not re.search(r"(?:baidu\.com|sogou\.com|baidustatic|bdstatic)", url):
            return url
    return links[0] if links else ""


async def search_baidu_mobile(query: str, max_results: int = 4, timeout: float = 6.0) -> List[Dict[str, str]]:
    """通过百度移动端抓取实时搜索摘要（保留来源 URL）"""
    url = f"https://m.baidu.com/s?word={urllib.parse.quote(query)}"
    results: List[Dict[str, str]] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                articles = re.findall(r"<article[^>]*>(.*?)</article>", resp.text, re.DOTALL)
                for art in articles:
                    source_url = _first_external_link(art)
                    clean = _clean_html(art)
                    if len(clean) > 25 and not clean.startswith(("大家还在搜", "百度APP", "热搜")):
                        results.append({"snippet": clean[:260], "url": source_url})
                    if len(results) >= max_results:
                        break
    except Exception as e:
        logger.warning(f"Baidu 移动端搜索异常: {e}")
    return results


async def search_sogou(query: str, max_results: int = 3, timeout: float = 5.0) -> List[Dict[str, str]]:
    """备用搜索源：搜狗搜索（保留来源 URL）"""
    url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}"
    results: List[Dict[str, str]] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                matches = re.findall(r'<p class="str-info"[^>]*>(.*?)</p>', resp.text, re.DOTALL)
                for m in matches[:max_results]:
                    clean = _clean_html(m)
                    if len(clean) > 20:
                        results.append({"snippet": clean[:200], "url": _first_external_link(m)})
    except Exception as e:
        logger.warning(f"Sogou 搜索异常: {e}")
    return results


async def web_search(query: str, max_results: int = 4) -> str:
    """
    统一入口：联网搜索指定关键词，返回带来源 URL 的结构化文本结果。
    每条结果都带「来源: URL」，大模型据此在回答末尾输出「来源：」小节。
    """
    q = query.strip()
    if not q:
        return "搜索关键词为空。"

    # 优先使用百度移动端
    results = await search_baidu_mobile(q, max_results=max_results)

    # 若未找到，使用搜狗作为 fallback
    if not results:
        results = await search_sogou(q, max_results=max_results)

    if not results:
        return f"互联网公开检索未找到与「{q}」直接相关的有效事实信息，建议结合常规农事规程咨询。"

    lines = [f"【互联网最新搜索检索结果（关键词: {q}）】"]
    for i, r in enumerate(results, 1):
        lines.append(f"{i}. {r['snippet']}")
        if r.get("url"):
            lines.append(f"   来源: {r['url']}")
    lines.append("提示：回答引用以上外部事实时，须在末尾以「来源：」小节列出对应链接。")
    return "\n".join(lines)
