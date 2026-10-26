# -*- coding: utf-8 -*-
import json

import httpx

parts = []
evts = []
with httpx.Client(timeout=120) as c:
    with c.stream("POST", "http://127.0.0.1:8010/screen/chat/stream",
                  json={"message": "玉米大斑病的典型病斑特征？一句话回答"}) as r:
        print("HTTP", r.status_code)
        for line in r.iter_lines():
            if line.startswith("data: "):
                e = json.loads(line[6:])
                if e.get("type") == "delta":
                    parts.append(e.get("content", ""))
                else:
                    evts.append(e.get("type"))
print("events:", evts)
print("reply:", "".join(parts)[:100])
