"""模型对比测速：ResNet50 vs MobileNetV3-Large（参数量 / 单图耗时 / 吞吐）。

用法：
    python -m scripts.benchmark
    python -m scripts.benchmark --model resnet50 --model mobilenet_v3_large --iters 50

结果输出到 outputs/reports/benchmark.json，可直接放进答辩 PPT 的对比表格。
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config  # noqa: E402
from src.models import build_model, count_parameters  # noqa: E402


def bench(model: torch.nn.Module, device: torch.device, size: int, batch: int, iters: int):
    x = torch.randn(batch, 3, size, size, device=device)
    model.eval()
    with torch.no_grad():
        for _ in range(5):  # warmup
            model(x)
        if device.type == "cuda":
            torch.cuda.synchronize()
        t0 = time.perf_counter()
        for _ in range(iters):
            model(x)
        if device.type == "cuda":
            torch.cuda.synchronize()
        total = time.perf_counter() - t0
    return total / iters / batch * 1000, batch / (total / iters)  # 单图 ms, 每秒图片数


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--model", action="append", default=None)
    ap.add_argument("--size", type=int, default=224)
    ap.add_argument("--batch", type=int, default=1)
    ap.add_argument("--iters", type=int, default=30)
    ap.add_argument("--device", default="auto")
    args = ap.parse_args(argv)

    cfg = load_config(args.config)
    device = torch.device("cuda" if (args.device == "auto" and torch.cuda.is_available()) else
                          ("cpu" if args.device == "auto" else args.device))
    archs = args.model or ["resnet50", "mobilenet_v3_large"]
    num_classes = int(cfg.get("model", {}).get("num_classes", 4))

    rows = []
    print(f"设备: {device} | 输入: {args.size}x{args.size} | batch={args.batch} | iters={args.iters}")
    print(f"{'模型':<24}{'参数量(M)':>12}{'单图耗时(ms)':>16}{'吞吐(img/s)':>14}")
    for arch in archs:
        m = build_model(arch, num_classes, pretrained=False).to(device)
        params = count_parameters(m)
        ms, fps = bench(m, device, args.size, args.batch, args.iters)
        rows.append(
            {
                "arch": arch,
                "params_total_M": round(params["total"] / 1e6, 2),
                "latency_ms_per_image": round(ms, 2),
                "throughput_img_s": round(fps, 1),
            }
        )
        print(f"{arch:<24}{params['total']/1e6:>12.2f}{ms:>16.2f}{fps:>14.1f}")

    out = ROOT / "outputs" / "reports" / "benchmark.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({"device": str(device), "rows": rows}, ensure_ascii=False, indent=2),
                   encoding="utf-8")
    print(f"\n结果已保存: {out}")


if __name__ == "__main__":
    main()
