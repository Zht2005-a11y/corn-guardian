"""数据加载与预处理模块。

核心职责：
1. 适配 ImageFolder 文件夹分类结构，并支持 **多个数据集源合并**（后续新增数据集直接改 yaml）；
2. 提供训练专属的数据增强（翻转 / 旋转 / 颜色抖动 / 随机缩放裁剪）；
3. 测试集只做确定性变换（resize + 中心裁剪 + 归一化），保证评估可复现；
4. 输出类别名与索引的对应关系，支持中文标签映射。

【为什么要在 ImageFolder 之外再包一层】
MCDD 只提供 train/test，没有验证集；同时不同数据集的文件夹命名可能不一致
（如 Rust / Common_Rust）。这里用 `MergedImageFolder` 做三件事：
  - 把各数据集的类别名归一到标准类别名；
  - 把多个数据集的样本列表拼在一起；
  - 按 `val_ratio` 分层切分出验证集，避免小类别在验证集中"消失"。
"""
from __future__ import annotations

# 说明：本模块顶层的 torch / torchvision 依赖全部写在函数内部（懒加载），
# 这样只做数据集统计时无需安装 PyTorch；训练时依旧完全等价。
import json
import os
import random
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from PIL import Image

from .config import get_class_names, get_class_cn, normalize_class_name

IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".JPG", ".JPEG", ".PNG"}

# ImageNet 标准化参数（使用预训练权重必须严格一致）
IMAGENET_MEAN = [0.485, 0.456, 0.406]
IMAGENET_STD = [0.229, 0.224, 0.225]


# ==========================================================================
#  transforms
# ==========================================================================
def build_train_transform(image_size: int = 224):
    """玉米叶片图像专用训练增强。

    （返回 torchvision.transforms.Compose；返回类型不写死以免顶层依赖 torchvision）

    设计依据（为什么这样选）：
    - 田间拍摄角度随意 -> 水平/垂直翻转 + ±30° 旋转，模拟相机位姿变化；
    - 光照条件差异大   -> 亮度/对比度/饱和度抖动，提升对强光、阴天、阴影的鲁棒性；
    - 拍摄距离不一致   -> RandomResizedCrop(scale 0.6~1.0) 模拟远近与目标占比变化；
    - 病斑相对位置是识别关键，不宜做大幅平移或过度裁剪，故 scale 下限不低于 0.6；
    - 使用 ImageNet 归一化，与预训练权重分布对齐。
    """
    from torchvision import transforms

    return transforms.Compose(
        [
            transforms.RandomResizedCrop(image_size, scale=(0.6, 1.0), ratio=(0.85, 1.15)),
            transforms.RandomHorizontalFlip(p=0.5),
            transforms.RandomVerticalFlip(p=0.2),  # 叶片上下颠倒也常见，但概率略低
            transforms.RandomRotation(degrees=30, fill=(0, 0, 0)),
            transforms.ColorJitter(brightness=0.3, contrast=0.3, saturation=0.2, hue=0.02),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
            transforms.RandomErasing(p=0.15, scale=(0.02, 0.08), value=0),  # 模拟遮挡/脏污
        ]
    )


