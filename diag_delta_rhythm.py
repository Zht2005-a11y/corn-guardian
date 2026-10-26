# -*- coding: utf-8 -*-
"""诊断：SSE delta 到达节奏是否均匀（burst 检测）"""
import json
import time

import httpx

URL = "http://127.0.0.1:8010/screen/chat/stream"

def main():
    t0 = time.perf_counter()
    stamps = []
    with httpx.Client(timeout=90) as client:
        with client.stream("POST", URL, json={"message": "玉米灰斑病用什么药最有效？"}) as r:
            for line in r.iter_lines():
                if not line.startswith("data: "):
                    continue
                evt = json.loads(line[6:])
                if evt.get("type") == "delta":
                    stamps.append(time.perf_counter() - t0)

    if len(stamps) < 2:
        print(f"only {len(stamps)} deltas")
        return

    gaps = [b - a for a, b in zip(stamps, stamps[1:])]
    gaps_sorted = sorted(gaps)
    n = len(gaps)
    total = stamps[-1] - stamps[0]
    buckets = [(0, 0.02), (0.02, 0.05), (0.05, 0.1), (0.1, 0.3), (0.3, 1.0), (1.0, 99)]
    hist = {f"{lo*1000:.0f}-{hi*1000:.0f}ms": 0 for lo, hi in buckets}
    for g in gaps:
        for lo, hi in buckets:
            if lo <= g < hi:
                hist[f"{lo*1000:.0f}-{hi*1000:.0f}ms"] += 1
                break
    print(f"deltas: {len(stamps)} | span: {total:.1f}s | avg rate: {len(stamps)/total:.1f}/s")
    print(f"gap min/median/p90/p99/max: "
          f"{gaps_sorted[0]*1000:.0f}/{gaps_sorted[n//2]*1000:.0f}/"
          f"{gaps_sorted[int(n*0.9)]*1000:.0f}/{gaps_sorted[int(n*0.99)]*1000:.0f}/"
          f"{gaps_sorted[-1]*1000:.0f} ms")
    print("interval histogram:")
    for k, v in hist.items():
        bar = "#" * min(v, 60)
        print(f"  {k:>10}: {v:4d} {bar}")

if __name__ == "__main__":
    main()
