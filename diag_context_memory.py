# -*- coding: utf-8 -*-
"""验证：1) 多轮上下文记忆  2) web_search 工具循环链路"""
import json
import time

import httpx

URL = "http://127.0.0.1:8010/screen/chat/stream"


def chat(message, history=None):
    """发一轮对话，返回 (事件序列, 拼接的回答文本)"""
    events = []
    text_parts = []
    t0 = time.perf_counter()
    body = {"message": message}
    if history is not None:
        body["history"] = history
    with httpx.Client(timeout=120) as client:
        with client.stream("POST", URL, json=body) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                evt = json.loads(line[6:])
                t = time.perf_counter() - t0
                if evt.get("type") == "delta":
                    text_parts.append(evt.get("content", ""))
                else:
                    events.append((t, evt))
                    kind = evt.get("type")
                    extra = evt.get("query", evt.get("message", ""))
                    print(f"    [{t:6.2f}s] {kind}: {extra}")
    return events, "".join(text_parts)


print("=== 第 1 轮：告知信息（不带历史） ===")
ev1, reply1 = chat("请记住：我家的玉米地在河南郑州。这句话你只需要简短确认。")
print(f"    reply1 ({len(reply1)}字): {reply1[:80]}")

print("=== 第 2 轮：带历史追问（考验上下文记忆） ===")
history = [
    {"role": "user", "content": "请记住：我家的玉米地在河南郑州。这句话你只需要简短确认。"},
    {"role": "ai", "content": reply1},
]
ev2, reply2 = chat("我只问你一件事：我刚才说我家在哪个省？只回答省名。", history=history)
print(f"    reply2: {reply2[:120]}")
ok_memory = ("河南" in reply2) and ("山东" not in reply2) and ("河北" not in reply2)
print(f"    >>> 上下文记忆 {'PASS ✅' if ok_memory else 'FAIL ❌'}")

print("=== 第 3 轮：外部行情问题（触发 web_search 工具链路） ===")
ev3, reply3 = chat("今天玉米最新收购价格行情怎么样？")
kinds = [e[1].get("type") for e in ev3]
print(f"    events: {kinds}")
print(f"    reply3 ({len(reply3)}字): {reply3[:100]}")
ok_tool = ("tool_call" in kinds) and ("tool_result" in kinds) and len(reply3) > 30
print(f"    >>> 工具链路 {'PASS ✅' if ok_tool else 'FAIL ❌（可能模型未触发检索，重跑一次再判断）'}")