def build_eval_transform(image_size: int = 224):
    """验证/测试/推理统一变换：不做任何随机增强，保证结果可复现。"""
    from torchvision import transforms

    resize = int(round(image_size / 0.875))  # 224 -> 256，与经典 ResNet 评估流程一致
    return transforms.Compose(
        [
            transforms.Resize(resize, interpolation=transforms.InterpolationMode.BICUBIC),
            transforms.CenterCrop(image_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
        ]
    )


# ==========================================================================
#  数据集：多源合并 + 类别归一 + 分层切分
# ==========================================================================
Sample = Tuple[str, int]  # (图片绝对路径, 类别索引)


class MergedImageFolder:
    """基于文件索引的通用分类数据集（不依赖 ImageFolder 的目录强约束）。

    参数
    ----
    samples: [(path, label_index), ...]
    class_names: 标准类别名列表
    transform: 图像变换

    注意：只实现 __len__ / __getitem__，torch 的 DataLoader 通过鸭子类型即可使用，
    因此本类不继承 torch.utils.data.Dataset —— 这样不安装 torch 也能做数据统计。
    """

    def __init__(
        self,
        samples: Sequence[Sample],
        class_names: Sequence[str],
        transform: Optional[Callable] = None,
    ) -> None:
        self.samples: List[Sample] = list(samples)
        self.class_names = list(class_names)
        self.transform = transform
        self.targets = [s[1] for s in self.samples]

    def __len__(self) -> int:
        return len(self.samples)

    def __getitem__(self, index: int):
        path, label = self.samples[index]
        try:
            img = Image.open(path)
            img = img.convert("RGB")  # 统一 3 通道，兼容灰度图 / 带 alpha 的 PNG
        except Exception:
            # 损坏图片：返回纯黑图，训练时不会中断；推理侧另有异常检测
            img = Image.new("RGB", (224, 224), (0, 0, 0))
        if self.transform is not None:
            img = self.transform(img)
        return img, label

    # ---- 便于打印数据集信息 ----
    @property
    def class_to_idx(self) -> Dict[str, int]:
        return {name: i for i, name in enumerate(self.class_names)}

    def class_distribution(self) -> Dict[str, int]:
        cnt = Counter(self.targets)
        return {self.class_names[i]: cnt.get(i, 0) for i in range(len(self.class_names))}

    # 便于与 torch 生态互通（DataLoader 的 collate 只要求可下标访问）
    @property
    def classes(self) -> List[str]:
        return list(self.class_names)


def _scan_split_dir(
    split_dir: Path, class_names: Sequence[str]
) -> Tuple[List[Sample], Dict[str, int]]:
    """扫描 <split_dir>/<类别>/xxx.jpg，返回样本列表与"被跳过的未识别类别"统计。"""
    name_to_idx = {n: i for i, n in enumerate(class_names)}
    samples: List[Sample] = []
    skipped: Dict[str, int] = defaultdict(int)

    if not split_dir.exists():
        return samples, dict(skipped)

    for cls_dir in sorted(p for p in split_dir.iterdir() if p.is_dir()):
        std_name = normalize_class_name(cls_dir.name)
        if std_name not in name_to_idx:
            n = sum(1 for f in cls_dir.rglob("*") if f.suffix in IMG_EXTS)
            skipped[cls_dir.name] = n
            continue
        label = name_to_idx[std_name]
        for f in cls_dir.rglob("*"):
            if f.is_file() and f.suffix in IMG_EXTS:
                samples.append((str(f.resolve()), label))
    return samples, dict(skipped)


def stratified_split(
    samples: Sequence[Sample], val_ratio: float, seed: int
) -> Tuple[List[Sample], List[Sample]]:
    """按类别分层切分训练/验证集，保证每个类别都有代表样本。"""
    rng = random.Random(seed)
    by_class: Dict[int, List[Sample]] = defaultdict(list)
    for s in samples:
        by_class[s[1]].append(s)

    train, val = [], []
    for label in sorted(by_class):
        items = by_class[label][:]
        rng.shuffle(items)
        n_val = max(1, int(round(len(items) * val_ratio))) if len(items) > 1 else 0
        val.extend(items[:n_val])
        train.extend(items[n_val:])
    rng.shuffle(train)
    rng.shuffle(val)
    return train, val


def collect_samples(
    cfg: Dict[str, Any], use_for_train_only: bool = True
) -> Tuple[List[Sample], List[Sample], Dict[str, Any]]:
    """汇总所有数据集源的 train / test 样本。

    返回 (train_samples, test_samples, info)
    info 包含每个源扫描到的样本数、跳过的类别等，用于日志与答辩材料。
    """
    class_names = get_class_names(cfg)
    data_cfg = cfg.get("data", {})
    all_train: List[Sample] = []
    all_test: List[Sample] = []
    info: Dict[str, Any] = {"sources": [], "class_names": class_names}

    for src in data_cfg.get("sources", []):
        root = Path(src["root"])
        if not root.exists():
            info["sources"].append({"name": src.get("name"), "error": f"路径不存在: {root}"})
            continue
        train_samples, skipped_tr = _scan_split_dir(root / src["train_dir"], class_names)
        test_samples, skipped_te = _scan_split_dir(root / src["test_dir"], class_names)
        if src.get("use_for_train", True):
            all_train.extend(train_samples)
        # evaluate=False 的数据源（没有官方测试划分）只提供训练样本，
        # 避免与训练集重复的图片进入评估导致"指标虚高"。
        include_test = src.get("evaluate", True)
        if include_test:
            all_test.extend(test_samples)
        info["sources"].append(
            {
                "name": src.get("name"),
                "root": str(root),
                "train_images": len(train_samples),
                "test_images": len(test_samples) if include_test else 0,
                "skipped_train_classes": skipped_tr,
                "skipped_test_classes": skipped_te,
                "use_for_train": src.get("use_for_train", True),
                "evaluate": include_test,
            }
        )

    info["train_total"] = len(all_train)
    info["test_total"] = len(all_test)
    info["train_distribution"] = _dist(all_train, class_names)
    info["test_distribution"] = _dist(all_test, class_names)
    return all_train, all_test, info


def _dist(samples: Sequence[Sample], class_names: Sequence[str]) -> Dict[str, int]:
    cnt = Counter(s[1] for s in samples)
    return {class_names[i]: cnt.get(i, 0) for i in range(len(class_names))}


def _limit_balanced(samples: Sequence[Sample], limit: int) -> List[Sample]:
    """按类别轮转取样，把样本数限制到 limit 左右（保证每个类别都有样本）。"""
    if len(samples) <= limit:
        return list(samples)
    by_class: Dict[int, List[Sample]] = defaultdict(list)
    for s in samples:
        by_class[s[1]].append(s)
    picked: List[Sample] = []
    queues = {k: v[:] for k, v in by_class.items()}
    while len(picked) < limit and any(queues.values()):
        for k in sorted(queues):
            if queues[k] and len(picked) < limit:
                picked.append(queues[k].pop(0))
    return picked


def build_datasets(
    cfg: Dict[str, Any],
    image_size: Optional[int] = None,
    with_verify: bool = False,
) -> Tuple[Any, Any, Any, Dict[str, Any]]:
    """构建 train / val / test 三个 Dataset。

    注意：验证集使用 eval 变换（不加增强），否则验证指标会被随机性污染。
    """
    image_size = image_size or cfg.get("train", {}).get("image_size", 224)
    data_cfg = cfg.get("data", {})
    class_names = get_class_names(cfg)

    # 1) 优先用 ImageFolder 校验目录合法性（用户初次配置错误时可给出清晰报错）
    if with_verify:
        _verify_with_imagefolder(data_cfg, class_names)

    # 2) 扫描所有数据源
    train_all, test_samples, info = collect_samples(cfg)
    if not train_all:
        raise RuntimeError(
            "未扫描到任何训练图片，请检查 configs/config.yaml 中 data.sources[].root 是否正确。\n"
            f"当前扫描详情: {json.dumps(info, ensure_ascii=False)}"
        )
    if not test_samples:
        raise RuntimeError("未扫描到测试图片，请检查 test_dir 配置。")

    # 3) 从 train 中分层切出验证集
    train_samples, val_samples = stratified_split(
        train_all, data_cfg.get("val_ratio", 0.15), data_cfg.get("split_seed", 42)
    )

    # 3.5) 可选：限制训练/测试样本数（仅用于单元测试 / 快速冒烟，正式训练不要配置）
    limit = data_cfg.get("limit_per_split")
    if limit:
        train_samples = _limit_balanced(train_samples, int(limit))
        val_samples = _limit_balanced(val_samples, max(4, int(limit) // 4))
        test_samples = _limit_balanced(test_samples, int(limit))

    train_ds = MergedImageFolder(train_samples, class_names, build_train_transform(image_size))
    val_ds = MergedImageFolder(val_samples, class_names, build_eval_transform(image_size))
    test_ds = MergedImageFolder(test_samples, class_names, build_eval_transform(image_size))

    info["final"] = {
        "train": len(train_ds),
        "val": len(val_ds),
        "test": len(test_ds),
        "train_distribution": train_ds.class_distribution(),
        "val_distribution": val_ds.class_distribution(),
        "test_distribution": test_ds.class_distribution(),
    }
    return train_ds, val_ds, test_ds, info


def _verify_with_imagefolder(data_cfg: Dict[str, Any], class_names: Sequence[str]) -> None:
    """用 ImageFolder 对第一个可用数据源做格式校验（顺带输出类别索引对应关系）。"""
    for src in data_cfg.get("sources", []):
        root = Path(src["root"])
        if not (root.exists() and (root / src["train_dir"]).exists()):
            continue
        from torchvision.datasets import ImageFolder

        probe = ImageFolder(str(root / src["train_dir"]))
        mapping = {v: k for k, v in probe.class_to_idx.items()}
        print(f"[数据校验] ImageFolder 识别到 {len(probe.classes)} 个类别: {mapping}")
        for idx, cn_name in sorted(mapping.items()):
            std = normalize_class_name(cn_name)
            flag = "OK" if std in class_names else "未在 class_names 中，将被跳过"
            print(f"          索引 {idx}: {cn_name} -> {get_class_cn(class_names.index(std)) if std in class_names else '-'} [{flag}]")
        break


# ==========================================================================
#  DataLoader
# ==========================================================================
def build_loaders(
    train_ds: Any,
    val_ds: Any,
    test_ds: Any,
    cfg: Dict[str, Any],
    balance_sampler: bool = False,
) -> Tuple[Any, Any, Any]:
    """构建三个 DataLoader。

    balance_sampler=True 时对训练集使用 WeightedRandomSampler，
    用于缓解类别不平衡（Gray_Leaf_Spot 样本约为 Blight 的 1/3）。
    """
    import torch
    from torch.utils.data import DataLoader

    data_cfg = cfg.get("data", {})
    train_cfg = cfg.get("train", {})
    bs = train_cfg.get("batch_size", 32)
    workers = data_cfg.get("num_workers", 4)
    pin = torch.cuda.is_available()
    persistent = workers > 0

    sampler = None
    shuffle = True
    if balance_sampler:
        sampler = build_weighted_sampler(train_ds)  # type: ignore[arg-type]
        shuffle = False

    train_loader = DataLoader(
        train_ds,
        batch_size=bs,
        shuffle=shuffle,
        sampler=sampler,
        num_workers=workers,
        pin_memory=pin,
        persistent_workers=persistent,
        drop_last=len(train_ds) > bs,
    )
    eval_kw = dict(
        batch_size=bs,
        shuffle=False,
        num_workers=workers,
        pin_memory=pin,
        persistent_workers=persistent,
    )
    val_loader = DataLoader(val_ds, **eval_kw)
    test_loader = DataLoader(test_ds, **eval_kw)
    return train_loader, val_loader, test_loader


def build_weighted_sampler(ds: MergedImageFolder):
    """按类别频率倒数赋权，使每个 batch 中各类别近似均衡。"""
    from torch.utils.data import WeightedRandomSampler

    cnt = Counter(ds.targets)
    weights_per_class = {c: 1.0 / max(n, 1) for c, n in cnt.items()}
    sample_weights = [weights_per_class[t] for t in ds.targets]
    return WeightedRandomSampler(sample_weights, num_samples=len(sample_weights), replacement=True)


def compute_class_weights(ds: Any, num_classes: int):
    """加权交叉熵所需的类别权重：w_c = N / (C * n_c)。"""
    import torch

    targets = getattr(ds, "targets", [])
    cnt = Counter(targets)
    total = max(sum(cnt.values()), 1)
    weights = [total / (num_classes * max(cnt.get(i, 0), 1)) for i in range(num_classes)]
    return torch.tensor(weights, dtype=torch.float32)


# ==========================================================================
#  单张图片（推理用）
# ==========================================================================
class _PathDataset:
    def __init__(self, paths: Sequence[str], transform: Callable) -> None:
        self.paths = list(paths)
        self.transform = transform

    def __len__(self) -> int:
        return len(self.paths)

    def __getitem__(self, i: int):
        p = self.paths[i]
        with Image.open(p) as im:
            img = self.transform(im.convert("RGB"))
        return img, 0


def load_image_tensor(path: str | Path, transform: Callable):
    """读取单张图片并返回 [1,3,H,W] 张量。"""
    with Image.open(path) as im:
        return transform(im.convert("RGB")).unsqueeze(0)


def tensor_to_display(tensor):
    """把归一化后的张量还原成可用于 Grad-CAM 叠加显示的原图。"""
    import numpy as np
    import torch

    mean = torch.tensor(IMAGENET_MEAN).view(3, 1, 1)
    std = torch.tensor(IMAGENET_STD).view(3, 1, 1)
    img = tensor.detach().cpu()[0] * std + mean
    img = img.clamp(0, 1).permute(1, 2, 0).numpy()
    return Image.fromarray((img * 255).astype("uint8"))


def ensure_dir(path: str | Path) -> Path:
    p = Path(path)
    os.makedirs(p, exist_ok=True)
    return p
