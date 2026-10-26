# -*- coding: utf-8 -*-
"""复测：工具检索后的回答是否还复述过程"""
import json
import time

import httpx

URL = "http://127.0.0.1:8010/screen/chat/stream"

t0 = time.perf_counter()
parts = []
events = []
with httpx.Client(timeout=120) as client:
    with client.stream("POST", URL, json={"message": "今天玉米最新收购价格行情怎么样？"}) as r:
        for line in r.iter_lines():
            if not line.startswith("data: "):
                continue
            evt = json.loads(line[6:])
            if evt.get("type") == "delta":
                parts.append(evt.get("content", ""))
            else:
                events.append(evt.get("type"))
reply = "".join(parts)
print(f"events: {events}")
print(f"reply ({len(reply)}字): {reply[:150]}")
narration = any(k in reply[:60] for k in ["用户询问", "需要调用", "超出", "工具来检索", "检索最"])
print(f">>> 过程复述 {'仍存在 ❌' if narration else '已消除 ✅'}")
