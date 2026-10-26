"""大田数字农业系统 —— 高可用通用网页搜索引擎工具 (web_search)

特性:
1. 采用轻量移动端爬虫聚合（优先百度移动端，辅以备选解析）；
2. 自动剔除广告、JS、样式，提取高价值农情资讯与实时行情摘要；
3. 超时保护与异常安全，保证在无外网或网络波动时优雅降级。
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


async def search_baidu_mobile(query: str, max_results: int = 4, timeout: float = 6.0) -> List[str]:
    """通过百度移动端抓取实时搜索摘要"""
    url = f"https://m.baidu.com/s?word={urllib.parse.quote(query)}"
    snippets: List[str] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                text = resp.text
                articles = re.findall(r"<article[^>]*>(.*?)</article>", text, re.DOTALL)
                for art in articles:
                    art = re.sub(r"<script.*?</script>", "", art, flags=re.DOTALL)
                    art = re.sub(r"<style.*?</style>", "", art, flags=re.DOTALL)
                    clean = re.sub(r"<[^>]+>", "", art).strip()
                    clean = re.sub(r"\s+", " ", clean)
                    if len(clean) > 25 and not clean.startswith(("大家还在搜", "百度APP", "热搜")):
                        # 截取合适长度
                        snippets.append(clean[:260])
                    if len(snippets) >= max_results:
                        break
    except Exception as e:
        logger.warning(f"Baidu 移动端搜索异常: {e}")
    return snippets


async def search_sogou(query: str, max_results: int = 3, timeout: float = 5.0) -> List[str]:
    """备用搜索源：搜狗搜索"""
    url = f"https://www.sogou.com/web?query={urllib.parse.quote(query)}"
    snippets: List[str] = []
    try:
        async with httpx.AsyncClient(follow_redirects=True, timeout=timeout) as client:
            resp = await client.get(url, headers=HEADERS)
            if resp.status_code == 200:
                matches = re.findall(r'<p class="str-info"[^>]*>(.*?)</p>', resp.text, re.DOTALL)
                for m in matches[:max_results]:
                    clean = re.sub(r"<[^>]+>", "", m).strip()
                    clean = re.sub(r"\s+", " ", clean)
                    if len(clean) > 20:
                        snippets.append(clean[:200])
    except Exception as e:
        logger.warning(f"Sogou 搜索异常: {e}")
    return snippets


async def web_search(query: str, max_results: int = 4) -> str:
    """
    统一入口：联网搜索指定关键词并返回结构化文本结果
    """
    q = query.strip()
    if not q:
        return "搜索关键词为空。"

    # 优先使用百度移动端
    snippets = await search_baidu_mobile(q, max_results=max_results)

    # 若未找到，使用搜狗作为 fallback
    if not snippets:
        snippets = await search_sogou(q, max_results=max_results)

    if not snippets:
        return f"互联网公开检索未找到与「{q}」直接相关的有效事实信息，建议结合常规农事规程咨询。"

    lines = [f"【互联网最新搜索检索结果（关键词: {q}）】"]
    for i, s in enumerate(snippets, 1):
        lines.append(f"{i}. {s}")
    return "\n".join(lines)
