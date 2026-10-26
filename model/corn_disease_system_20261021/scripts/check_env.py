"""环境自检：一键确认「能否开始 GPU 训练」。

用法（在项目根目录 corn_disease_system/ 下）：
    python -m scripts.check_env
    python -m scripts.check_env --gpu-test      # 额外做一次真实 GPU 前向+反传

检查项：
  1. Python / PyTorch / torchvision 版本，是否为 CUDA 版本
  2. 显卡型号、显存、算力，AMP 是否可用
  3. 数据集两个来源是否存在、类别是否全部归一成功
  4. ImageNet 预训练权重是否已在本地缓存（离线也能训练）
  5. 现有权重文件（正式训练前应为空）
  6. 打印推荐的训练命令
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

OK = "[ OK ]"
BAD = "[ !! ]"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--gpu-test", action="store_true", help="在 GPU 上跑一次模型前向+反传")
    args = ap.parse_args()

    problems = []

    # ---------------- 1. 框架 ----------------
    print("=" * 66)
    print("1) 深度学习框架")
    print("=" * 66)
    try:
        import torch
        import torchvision
    except Exception as e:  # pragma: no cover
        print(f"{BAD} 导入 torch 失败: {e}")
        return 1

    print(f"  Python      : {sys.version.split()[0]}  ({sys.executable})")
    print(f"  PyTorch     : {torch.__version__}")
    print(f"  torchvision : {torchvision.__version__}")
    is_cuda_build = torch.version.cuda is not None
    if is_cuda_build:
        print(f"{OK} CUDA 版本 torch（编译 CUDA {torch.version.cuda}）")
    else:
        print(f"{BAD} 当前是 CPU-only 版 torch，无法使用显卡训练")
        problems.append("torch 是 CPU 版，需安装 CUDA 版")

    # ---------------- 2. 显卡 ----------------
    print()
    print("=" * 66)
    print("2) 显卡")
    print("=" * 66)
    if torch.cuda.is_available():
        n = torch.cuda.device_count()
        for i in range(n):
            prop = torch.cuda.get_device_properties(i)
            print(f"{OK} cuda:{i} {prop.name} | 显存 {prop.total_memory / 1024**3:.1f} GB "
                  f"| 算力 {prop.major}.{prop.minor}")
        print(f"  AMP(混合精度) : {'可用' if hasattr(torch, 'amp') else '不可用'}")
    else:
        print(f"{BAD} torch.cuda.is_available() = False")
        if is_cuda_build:
            problems.append("CUDA 版 torch 已装，但显卡不可用（驱动或显卡被占用）")
        else:
            problems.append("无可用 GPU")

    # ---------------- 3. 数据集 ----------------
    print()
    print("=" * 66)
    print("3) 数据集")
    print("=" * 66)
    from src.config import get_class_names, load_config

    cfg = load_config(str(ROOT / "configs" / "config.yaml"))
    class_names = get_class_names(cfg)
    total = 0
    for src in cfg["data"]["sources"]:
        root = Path(src["root"])
        if not root.exists():
            print(f"{BAD} {src['name']}: 路径不存在 {root}")
            problems.append(f"数据源 {src['name']} 路径不存在")
            continue
        cnt = 0
        for split in {src.get("train_dir", "train"), src.get("test_dir", "test")}:
            d = root / split
            if d.exists():
                cnt += sum(1 for p in d.rglob("*") if p.suffix.lower() in {".jpg", ".jpeg", ".png"})
        total += cnt
        print(f"{OK} {src['name']:<8} {root}  图片 {cnt}")
    print(f"  类别: {class_names}")
    print(f"  图片总量: {total}")

    # ---------------- 4. 预训练权重 ----------------
    print()
    print("=" * 66)
    print("4) ImageNet 预训练权重缓存")
    print("=" * 66)
    cache = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
    for name, size_mb in (("resnet50-0676ba61.pth", 98), ("mobilenet_v3_large-8738ca79.pth", 21)):
        p = cache / name
        if p.exists() and p.stat().st_size > size_mb * 1024 * 1024 * 0.9:
            print(f"{OK} {name}  ({p.stat().st_size / 1024**2:.0f} MB)")
        else:
            print(f"{BAD} {name} 缺失，训练时会自动联网下载（约 {size_mb} MB）")

    # ---------------- 5. 现有权重 ----------------
    print()
    print("=" * 66)
    print("5) 现有权重产物")
    print("=" * 66)
    ckpt_dir = ROOT / "outputs" / "checkpoints"
    files = sorted(ckpt_dir.glob("*.pth")) if ckpt_dir.exists() else []
    if not files:
        print("  （空）")
    for f in files:
        print(f"  {f.name:<34}{f.stat().st_size / 1024**2:8.1f} MB")
    for want in ("best_corn_model.pth", "best_corn_mobilenetv3.pth", "best_corn_model_cbam.pth"):
        print(f"{OK if (ckpt_dir / want).exists() else BAD} {want}")

    # ---------------- 6. GPU 实测 ----------------
    if args.gpu_test and torch.cuda.is_available():
        print()
        print("=" * 66)
        print("6) GPU 前向 + 反传实测")
        print("=" * 66)
        from src.models import build_model, unfreeze_last_blocks

        dev = torch.device("cuda")
        model = build_model(arch="resnet50", num_classes=4, pretrained=False).to(dev)
        unfreeze_last_blocks(model, "resnet50", "layer2")
        opt = torch.optim.AdamW([p for p in model.parameters() if p.requires_grad], lr=1e-4)
        crit = torch.nn.CrossEntropyLoss()
        x = torch.randn(32, 3, 224, 224, device=dev)
        y = torch.randint(0, 4, (32,), device=dev)
        with torch.autocast("cuda", dtype=torch.float16):
            loss = crit(model(x), y)
        loss.backward()
        opt.step()
        torch.cuda.synchronize()
        print(f"{OK} batch=32 前向+反传正常，显存占用 "
              f"{torch.cuda.max_memory_allocated() / 1024**3:.2f} GB")
        del model, opt, x, y
        torch.cuda.empty_cache()

    # ---------------- 结论 ----------------
    print()
    print("=" * 66)
    if problems:
        print("结论: 还不能开始 GPU 训练")
        for p in problems:
            print(f"  - {p}")
        print("=" * 66)
        return 1
    print("结论: 环境就绪，可以开始 GPU 训练")
    print("=" * 66)
    print("主模型（推荐，先跑这个）:")
    print("    python -m scripts.train_full --only resnet50")
    print("全部三个模型（ResNet50 + MobileNetV3 + CBAM）:")
    print("    python -m scripts.train_full")
    print("显存不足时:")
    print("    python -m scripts.train_full --only resnet50 --batch-size 16")
    return 0


if __name__ == "__main__":
    sys.exit(main())
