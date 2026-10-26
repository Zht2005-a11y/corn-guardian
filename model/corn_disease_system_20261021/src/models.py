"""模型构建模块：ResNet50（主）/ MobileNetV3-Large（轻量备选）/ + CBAM 注意力。

【迁移学习原理】
ImageNet 预训练主干已经学到了边缘、纹理、颜色等通用视觉特征；
玉米叶片的病斑本质上是"颜色 + 纹理 + 形状"的组合模式，
因此在数据量只有约 4000 张时，冻结主干只训练分类头（阶段一）可以在
几个 epoch 内得到一个可用基线，再解冻浅层浅调（阶段二）让特征适配
叶片病斑的分布，通常能再提升 2~5 个百分点。
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

import torch
import torch.nn as nn
from torchvision import models


# ==========================================================================
#  CBAM：通道注意力 + 空间注意力（优化方案一）
# ==========================================================================
class ChannelAttention(nn.Module):
    """通道注意力：同时用 平均池化 与 最大池化 汇集全局信息，经共享 MLP 后相加再 Sigmoid。"""

    def __init__(self, channels: int, reduction: int = 16) -> None:
        super().__init__()
        hidden = max(channels // reduction, 8)
        self.avg_pool = nn.AdaptiveAvgPool2d(1)
        self.max_pool = nn.AdaptiveMaxPool2d(1)
        self.mlp = nn.Sequential(
            nn.Conv2d(channels, hidden, 1, bias=False),
            nn.ReLU(inplace=True),
            nn.Conv2d(hidden, channels, 1, bias=False),
        )
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        attn = self.sigmoid(self.mlp(self.avg_pool(x)) + self.mlp(self.max_pool(x)))
        return x * attn


class SpatialAttention(nn.Module):
    """空间注意力：沿通道维做 max/avg 压缩成 2 通道，7x7 卷积学习"哪里重要"。"""

    def __init__(self, kernel_size: int = 7) -> None:
        super().__init__()
        self.conv = nn.Conv2d(2, 1, kernel_size, padding=kernel_size // 2, bias=False)
        self.sigmoid = nn.Sigmoid()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        avg_map = torch.mean(x, dim=1, keepdim=True)
        max_map = torch.max(x, dim=1, keepdim=True)[0]
        attn = self.sigmoid(self.conv(torch.cat([avg_map, max_map], dim=1)))
        return x * attn


class CBAM(nn.Module):
    def __init__(self, channels: int, reduction: int = 16) -> None:
        super().__init__()
        self.ca = ChannelAttention(channels, reduction)
        self.sa = SpatialAttention()

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.sa(self.ca(x))


# ==========================================================================
#  模型工厂
# ==========================================================================
def build_model(
    arch: str = "resnet50",
    num_classes: int = 4,
    pretrained: bool = True,
    dropout: float = 0.3,
    use_cbam: bool = False,
    **_unused: Any,
) -> nn.Module:
    """构建分类模型。

    参数
    ----
    arch: resnet50 | resnet50_cbam | mobilenet_v3_large
    pretrained: 是否加载 ImageNet 权重（训练时 True，加载自训练权重时无所谓）
    dropout: 分类头 dropout（ResNet 原版分类头就是 Dropout+FC，这里沿用）
    """
    arch = arch.lower()
    use_cbam = bool(use_cbam)

    if arch in ("resnet50", "resnet50_cbam"):
        try:
            weights = models.ResNet50_Weights.IMAGENET1K_V2 if pretrained else None
            model = models.resnet50(weights=weights)
        except (AttributeError, TypeError):  # 旧版本 torchvision 兼容
            model = models.resnet50(pretrained=pretrained)

        if use_cbam or arch == "resnet50_cbam":
            # 在 stage3 / stage4 输出后插入 CBAM：越深的层空间分辨率越低、语义越强，
            # 在此处加注意力性价比最高，且不会破坏 stage1/2 的浅层纹理特征。
            model.layer3 = _wrap_with_cbam(model.layer3, 1024)
            model.layer4 = _wrap_with_cbam(model.layer4, 2048)

        in_features = model.fc.in_features
        model.fc = nn.Sequential(
            nn.Dropout(p=dropout),
            nn.Linear(in_features, num_classes),
        )
        return model

    if arch in ("mobilenetv3", "mobilenet_v3_large", "mobilenet_v3"):
        try:
            weights = models.MobileNet_V3_Large_Weights.IMAGENET1K_V2 if pretrained else None
            model = models.mobilenet_v3_large(weights=weights)
        except (AttributeError, TypeError):
            model = models.mobilenet_v3_large(pretrained=pretrained)
        # MobileNetV3 自带 classifier = [Linear, Hardswish, Dropout, Linear]
        in_features = model.classifier[-1].in_features
        model.classifier[-1] = nn.Linear(in_features, num_classes)
        return model

    raise ValueError(f"不支持的模型结构: {arch}，可选: resnet50 / resnet50_cbam / mobilenet_v3_large")


class _CBAMBlock(nn.Module):
    """把原始 stage 包一层，前向结束后做注意力加权。"""

    def __init__(self, block: nn.Module, channels: int) -> None:
        super().__init__()
        self.block = block
        self.cbam = CBAM(channels)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return self.cbam(self.block(x))


def _wrap_with_cbam(block: nn.Module, channels: int) -> nn.Module:
    return _CBAMBlock(block, channels)


# ==========================================================================
#  冻结 / 解冻（两阶段训练的关键工具）
# ==========================================================================
def freeze_backbone(model: nn.Module, arch: str = "resnet50") -> None:
    """阶段一：冻结全部主干参数，仅保留分类头可训练。"""
    for p in model.parameters():
        p.requires_grad = False
    head = _get_head(model, arch)
    for p in head.parameters():
        p.requires_grad = True


def unfreeze_last_blocks(model: nn.Module, arch: str = "resnet50", freeze_until: str = "layer2") -> List[str]:
    """阶段二：解冻最后两个残差块（layer3、layer4）与分类头，其余保持冻结。

    返回被解冻的模块名，便于日志打印。
    """
    # 先全部冻结，再逐层放开
    for p in model.parameters():
        p.requires_grad = False

    unfrozen: List[str] = []
    arch = arch.lower()

    if arch.startswith("resnet"):
        stages = ["layer1", "layer2", "layer3", "layer4"]
        start_idx = stages.index(freeze_until) + 1 if freeze_until in stages else 2
        for name in stages[start_idx:]:
            module = getattr(model, name, None)
            if module is None:
                continue
            for p in module.parameters():
                p.requires_grad = True
            unfrozen.append(name)
        # BatchNorm 统计量在微调时继续更新会导致小 batch 下不稳定，这里统计量冻结、仿射参数可学
        for name in stages[start_idx:]:
            _freeze_bn_stats(getattr(model, name, None))
    else:
        # MobileNetV3：解冻最后若干个 features 子块
        features = getattr(model, "features", None)
        if features is not None:
            n = len(features)
            for i, blk in enumerate(features):
                if i >= n - 3:
                    for p in blk.parameters():
                        p.requires_grad = True
                    unfrozen.append(f"features[{i}]")
            for i in range(max(0, n - 3), n):
                _freeze_bn_stats(features[i])

    for p in _get_head(model, arch).parameters():
        p.requires_grad = True
    unfrozen.append("head")
    return unfrozen


def _freeze_bn_stats(module: Optional[nn.Module]) -> None:
    if module is None:
        return
    for m in module.modules():
        if isinstance(m, (nn.BatchNorm2d, nn.SyncBatchNorm)):
            m.eval()


def _get_head(model: nn.Module, arch: str) -> nn.Module:
    return model.fc if hasattr(model, "fc") else model.classifier  # type: ignore[attr-defined]


def count_parameters(model: nn.Module) -> Dict[str, int]:
    total = sum(p.numel() for p in model.parameters())
    trainable = sum(p.numel() for p in model.parameters() if p.requires_grad)
    return {"total": total, "trainable": trainable}


def build_criterion(
    label_smoothing: float = 0.0,
    class_weights: Optional[torch.Tensor] = None,
    device: Optional[torch.device] = None,
) -> nn.Module:
    """交叉熵损失（支持标签平滑 + 类别权重）。

    - 标签平滑：把 one-hot 的 1 变成 (1-ε)，ε 平均分给其他类，
      抑制模型"过度自信"，对混淆矩阵中相邻病斑的误判有明显缓解；
    - 类别权重：缓解 Gray_Leaf_Spot 等小类被大类别"淹没"的问题。
    """
    cw = class_weights.to(device) if (class_weights is not None and device is not None) else class_weights
    try:
        return nn.CrossEntropyLoss(weight=cw, label_smoothing=float(label_smoothing))
    except TypeError:  # torch < 1.10
        return nn.CrossEntropyLoss(weight=cw)


def build_optimizer(model: nn.Module, lr: float, weight_decay: float) -> torch.optim.Optimizer:
    """AdamW：解耦权重衰减的正则化版本，比 SGD 在迁移学习小数据上更稳。

    只把 requires_grad=True 的参数交给优化器，并让 1D 参数（BN 的 weight/bias）
    不做权重衰减，这是微调 Transformer/CNN 的常用技巧。
    """
    decay, no_decay = [], []
    for name, p in model.named_parameters():
        if not p.requires_grad:
            continue
        if p.ndim <= 1:  # bias / BN weight
            no_decay.append(p)
        else:
            decay.append(p)
    return torch.optim.AdamW(
        [
            {"params": decay, "weight_decay": weight_decay},
            {"params": no_decay, "weight_decay": 0.0},
        ],
        lr=lr,
    )


def build_scheduler(optimizer: torch.optim.Optimizer, total_epochs: int, warmup_epochs: int = 1, eta_min: float = 1e-6):
    """warmup（线性升温）+ 余弦退火 组合调度器。

    为什么需要 warmup：阶段二解冻后的第一批梯度很"脏"，
    直接用大学习率可能破坏预训练权重，先小幅升温再余弦衰减更稳。

    注意：LambdaLR 在构造时就会调用一次 lr_lambda(0)，
    因此内部用 self.last_epoch 计数（构造时从 -1 开始），
    保证第 1 个 epoch 的 lr = base_lr * 1/warmup，最后一个 epoch 衰减到 eta_min。
    """
    import math

    from torch.optim.lr_scheduler import LambdaLR

    warmup = max(0, int(warmup_epochs))
    total = max(1, int(total_epochs))
    base_lr = optimizer.param_groups[0]["lr"]

    def lr_lambda(epoch: int) -> float:
        # LambdaLR 构造时以 epoch=-1 调用一次（初始化），之后每次 step() 递增 1
        if epoch < 0:
            epoch = 0
        warmup_span = max(1, min(warmup, total))
        if warmup > 0 and epoch < warmup_span:
            return float(epoch + 1) / float(warmup_span)
        progress = (epoch - warmup_span) / max(1, total - warmup_span)
        progress = min(max(progress, 0.0), 1.0)
        eta_ratio = eta_min / max(base_lr, 1e-12)
        return eta_ratio + (1 - eta_ratio) * 0.5 * (1 + math.cos(math.pi * progress))

    return LambdaLR(optimizer, lr_lambda)


def current_lr(optimizer: torch.optim.Optimizer) -> float:
    """取当前学习率（日志用）。"""
    return optimizer.param_groups[0]["lr"]
