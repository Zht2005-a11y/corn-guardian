"""非目标图像门控 —— 判断输入是不是「玉米叶片」，不重新训练模型。

为什么需要：4 分类 softmax 一定会在 4 个病名里挑一个，桌面、天空、绿墙、草地也会
输出「玉米锈病 0.69」，前端照旧给处方。

判定逻辑（按顺序短路，任一命中即通过）：

  1. 特征距离 ≤ 0.60                       —— 和已知四类的特征中心很像，直接放行
  2. 纹理过平（< 0.012）                    —— 纯色、模糊、纯绿渐变，直接拒
  3. 有颜色证据 且 特征距离 ≤ 0.65          —— 绿色/黄褐色组织 + 特征接近
  4. 特征距离 ≤ 0.82 且 top1 ≥ 0.90
     且 top1-top2 ≥ 0.80                    —— 病斑占满整叶时特征会被拉偏，
                                              但模型极其笃定，仍判为叶片
  否则判为非目标。

注意：颜色**不再单独放行**。早期版本只要绿色占比 ≥0.25 就通过，结果纯绿图片
（纯色、噪声、渐变）全部漏网，这是本次修复的核心。

类中心按模型分别统计（不同网络的 avgpool 特征空间不可混用），
由 scripts/build_gate_centroids.py 生成到 assets/gate/centroids.npz。
阈值可用环境变量覆盖：LEAF_GATE_COS / LEAF_GATE_COLOR_COS / LEAF_GATE_GREEN /
LEAF_GATE_EXG / LEAF_GATE_RESCUE_COS / LEAF_GATE_MIN_TEXTURE。
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


# 特征距离主阈值
COS_PASS = _env_float("LEAF_GATE_COS", 0.60)
# 颜色证据 + 特征距离（放宽一档）
COLOR_COS = _env_float("LEAF_GATE_COLOR_COS", 0.65)
GREEN_RATIO = _env_float("LEAF_GATE_GREEN", 0.35)
EXG_MIN = _env_float("LEAF_GATE_EXG", 0.12)
# 纹理下限：低于此值视为纯色 / 模糊
MIN_TEXTURE = _env_float("LEAF_GATE_MIN_TEXTURE", 0.012)
# 灰区救援：特征偏大但模型极笃定
RESCUE_COS = _env_float("LEAF_GATE_RESCUE_COS", 0.82)
RESCUE_TOP1 = _env_float("LEAF_GATE_RESCUE_TOP1", 0.90)
RESCUE_MARGIN = _env_float("LEAF_GATE_RESCUE_MARGIN", 0.80)
# 完全没有类中心时的兜底
FALLBACK_TOP1 = _env_float("LEAF_GATE_FALLBACK_TOP1", 0.85)


def color_metrics(img: Image.Image) -> Dict[str, float]:
    """颜色 / 纹理统计（0~1 量纲）。"""
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
    """按模型加载类中心并提供 evaluate()。"""

    def __init__(self, centroids_path: Optional[str | Path] = None) -> None:
        self.path = Path(centroids_path) if centroids_path else _ASSET
        self.centroids: Dict[str, Dict[str, np.ndarray]] = {}
        self._load()

    def _load(self) -> None:
        """npz 的键形如 'resnet50_cbam::Blight'；兼容旧的纯类名键（视为 cbam）。"""
        try:
            if not self.path.exists():
                return
            data = np.load(self.path)
            for k in data.files:
                vec = data[k].astype(np.float32)
                if "::" in k:
                    model_key, cls = k.split("::", 1)
                else:
                    model_key, cls = "resnet50_cbam", k
                self.centroids.setdefault(model_key, {})[cls] = vec
        except Exception:  # noqa: BLE001
            self.centroids = {}

    @property
    def ready(self) -> bool:
        return bool(self.centroids)

    def models(self):
        return sorted(self.centroids)

    def evaluate(
        self,
        img: Image.Image,
        feature: Optional[np.ndarray] = None,
        prob: Optional[np.ndarray] = None,
        model_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        cm = color_metrics(img)
        metrics: Dict[str, Any] = dict(cm)
        reasons = []

        cents = self.centroids.get(model_key or "", {})
        cos_dist = None
        if feature is not None and cents:
            f = feature.astype(np.float32).ravel()
            f = f / (float(np.linalg.norm(f)) + 1e-8)
            cos_dist = min(1.0 - float(f @ c) for c in cents.values())
            metrics["cos_dist"] = round(cos_dist, 4)

        margin = None
        if prob is not None and len(prob) > 1:
            s = np.sort(prob)[::-1]
            metrics["top1"] = round(float(s[0]), 4)
            metrics["margin"] = round(float(s[0] - s[1]), 4)
            margin = float(s[0] - s[1])

        color_ok = cm["green_ratio"] >= GREEN_RATIO or cm["exg_mean"] >= EXG_MIN
        metrics["color_ok"] = color_ok
        metrics["gate_model"] = model_key or ""

        is_target = False
        if cos_dist is not None:
            if cos_dist <= COS_PASS:
                is_target = True
                reasons.append(f"特征接近已知类别（距离 {cos_dist:.2f}）")
            elif cm["texture"] < MIN_TEXTURE:
                is_target = False
                reasons.append(f"纹理过于平坦（{cm['texture']:.3f}），判为纯色/模糊图")
            elif color_ok and cos_dist <= COLOR_COS:
                is_target = True
                reasons.append(f"颜色符合叶片组织且特征可接受（距离 {cos_dist:.2f}）")
            elif (
                cos_dist <= RESCUE_COS
                and metrics.get("top1", 0) >= RESCUE_TOP1
                and (margin is None or margin >= RESCUE_MARGIN)
            ):
                is_target = True
                reasons.append(
                    f"特征偏大（{cos_dist:.2f}）但模型极笃定"
                    f"（{metrics['top1']:.2f}/{margin:.2f}），判为病斑异常叶片"
                )
            else:
                reasons.append(f"特征距离 {cos_dist:.2f} 超出阈值，且不满足颜色/置信度条件")
        else:
            # 没有该模型的类中心：只用颜色 + 置信度兜底，并明确标注
            is_target = bool(color_ok and metrics.get("top1", 0) >= FALLBACK_TOP1)
            reasons.append("缺少该模型的类中心，使用颜色+置信度兜底判断")

        score = 0.0
        if cos_dist is not None:
            score = round(max(0.0, min(1.0, 1.0 - cos_dist)), 3)
        if is_target:
            score = max(score, 0.6)

        return {
            "is_target": bool(is_target),
            "score": score,
            "reasons": reasons,
            "metrics": metrics,
            "models": self.models(),
        }
