# -*- coding: utf-8 -*-
"""诊断：/api/screen/chat/stream 从发送到首个 delta 的时间线，以及上游原始流是否含 reasoning_content"""
import asyncio
import json
import os
import time

import httpx

LOCAL = "http://127.0.0.1:8010/screen/chat/stream"
UPSTREAM = "https://apihub.agnes-ai.cn/v1/chat/completions"
KEY = os.environ.get("AGNES_API_KEY", "")
MODEL = "agnes-3.0-flash"


async def probe_local():
    t0 = time.perf_counter()
    first_delta = None
    last_delta = None
    n_delta = 0
    async with httpx.AsyncClient(timeout=90) as client:
        async with client.stream("POST", LOCAL, json={
            "message": "玉米灰斑病用什么药最有效？",
        }) as r:
            print(f"[local] HTTP {r.status_code} @ {time.perf_counter()-t0:.2f}s")
            async for line in r.aiter_lines():
                if not line.startswith("data: "):
                    continue
                t = time.perf_counter() - t0
                evt = json.loads(line[6:])
                if evt.get("type") == "delta":
                    n_delta += 1
                    if first_delta is None:
                        first_delta = t
                    last_delta = t
                else:
                    print(f"[local] [{t:6.2f}s] {evt}")
    print(f"[local] first delta @ {first_delta:.2f}s | last @ {last_delta:.2f}s | deltas={n_delta}")


async def probe_upstream():
    t0 = time.perf_counter()
    seen_delta_keys = set()
    shown = 0
    payload = {
        "model": MODEL,
        "messages": [{"role": "user", "content": "玉米灰斑病用什么药最有效？请简要回答。"}],
        "temperature": 0.3,
        "max_tokens": 512,
        "stream": True,
    }
    headers = {"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"}
    async with httpx.AsyncClient(timeout=90, trust_env=False) as client:
        async with client.stream("POST", UPSTREAM, headers=headers, json=payload) as r:
            print(f"[upstream] HTTP {r.status_code} @ {time.perf_counter()-t0:.2f}s")
            async for line in r.aiter_lines():
                if not line.startswith("data: ") or line.endswith("[DONE]"):
                    continue
                t = time.perf_counter() - t0
                try:
                    chunk = json.loads(line[6:])
                except Exception:
                    continue
                delta = (chunk.get("choices") or [{}])[0].get("delta", {}) or {}
                for k in delta:
                    if k not in seen_delta_keys:
                        seen_delta_keys.add(k)
                        preview = str(delta.get(k))[:40]
                        print(f"[upstream] [{t:6.2f}s] NEW delta key: {k!r} -> {preview!r}")
                if shown < 6 and delta.get("content"):
                    print(f"[upstream] [{t:6.2f}s] content chunk: {delta['content'][:20]!r}")
                    shown += 1
    print(f"[upstream] delta keys seen: {seen_delta_keys}")


async def main():
    print("=== 1. 本地接口全链路 ===")
    try:
        await probe_local()
    except Exception as e:
        print(f"[local] FAILED: {e}")
    print("=== 2. 上游原始流（看是否有隐藏 reasoning） ===")
    try:
        await probe_upstream()
    except Exception as e:
        print(f"[upstream] FAILED: {e}")


if __name__ == "__main__":
    asyncio.run(main())
