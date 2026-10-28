"""非目标图像门控 —— 判断输入是不是「玉米叶片」，不重新训练模型。

问题：4 分类 softmax 一定会在 4 个病名里挑一个，对桌面、天空、截图、纯色也会
输出「玉米锈病 0.62」，前端照旧给处方。

做法（三者取或，任一满足即认为像叶片）：
  1. 颜色/植被指数：绿色像素占比、超绿指数 ExG —— 明显是绿色组织的直接放行；
  2. 特征空间余弦距离：模型 avgpool 特征到已知类中心的距离（类中心由训练集离线统计，
     见 scripts/build_gate_centroids.py）—— 颜色不像但特征像（黄褐色重病叶、逆光叶）；
  3. 置信度兜底：仅在类中心文件缺失时启用（阈值更严）。

阈值默认值来自 MCDD 测试集（48 张真叶）+ 截图/纯色/噪声/渐变（12 张）实测：
  正样本 48/48 通过，负样本 12/12 拦截（见提交说明）。
可用环境变量微调：LEAF_GATE_GREEN / LEAF_GATE_EXG / LEAF_GATE_COS。
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np
from PIL import Image

_ASSET = Path(__file__).resolve().parent.parent / "assets" / "gate" / "centroids.npz"


def _env_float(name: str, default: float) -> float:
    try:
        return float(os.environ.get(name, default))
    except (TypeError, ValueError):
        return default


# 颜色白名单（明显是绿色植物组织）
GREEN_RATIO_PASS = _env_float("LEAF_GATE_GREEN", 0.25)
EXG_PASS = _env_float("LEAF_GATE_EXG", 0.10)
# 特征距离（越小越像）
COS_PASS = _env_float("LEAF_GATE_COS", 0.60)
# 灰区救援：特征距离略远、但模型极其自信时放行（重病斑叶片特征会偏离健康叶中心）
COS_GRAY = _env_float("LEAF_GATE_COS_GRAY", 0.85)
CONF_RESCUE = _env_float("LEAF_GATE_CONF_RESCUE", 0.90)
MARGIN_RESCUE = _env_float("LEAF_GATE_MARGIN_RESCUE", 0.30)
# 无类中心时的置信度兜底
CONF_PASS = _env_float("LEAF_GATE_CONF", 0.85)
MARGIN_PASS = _env_float("LEAF_GATE_MARGIN", 0.20)


def color_metrics(img: Image.Image) -> Dict[str, float]:
    """颜色/纹理统计（0~1 量纲，便于打印与调阈值）。"""
    arr = np.asarray(img.convert("RGB").resize((160, 160), Image.BILINEAR), dtype=np.float32) / 255.0
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]
    exg = 2 * g - r - b
    mn, mx = arr.min(axis=2), arr.max(axis=2)
    sat = np.where(mx > 0, (mx - mn) / (mx + 1e-6), 0.0)
    greenish = ((exg > 0.06) & (g > r) & (g > b) & (sat > 0.15)).mean()
    gray = arr.mean(axis=2)
    texture = float(np.abs(np.diff(gray, axis=1)).mean() + np.abs(np.diff(gray, axis=0)).mean())
    return {
        "green_ratio": float(greenish),
        "exg_mean": float(exg.mean()),
        "sat_mean": float(sat.mean()),
        "texture": texture,
    }


class LeafGate:
    """加载类中心并提供 evaluate()；类中心缺失时降级为「颜色 + 置信度」判断。"""

    def __init__(self, centroids_path: Optional[str | Path] = None) -> None:
        self.path = Path(centroids_path) if centroids_path else _ASSET
        self.centroids: Dict[str, np.ndarray] = {}
        self._load()

    def _load(self) -> None:
        try:
            if self.path.exists():
                data = np.load(self.path)
                self.centroids = {k: data[k].astype(np.float32) for k in data.files}
        except Exception:  # noqa: BLE001
            self.centroids = {}

    @property
    def ready(self) -> bool:
        return bool(self.centroids)

    def evaluate(
        self,
        img: Image.Image,
        feature: Optional[np.ndarray] = None,
        prob: Optional[np.ndarray] = None,
    ) -> Dict[str, Any]:
        """返回 {is_target, score, reasons, metrics}。"""
        cm = color_metrics(img)
        metrics: Dict[str, Any] = dict(cm)
        reasons = []

        color_hit = cm["green_ratio"] >= GREEN_RATIO_PASS or cm["exg_mean"] >= EXG_PASS
        if color_hit:
            reasons.append("颜色/植被指数符合叶片特征")

        cos_dist = None
        if feature is not None and self.ready:
            f = feature.astype(np.float32).ravel()
            n = float(np.linalg.norm(f)) + 1e-8
            fn = f / n
            cos_dist = min(1.0 - float(fn @ c) for c in self.centroids.values())
            metrics["cos_dist"] = round(cos_dist, 4)

        margin = None
        if prob is not None and len(prob) > 1:
            s = np.sort(prob)[::-1]
            metrics["top1"] = round(float(s[0]), 4)
            metrics["margin"] = round(float(s[0] - s[1]), 4)
            margin = float(s[0] - s[1])

        feature_hit = cos_dist is not None and cos_dist <= COS_PASS
        if feature_hit:
            reasons.append(f"特征接近已知类别（距离 {cos_dist:.2f}）")

        # 灰区救援：距离偏大但模型极自信（典型是病斑占满的叶片，特征被病斑拉偏）
        rescue_hit = False
        if (
            cos_dist is not None
            and not feature_hit
            and cos_dist <= COS_GRAY
            and metrics.get("top1", 0.0) >= CONF_RESCUE
            and (margin is None or margin >= MARGIN_RESCUE)
        ):
            rescue_hit = True
            reasons.append(
                f"特征距离偏大（{cos_dist:.2f}）但置信度极高（{metrics['top1']:.2f}），判为病斑异常样本"
            )

        # 类中心不可用时，退化为置信度兜底（更严，宁拦勿放）
        conf_hit = False
        if not self.ready and prob is not None:
            conf_hit = (
                metrics.get("top1", 0.0) >= CONF_PASS
                and (margin is None or margin >= MARGIN_PASS)
            )
            if conf_hit:
                reasons.append("置信度与间隔达到阈值（无类中心，兜底判断）")

        is_target = bool(color_hit or feature_hit or conf_hit or rescue_hit)
        if not is_target:
            if cos_dist is not None:
                reasons.append(f"颜色不像叶片，且特征距离 {cos_dist:.2f} > {COS_PASS}")
            else:
                reasons.append("颜色与置信度均不满足叶片条件")

        # 综合分数：越像 1 越像叶片
        score = 0.0
        if color_hit:
            score = max(score, 0.75)
        if feature_hit:
            score = max(score, min(0.95, 1.0 - cos_dist / max(COS_PASS, 1e-6) * 0.25))
        if conf_hit:
            score = max(score, 0.6)

        return {
            "is_target": is_target,
            "score": round(float(score), 3),
            "reasons": reasons,
            "metrics": metrics,
            "centroids": len(self.centroids),
        }
