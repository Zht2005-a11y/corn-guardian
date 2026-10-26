"""模型评估脚本：测试集整体准确率、分类别 P/R/F1、混淆矩阵（中文坐标轴）。

使用：
    python -m src.evaluate --weight outputs/checkpoints/best_corn_model.pth
    python -m src.evaluate --weight ... --arch mobilenet_v3_large --split val

输出：
    outputs/reports/metrics_<arch>.json          指标明细
    outputs/reports/confusion_matrix_<arch>.png  混淆矩阵
    outputs/reports/confusion_matrix_norm_<arch>.png  归一化混淆矩阵
    outputs/reports/report_<arch>.txt            文本版报告（可直接贴进论文）
"""
from __future__ import annotations

import argparse
import time
from pathlib import Path

import torch
from torch.utils.data import DataLoader
from tqdm import tqdm

from .config import PROJECT_ROOT, load_config
from .dataset import build_datasets
from .metrics import (
    classification_report_dict,
    plot_confusion_matrix,
    save_json,
)
from .models import build_model


def load_model(weight_path: str | Path, device: torch.device, arch: str | None = None) -> tuple[torch.nn.Module, dict]:
    """加载自训练权重（兼容 cfg 里 server.models 的写法）。"""
    ckpt = torch.load(weight_path, map_location=device)
    if not isinstance(ckpt, dict) or "model_state_dict" not in ckpt:
        ckpt = {"model_state_dict": ckpt}
    meta = {k: v for k, v in ckpt.items() if k != "model_state_dict"}
    arch = arch or meta.get("arch", "resnet50")
    num_classes = int(meta.get("num_classes", 4))
    model = build_model(
        arch=arch,
        num_classes=num_classes,
        pretrained=False,
        use_cbam=bool(meta.get("use_cbam", "cbam" in arch)),
    )
    model.load_state_dict(ckpt["model_state_dict"])
    model.to(device).eval()
    meta["arch"] = arch
    return model, meta


@torch.no_grad()
def predict_loader(model: torch.nn.Module, loader: DataLoader, device: torch.device):
    y_true, y_pred, y_conf = [], [], []
    for images, labels in tqdm(loader, desc="评估中", ncols=90):
        images = images.to(device, non_blocking=True)
        logits = model(images)
        prob = torch.softmax(logits.float(), dim=1)
        conf, pred = prob.max(1)
        y_true.extend(labels.tolist())
        y_pred.extend(pred.cpu().tolist())
        y_conf.extend(conf.cpu().tolist())
    return y_true, y_pred, y_conf


