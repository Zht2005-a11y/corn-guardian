"""Grad-CAM 可视化：高亮模型判断时关注的叶片区域（答辩可视化加分项）。

原理（简述，便于答辩讲解）：
1. 取模型最后一个卷积层（ResNet 的 layer4）的输出特征图 A（C×h×w）；
2. 对目标类别的 logit 反向求导，得到梯度 G，对 G 在空间维做全局平均池化得到通道权重 α_c；
3. 加权求和 ReLU(A·α) 得到热力图，再双线性插值回原图尺寸；
4. 用 JET 伪彩色与原图叠加，红色/黄色区域即为模型关注区域。
"""
from __future__ import annotations

import base64
import io
from pathlib import Path
from typing import Optional, Tuple

import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from PIL import Image


class GradCAM:
    """通用 Grad-CAM（支持 ResNet 的 layer4 与 MobileNetV3 的 features[-1]）。"""

    def __init__(self, model: nn.Module, target_layer: Optional[nn.Module] = None) -> None:
        self.model = model
        self.model.eval()
        self.target_layer = target_layer or self._find_target_layer(model)
        self._activations: Optional[torch.Tensor] = None
        self._gradients: Optional[torch.Tensor] = None
        self._handles = [
            self.target_layer.register_forward_hook(self._forward_hook),
            # full_backward_hook 在部分版本已废弃，用 tensor hook 更稳
            self.target_layer.register_full_backward_hook(self._backward_hook),
        ]

    @staticmethod
    def _find_target_layer(model: nn.Module) -> nn.Module:
        if hasattr(model, "layer4"):
            # 若 layer4 被 CBAM 包装，取内部的特征提取块，保证拿到的是卷积输出
            return getattr(model.layer4, "block", model.layer4)
        if hasattr(model, "features"):
            return model.features[-1]
        raise AttributeError("未找到合适的 Grad-CAM 目标层，请手动传入 target_layer")

    def _forward_hook(self, module, inputs, output):
        self._activations = output.detach()

    def _backward_hook(self, module, grad_input, grad_output):
        self._gradients = grad_output[0].detach()

    def remove(self) -> None:
        for h in self._handles:
            h.remove()
        self._handles = []

    def __call__(self, tensor: torch.Tensor, class_idx: Optional[int] = None) -> Tuple[np.ndarray, int]:
        """输入 [1,3,H,W]（已归一化），返回 (热力图 float32[H,W] ∈[0,1], 预测类别索引)。"""
        self.model.zero_grad(set_to_none=True)
        tensor = tensor.clone().requires_grad_(True)
        logits = self.model(tensor)
        probs = torch.softmax(logits.float(), dim=1)
        if class_idx is None:
            class_idx = int(probs.argmax(1).item())

        score = logits[0, class_idx]
        score.backward(retain_graph=False)

        if self._activations is None or self._gradients is None:
            raise RuntimeError("Grad-CAM 未捕获到特征图/梯度，请检查 target_layer 是否正确")

        acts = self._activations[0]          # C,h,w
        grads = self._gradients[0]           # C,h,w
        weights = grads.mean(dim=(1, 2), keepdim=True)  # 通道权重 α
        cam = torch.relu((weights * acts).sum(dim=0))   # 只保留正向贡献

        cam = cam - cam.min()
        cam = cam / (cam.max() + 1e-8)
        cam = F.interpolate(cam[None, None], size=tensor.shape[-2:],
                            mode="bilinear", align_corners=False)[0, 0]
        self.model.zero_grad(set_to_none=True)
        return cam.cpu().numpy(), class_idx


def _colormap(cam: np.ndarray) -> np.ndarray:
    """轻量 JET 伪彩色（不依赖 OpenCV，RGB uint8）。"""
    cam = np.clip(cam, 0, 1)
    r = np.clip(1.5 - np.abs(4 * cam - 3), 0, 1)
    g = np.clip(1.5 - np.abs(4 * cam - 2), 0, 1)
    b = np.clip(1.5 - np.abs(4 * cam - 1), 0, 1)
    return (np.stack([r, g, b], axis=-1) * 255).astype(np.uint8)


def overlay_cam(image: Image.Image, cam: np.ndarray, alpha: float = 0.45) -> Image.Image:
    """把热力图叠加到原图上。"""
    base = image.convert("RGB").resize((cam.shape[1], cam.shape[0]), Image.BICUBIC)
    heat = Image.fromarray(_colormap(cam))
    return Image.blend(base, heat, alpha=alpha)


def cam_to_base64(image: Image.Image, fmt: str = "PNG") -> str:
    """转成前端 <img src> 可直接用的 base64 字符串。"""
    buf = io.BytesIO()
    image.save(buf, format=fmt)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def save_cam(image: Image.Image, cam: np.ndarray, save_path: str | Path, alpha: float = 0.45) -> Path:
    out = Path(save_path)
    out.parent.mkdir(parents=True, exist_ok=True)
    overlay_cam(image, cam, alpha).save(out)
    return out
