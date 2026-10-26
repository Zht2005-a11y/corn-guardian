"""评估指标与可视化：准确率、精确率/召回率/F1、混淆矩阵、训练曲线。"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List, Sequence

import numpy as np

import matplotlib

matplotlib.use("Agg")  # 服务器 / 无显示环境下必须使用非交互后端
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib import font_manager  # noqa: E402

from .config import CLASS_INDEX_TO_CN  # noqa: E402

# --------------------------------------------------------------------------
# 中文字体：自动探测系统中可用的中文字体，避免坐标轴出现"口口口"
# --------------------------------------------------------------------------
_CJK_CANDIDATES = [
    "Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC",
    "Source Han Sans SC", "WenQuanYi Zen Hei", "PingFang SC", "Arial Unicode MS",
]


def setup_chinese_font() -> str:
    available = {f.name for f in font_manager.fontManager.ttflist}
    for name in _CJK_CANDIDATES:
        if name in available:
            plt.rcParams["font.sans-serif"] = [name] + plt.rcParams.get("font.sans-serif", [])
            plt.rcParams["axes.unicode_minus"] = False
            return name
    plt.rcParams["axes.unicode_minus"] = False
    return ""


def chinese_labels(num_classes: int) -> List[str]:
    return [CLASS_INDEX_TO_CN.get(i, f"类别{i}") for i in range(num_classes)]


# --------------------------------------------------------------------------
# 指标计算（不依赖 sklearn，方便在最小环境里跑通；sklearn 可用时结果一致）
# --------------------------------------------------------------------------
def classification_report_dict(
    y_true: Sequence[int], y_pred: Sequence[int], num_classes: int
) -> Dict:
    """逐类别 precision / recall / f1 / support + 整体指标（macro / weighted）。"""
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    cm = confusion_matrix_np(y_true, y_pred, num_classes)

    labels = chinese_labels(num_classes)
    per_class = []
    for i in range(num_classes):
        tp = cm[i, i]
        fp = cm[:, i].sum() - tp
        fn = cm[i, :].sum() - tp
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        support = int(cm[i, :].sum())
        per_class.append(
            {
                "class_index": i,
                "class_name": labels[i],
                "precision": round(float(precision), 4),
                "recall": round(float(recall), 4),
                "f1": round(float(f1), 4),
                "support": support,
            }
        )

    total = int(cm.sum())
    acc = float(np.trace(cm) / total) if total else 0.0
    macro_p = float(np.mean([c["precision"] for c in per_class]))
    macro_r = float(np.mean([c["recall"] for c in per_class]))
    macro_f1 = float(np.mean([c["f1"] for c in per_class]))
    supports = np.array([c["support"] for c in per_class], dtype=float)
    weighted_f1 = (
        float((np.array([c["f1"] for c in per_class]) * supports).sum() / supports.sum())
        if supports.sum() > 0
        else 0.0
    )

    return {
        "accuracy": round(acc, 4),
        "macro_precision": round(macro_p, 4),
        "macro_recall": round(macro_r, 4),
        "macro_f1": round(macro_f1, 4),
        "weighted_f1": round(weighted_f1, 4),
        "num_samples": total,
        "per_class": per_class,
        "confusion_matrix": cm.tolist(),
        "labels": labels,
    }


def confusion_matrix_np(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int) -> np.ndarray:
    cm = np.zeros((num_classes, num_classes), dtype=np.int64)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def plot_confusion_matrix(
    cm: Sequence[Sequence[int]],
    labels: Sequence[str],
    save_path: str | Path,
    title: str = "混淆矩阵",
    normalize: bool = False,
) -> Path:
    """绘制混淆矩阵（中文类别名），支持归一化显示。"""
    setup_chinese_font()
    cm = np.asarray(cm, dtype=float)
    if normalize:
        row_sum = cm.sum(axis=1, keepdims=True)
        cm_disp = np.divide(cm, row_sum, out=np.zeros_like(cm), where=row_sum != 0)
    else:
        cm_disp = cm

    fig, ax = plt.subplots(figsize=(7.2, 6.2), dpi=150)
    im = ax.imshow(cm_disp, cmap="Blues")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("比例" if normalize else "样本数", rotation=270, labelpad=18)

    ax.set_xticks(range(len(labels)))
    ax.set_yticks(range(len(labels)))
    ax.set_xticklabels(labels, rotation=30, ha="right")
    ax.set_yticklabels(labels)
    ax.set_xlabel("预测类别")
    ax.set_ylabel("真实类别")
    ax.set_title(title)

    thresh = cm_disp.max() / 2.0 if cm_disp.size else 0.5
    for i in range(cm.shape[0]):
        for j in range(cm.shape[1]):
            txt = f"{cm_disp[i, j]:.2f}" if normalize else f"{int(cm[i, j])}"
            ax.text(
                j, i, txt, ha="center", va="center",
                color="white" if cm_disp[i, j] > thresh else "black", fontsize=10,
            )
    fig.tight_layout()
    out = Path(save_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def plot_training_curves(history: List[Dict], save_path: str | Path) -> Path:
    """绘制 loss / accuracy 曲线（训练 + 验证双线，并标注阶段分界）。"""
    setup_chinese_font()
    epochs = [h["epoch"] for h in history]
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), dpi=150)
    single = len(epochs) <= 3  # 样本点太少时用散点更清晰

    axes[0].plot(epochs, [h["train_loss"] for h in history], label="训练损失",
                 marker="o" if single else None)
    axes[0].plot(epochs, [h["val_loss"] for h in history], label="验证损失",
                 marker="s" if single else None)
    axes[0].set_xlabel("Epoch")
    axes[0].set_ylabel("Loss")
    axes[0].set_title("损失曲线")
    axes[0].legend()
    axes[0].grid(alpha=0.3)

    axes[1].plot(epochs, [h["train_acc"] for h in history], label="训练准确率",
                 marker="o" if single else None)
    axes[1].plot(epochs, [h["val_acc"] for h in history], label="验证准确率",
                 marker="s" if single else None)
    axes[1].set_xlabel("Epoch")
    axes[1].set_ylabel("Accuracy")
    axes[1].set_title("准确率曲线")
    axes[1].legend()
    axes[1].grid(alpha=0.3)

    stage2_start = next((h["epoch"] for h in history if h.get("stage") == 2), None)
    if stage2_start:
        for ax in axes:
            ax.axvline(stage2_start - 0.5, color="orange", linestyle="--", alpha=0.8)
        axes[1].text(
            stage2_start, axes[1].get_ylim()[0], " 阶段二：解冻微调",
            color="orange", fontsize=9, va="bottom",
        )

    fig.tight_layout()
    out = Path(save_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)
    return out


def save_json(obj, path: str | Path) -> Path:
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(obj, ensure_ascii=False, indent=2), encoding="utf-8")
    return out