def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="玉米病害模型评估")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "config.yaml"))
    parser.add_argument("--weight", default="outputs/checkpoints/best_corn_model.pth")
    parser.add_argument("--arch", default=None)
    parser.add_argument("--split", default="test", choices=["test", "val", "train"])
    parser.add_argument("--batch-size", type=int, default=32)
    parser.add_argument("--device", default="auto")
    parser.add_argument("--compare", default=None, help="另一个权重路径，用于两模型对比")
    parser.add_argument("--compare-arch", default=None)
    args = parser.parse_args(argv)

    cfg = load_config(args.config)
    device = torch.device("cuda" if (args.device == "auto" and torch.cuda.is_available()) else
                          ("cpu" if args.device == "auto" else args.device))

    train_ds, val_ds, test_ds, _ = build_datasets(cfg)
    ds = {"train": train_ds, "val": val_ds, "test": test_ds}[args.split]
    loader = DataLoader(ds, batch_size=args.batch_size, shuffle=False,
                        num_workers=cfg["data"].get("num_workers", 4))

    weight = Path(args.weight)
    if not weight.is_absolute():
        weight = PROJECT_ROOT / weight
    model, meta = load_model(weight, device, args.arch)
    num_classes = int(meta.get("num_classes", len(cfg["data"]["class_names"])))

    t0 = time.perf_counter()
    y_true, y_pred, y_conf = predict_loader(model, loader, device)
    elapsed = time.perf_counter() - t0
    report = classification_report_dict(y_true, y_pred, num_classes)
    report["split"] = args.split
    report["arch"] = meta.get("arch")
    report["weight"] = str(weight)
    report["inference_seconds"] = round(elapsed, 3)
    report["avg_latency_ms"] = round(elapsed / max(len(ds), 1) * 1000, 2)
    report["avg_confidence"] = round(sum(y_conf) / max(len(y_conf), 1), 4)

    reports = PROJECT_ROOT / "outputs" / "reports"
    arch_tag = str(meta.get("arch", "model"))
    save_json(report, reports / f"metrics_{arch_tag}_{args.split}.json")
    plot_confusion_matrix(report["confusion_matrix"], report["labels"],
                          reports / f"confusion_matrix_{arch_tag}.png",
                          title=f"{arch_tag} 测试集混淆矩阵")
    plot_confusion_matrix(report["confusion_matrix"], report["labels"],
                          reports / f"confusion_matrix_norm_{arch_tag}.png",
                          title=f"{arch_tag} 测试集混淆矩阵（归一化）", normalize=True)

    lines = [
        f"模型: {arch_tag}   数据划分: {args.split}   样本数: {report['num_samples']}",
        f"整体准确率 Accuracy : {report['accuracy']:.4f}",
        f"宏平均精确率 Macro-P: {report['macro_precision']:.4f}",
        f"宏平均召回率 Macro-R: {report['macro_recall']:.4f}",
        f"宏平均 F1    Macro-F1: {report['macro_f1']:.4f}",
        f"加权 F1      Weighted-F1: {report['weighted_f1']:.4f}",
        f"平均单图耗时: {report['avg_latency_ms']:.2f} ms",
        "",
        f"{'类别':<12}{'Precision':>10}{'Recall':>10}{'F1':>10}{'Support':>10}",
        "-" * 52,
    ]
    for c in report["per_class"]:
        lines.append(f"{c['class_name']:<12}{c['precision']:>10.4f}{c['recall']:>10.4f}"
                     f"{c['f1']:>10.4f}{c['support']:>10d}")
    text = "\n".join(lines)
    (reports / f"report_{arch_tag}_{args.split}.txt").write_text(text, encoding="utf-8")
    print("\n" + text)
    print(f"\n混淆矩阵已保存: {reports / f'confusion_matrix_{arch_tag}.png'}")

    # ---------- 可选：两个模型对比 ----------
    if args.compare:
        cmp_path = Path(args.compare)
        if not cmp_path.is_absolute():
            cmp_path = PROJECT_ROOT / cmp_path
        model2, meta2 = load_model(cmp_path, device, args.compare_arch)
        t1 = time.perf_counter()
        yt2, yp2, _ = predict_loader(model2, loader, device)
        el2 = time.perf_counter() - t1
        rep2 = classification_report_dict(yt2, yp2, num_classes)
        summary = [
            {"model": meta.get("arch"), "accuracy": report["accuracy"],
             "macro_f1": report["macro_f1"], "avg_latency_ms": round(elapsed / len(ds) * 1000, 2),
             "params_total": meta.get("params_total")},
            {"model": meta2.get("arch"), "accuracy": rep2["accuracy"],
             "macro_f1": rep2["macro_f1"], "avg_latency_ms": round(el2 / len(ds) * 1000, 2),
             "params_total": meta2.get("params_total")},
        ]
        save_json(summary, reports / "model_comparison.json")
        print("\n==== 模型对比 ====")
        for s in summary:
            print(f"{s['model']:<22} Acc={s['accuracy']:.4f}  Macro-F1={s['macro_f1']:.4f}  "
                  f"单图耗时={s['avg_latency_ms']:.2f} ms")


if __name__ == "__main__":
    main()
