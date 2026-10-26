"""一键完整训练 + 评估脚本（答辩前跑一次即可）。

作用：
  1. 训练 ResNet50 主模型 → outputs/checkpoints/best_corn_model.pth
  2. 训练 MobileNetV3-Large 轻量模型 → outputs/checkpoints/best_corn_mobilenetv3.pth
  3. （默认）训练 CBAM 增强版 → outputs/checkpoints/best_corn_model_cbam.pth
  4. 在官方测试集上评估三个模型，生成混淆矩阵 / 指标表 / 对比表

用法：
    python -m scripts.train_full                      # 全部跑（GPU 约 40~70 分钟）
    python -m scripts.train_full --skip-cbam          # 只训 ResNet50 + MobileNetV3
    python -m scripts.train_full --only resnet50      # 只训主模型
    python -m scripts.train_full --epochs-stage2 30   # 自定义阶段二轮数
    python -m scripts.train_full --device cpu --epochs-stage1 2 --epochs-stage2 3   # 仅冒烟

注意：脚本以子进程方式调用 `python -m src.train` / `src.evaluate`，
      单个模型训练失败不会中断整体流程，最后统一汇总结果。
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

MODELS = {
    "resnet50": {"arch": "resnet50", "best": "best_corn_model.pth", "extra": []},
    "mobilenet_v3_large": {"arch": "mobilenet_v3_large", "best": "best_corn_mobilenetv3.pth", "extra": []},
    "resnet50_cbam": {"arch": "resnet50_cbam", "best": "best_corn_model_cbam.pth", "extra": ["--use-cbam"]},
}

ORDER = ["resnet50", "mobilenet_v3_large", "resnet50_cbam"]


def run(cmd: list[str]) -> int:
    print("\n$ " + " ".join(cmd), flush=True)
    t0 = time.perf_counter()
    code = subprocess.call(cmd, cwd=str(ROOT))
    print(f"  -> exit={code} ({time.perf_counter() - t0:.1f}s)", flush=True)
    return code


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="*", default=None, choices=ORDER,
                    help="只训练指定模型")
    ap.add_argument("--skip-cbam", action="store_true")
    ap.add_argument("--epochs-stage1", type=int, default=None)
    ap.add_argument("--epochs-stage2", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=None)
    ap.add_argument("--device", default="auto")
    ap.add_argument("--balance", action="store_true", help="启用类别均衡采样 + 加权损失")
    args = ap.parse_args()

    if args.only:
        targets = list(args.only)
    else:
        targets = ["resnet50", "mobilenet_v3_large"] + ([] if args.skip_cbam else ["resnet50_cbam"])

    common: list[str] = ["--device", args.device]
    if args.epochs_stage1 is not None:
        common += ["--epochs-stage1", str(args.epochs_stage1)]
    if args.epochs_stage2 is not None:
        common += ["--epochs-stage2", str(args.epochs_stage2)]
    if args.batch_size is not None:
        common += ["--batch-size", str(args.batch_size)]
    if args.balance:
        common += ["--balance-sampler", "--class-weighted-loss"]

    results = {}
    for key in targets:
        spec = MODELS[key]
        print(f"\n{'#' * 70}\n# 训练 {key}\n{'#' * 70}", flush=True)
        code = run([sys.executable, "-X", "utf8", "-m", "src.train",
                    "--arch", spec["arch"], "--best-name", spec["best"], *spec["extra"], *common])
        results[key] = "ok" if code == 0 else f"train_failed({code})"

    # ---------- 评估 ----------
    ckpt_dir = ROOT / "outputs" / "checkpoints"
    trained = {k: ckpt_dir / MODELS[k]["best"] for k in targets if (ckpt_dir / MODELS[k]["best"]).exists()}
    reports = ROOT / "outputs" / "reports"
    summary = []
    for key, ckpt in trained.items():
        print(f"\n{'#' * 70}\n# 评估 {key}\n{'#' * 70}", flush=True)
        cmd = [sys.executable, "-X", "utf8", "-m", "src.evaluate", "--weight", str(ckpt),
               "--arch", MODELS[key]["arch"], "--device", args.device]
        # 与主模型对比（精度 + 单图耗时）
        if key == "resnet50" and "mobilenet_v3_large" in trained:
            cmd += ["--compare", str(trained["mobilenet_v3_large"]),
                    "--compare-arch", MODELS["mobilenet_v3_large"]["arch"]]
        if run(cmd) == 0:
            rep = reports / f"metrics_{MODELS[key]['arch']}_test.json"
            if rep.exists():
                d = json.loads(rep.read_text(encoding="utf-8"))
                summary.append({
                    "model": key,
                    "accuracy": d["accuracy"],
                    "macro_f1": d["macro_f1"],
                    "weighted_f1": d["weighted_f1"],
                    "avg_latency_ms": d.get("avg_latency_ms"),
                    "checkpoint": str(ckpt),
                })

    if summary:
        out = reports / "final_summary.json"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
        print("\n" + "=" * 70)
        print(f"{'模型':<24}{'Accuracy':>12}{'Macro-F1':>12}{'单图(ms)':>12}")
        for s in summary:
            print(f"{s['model']:<24}{s['accuracy']:>12.4f}{s['macro_f1']:>12.4f}"
                  f"{(s['avg_latency_ms'] or 0):>12.2f}")
        print(f"\n汇总已保存: {out}")
        print("答辩前别忘了把 outputs/reports/ 下的混淆矩阵与曲线图放进 PPT。")
    else:
        print("\n没有可评估的权重，请检查训练日志。")
        return 1

    failed = {k: v for k, v in results.items() if v != "ok"}
    if failed:
        print(f"以下模型训练失败: {failed}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
