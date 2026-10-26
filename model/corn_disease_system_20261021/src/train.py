"""玉米病虫害识别 —— 模型训练主脚本（两阶段迁移学习）。

使用方式（在项目根目录 corn_disease_system/ 下执行）：
    python -m src.train                          # 默认按 configs/config.yaml 训练 ResNet50
    python -m src.train --arch mobilenet_v3_large --best-name best_corn_mobilenetv3.pth
    python -m src.train --config configs/config.yaml --epochs-stage2 30
    python -m src.train --balance-sampler        # 类别不均衡时打开（Gray_Leaf_Spot 样本少）
    python -m src.train --resume outputs/checkpoints/best_corn_model.pth

产物（outputs/ 目录）：
    checkpoints/best_corn_model.pth        验证集准确率最高的权重
    checkpoints/last_corn_model.pth        最后一个 epoch 的权重（断点续训用）
    checkpoints/model_meta.json            类别映射、变换参数、训练配置
    logs/train_resnet50_YYYYmmdd_HHMMSS.log
    reports/history_resnet50.json          每个 epoch 的 loss/acc
    reports/curves_resnet50.png            训练曲线图
"""
from __future__ import annotations

import argparse
import json
import logging
import os
import random
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Tuple

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader
from tqdm import tqdm

from .config import PROJECT_ROOT, get_class_names, load_config
from .dataset import (
    build_datasets,
    build_loaders,
    build_weighted_sampler,
    compute_class_weights,
    MergedImageFolder,
)
from .metrics import plot_training_curves, save_json
from .models import (
    build_criterion,
    build_model,
    build_optimizer,
    build_scheduler,
    count_parameters,
    freeze_backbone,
    unfreeze_last_blocks,
)

logger = logging.getLogger("corn.train")


# ==========================================================================
#  工具函数
# ==========================================================================
def set_seed(seed: int) -> None:
    """固定随机种子，保证答辩演示/复现实验时结果一致。"""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = True  # 输入尺寸固定，开启可提速


def setup_logging(save_dir: Path) -> Path:
    """同时输出到控制台与文件。

    注意：必须显式 close() 旧的 FileHandler，否则 Windows 下文件句柄不释放，
    会出现 PermissionError: [WinError 32]（例如同一进程内反复调用训练/测试脚本）。
    """
    log_dir = save_dir.parent / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / f"train_{datetime.now():%Y%m%d_%H%M%S}.log"

    root = logging.getLogger()
    root.setLevel(logging.INFO)
    for h in list(root.handlers):
        root.removeHandler(h)
        try:
            h.close()
        except Exception:
            pass
    fmt = logging.Formatter("%(asctime)s | %(levelname)-7s | %(message)s", "%H:%M:%S")

    # Windows 控制台可能是 GBK，StreamHandler 遇到无法编码的字符会抛异常
    try:
        stream = sys.stdout
        stream.reconfigure(errors="replace")  # type: ignore[attr-defined]
    except Exception:
        stream = sys.stdout
    sh = logging.StreamHandler(stream)
    sh.setFormatter(fmt)
    root.addHandler(sh)
    fh = logging.FileHandler(log_file, encoding="utf-8", mode="a", delay=True)
    fh.setFormatter(fmt)
    root.addHandler(fh)
    return log_file


def shutdown_logging() -> None:
    """关闭并移除所有 handler（释放日志文件句柄，Windows 必备）。"""
    for lg in (logging.getLogger(), logger):
        for h in list(lg.handlers):
            try:
                h.flush()
                h.close()
            except Exception:
                pass
            lg.removeHandler(h)


def get_device(prefer: str = "auto") -> torch.device:
    if prefer == "cpu":
        return torch.device("cpu")
    if torch.cuda.is_available():
        return torch.device("cuda")
    return torch.device("cpu")


# ==========================================================================
#  单个 epoch 的训练 / 验证
# ==========================================================================
def train_one_epoch(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    optimizer: torch.optim.Optimizer,
    device: torch.device,
    scaler: torch.cuda.amp.GradScaler | None,
    epoch_desc: str,
) -> Tuple[float, float]:
    model.train()
    # 阶段一冻结了主干，但主干里仍有 BN 层；保持其统计量不更新，
    # 避免用极少样本估出的均值方差污染预训练特征。
    _set_bn_eval_for_frozen(model)

    total_loss, correct, total = 0.0, 0, 0
    pbar = tqdm(loader, desc=epoch_desc, ncols=100, leave=False)
    for images, labels in pbar:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)

        optimizer.zero_grad(set_to_none=True)
        if scaler is not None:
            with torch.cuda.amp.autocast():
                logits = model(images)
                loss = criterion(logits, labels)
            scaler.scale(loss).backward()
            scaler.unscale_(optimizer)
            nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], max_norm=5.0)
            scaler.step(optimizer)
            scaler.update()
        else:
            logits = model(images)
            loss = criterion(logits, labels)
            loss.backward()
            nn.utils.clip_grad_norm_([p for p in model.parameters() if p.requires_grad], max_norm=5.0)
            optimizer.step()

        bs = images.size(0)
        total_loss += loss.item() * bs
        correct += (logits.argmax(1) == labels).sum().item()
        total += bs
        pbar.set_postfix(loss=f"{total_loss / total:.4f}", acc=f"{correct / total:.4f}")

    return total_loss / max(total, 1), correct / max(total, 1)


@torch.no_grad()
def evaluate(
    model: nn.Module,
    loader: DataLoader,
    criterion: nn.Module,
    device: torch.device,
) -> Tuple[float, float]:
    model.eval()
    total_loss, correct, total = 0.0, 0, 0
    for images, labels in loader:
        images = images.to(device, non_blocking=True)
        labels = labels.to(device, non_blocking=True)
        logits = model(images)
        loss = criterion(logits, labels)
        total_loss += loss.item() * images.size(0)
        correct += (logits.argmax(1) == labels).sum().item()
        total += images.size(0)
    return total_loss / max(total, 1), correct / max(total, 1)


def _set_bn_eval_for_frozen(model: nn.Module) -> None:
    for m in model.modules():
        if isinstance(m, (nn.BatchNorm2d, nn.SyncBatchNorm)):
            # 参数本身不可训练（处于冻结阶段）时使用 running stats
            if not m.weight.requires_grad:
                m.eval()
            else:
                m.train()


# ==========================================================================
#  主训练流程
# ==========================================================================
def main(argv=None) -> None:
    parser = argparse.ArgumentParser(description="玉米病虫害分类模型训练（两阶段迁移学习）")
    parser.add_argument("--config", default=str(PROJECT_ROOT / "configs" / "config.yaml"))
    parser.add_argument("--arch", default=None, help="resnet50 | resnet50_cbam | mobilenet_v3_large")
    parser.add_argument("--data-root", default=None, help="覆盖第一个数据集源的根目录（MCDD/data）")
    parser.add_argument("--epochs-stage1", type=int, default=None)
    parser.add_argument("--epochs-stage2", type=int, default=None)
    parser.add_argument("--batch-size", type=int, default=None)
    parser.add_argument("--lr-stage1", type=float, default=None)
    parser.add_argument("--lr-stage2", type=float, default=None)
    parser.add_argument("--label-smoothing", type=float, default=None)
    parser.add_argument("--use-cbam", action="store_true", help="启用 CBAM 注意力模块")
    parser.add_argument("--balance-sampler", action="store_true", help="加权采样缓解类别不均衡")
    parser.add_argument("--class-weighted-loss", action="store_true", help="加权交叉熵")
    parser.add_argument("--no-pretrained", action="store_true", help="不使用 ImageNet 预训练权重")
    parser.add_argument("--num-workers", type=int, default=None)
    parser.add_argument("--resume", default=None, help="从指定权重继续训练（只恢复模型参数）")
    parser.add_argument("--best-name", default=None, help="最佳权重文件名")
    parser.add_argument("--device", default="auto")
    parser.add_argument("--seed", type=int, default=None)
    args = parser.parse_args(argv)

    # ---------------- 配置合并 ----------------
    cfg = load_config(args.config)
    train_cfg = cfg["train"]
    model_cfg = cfg["model"]

    arch = (args.arch or model_cfg.get("name", "resnet50")).lower()
    if args.use_cbam:
        model_cfg["use_cbam"] = True
        if arch == "resnet50" and "cbam" not in arch:
            arch = "resnet50_cbam"
    image_size = train_cfg.get("image_size", 224)
    epochs1 = args.epochs_stage1 if args.epochs_stage1 is not None else train_cfg["epochs_stage1"]
    epochs2 = args.epochs_stage2 if args.epochs_stage2 is not None else train_cfg["epochs_stage2"]
    bs = args.batch_size or train_cfg["batch_size"]
    lr1 = args.lr_stage1 or train_cfg["lr_stage1"]
    lr2 = args.lr_stage2 or train_cfg["lr_stage2"]
    seed = args.seed or train_cfg.get("seed", 42)
    smoothing = args.label_smoothing if args.label_smoothing is not None else model_cfg.get("label_smoothing", 0.0)
    best_name = args.best_name or train_cfg["best_name"]

    if args.data_root:
        cfg["data"]["sources"][0]["root"] = str(Path(args.data_root).resolve())
    if args.num_workers is not None:
        cfg["data"]["num_workers"] = args.num_workers

    save_dir = Path(train_cfg["save_dir"])
    save_dir.mkdir(parents=True, exist_ok=True)
    log_file = setup_logging(save_dir)
    set_seed(seed)
    device = get_device(args.device)

    logger.info("=" * 78)
    logger.info("玉米病虫害识别模型训练启动")
    logger.info(f"日志文件: {log_file}")
    logger.info(f"设备: {device} | 模型: {arch} | 图像尺寸: {image_size} | batch: {bs} | seed: {seed}")
    logger.info("=" * 78)

    # ---------------- 数据 ----------------
    class_names = get_class_names(cfg)
    logger.info(f"类别索引映射: { {i: n for i, n in enumerate(class_names)} }")
    train_ds, val_ds, test_ds, info = build_datasets(cfg, image_size=image_size, with_verify=True)
    for s in info["sources"]:
        if "error" in s:
            logger.warning(f"[数据源] {s['name']}: {s['error']}")
        else:
            logger.info(
                f"[数据源] {s['name']}: train={s['train_images']} test={s['test_images']} "
                f"use_for_train={s['use_for_train']} skipped={s['skipped_train_classes']}"
            )
    logger.info(f"[划分结果] train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}")
    logger.info(f"[分布] train={info['final']['train_distribution']}")
    logger.info(f"[分布] test ={info['final']['test_distribution']}")
    save_json(info, save_dir.parent / "reports" / f"dataset_info_{arch}.json")

    train_loader, val_loader, _ = build_loaders(train_ds, val_ds, test_ds, cfg,
                                                balance_sampler=args.balance_sampler)
    if args.balance_sampler:
        logger.info("已启用 WeightedRandomSampler（类别均衡采样）")

    # ---------------- 模型 ----------------
    model = build_model(
        arch=arch,
        num_classes=len(class_names),
        pretrained=not args.no_pretrained,
        dropout=model_cfg.get("dropout", 0.3),
        use_cbam=model_cfg.get("use_cbam", False),
    ).to(device)

    if args.resume and Path(args.resume).exists():
        ckpt = torch.load(args.resume, map_location=device)
        state = ckpt.get("model_state_dict", ckpt)
        model.load_state_dict(state, strict=False)
        logger.info(f"已从 {args.resume} 恢复模型参数（直接进入阶段二）")
        epochs1 = 0

    # ---------------- 损失函数 ----------------
    class_weights = None
    if args.class_weighted_loss or model_cfg.get("class_weighted_loss", False):
        class_weights = compute_class_weights(train_ds, len(class_names))  # type: ignore[arg-type]
        logger.info(f"类别权重: {class_weights.tolist()}")
    criterion = build_criterion(smoothing, class_weights, device)
    logger.info(f"损失函数: CrossEntropy(label_smoothing={smoothing}, weighted={class_weights is not None})")

    # 验证用不带标签平滑的损失，便于比较真实收敛程度
    val_criterion = build_criterion(0.0, None, device)

    history = []
    best_val_acc = 0.0
    best_epoch = 0
    use_amp = bool(train_cfg.get("amp", True)) and device.type == "cuda"

    # ======================= 阶段一：只训练分类头 =======================
    if epochs1 > 0:
        freeze_backbone(model, arch)
        params = count_parameters(model)
        logger.info("-" * 78)
        logger.info(f"阶段一：冻结骨干网络，仅训练分类头 | 可训练参数 {params['trainable']:,} / {params['total']:,}")
        logger.info("-" * 78)

        optimizer = build_optimizer(model, lr1, train_cfg["weight_decay"])
        scheduler = build_scheduler(optimizer, epochs1, 0, train_cfg.get("cosine_eta_min", 1e-6))
        scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

        for epoch in range(1, epochs1 + 1):
            t0 = time.time()
            tr_loss, tr_acc = train_one_epoch(
                model, train_loader, criterion, optimizer, device, scaler, f"[阶段1] Epoch {epoch}/{epochs1}"
            )
            val_loss, val_acc = evaluate(model, val_loader, val_criterion, device)
            lr_now = optimizer.param_groups[0]["lr"]
            scheduler.step()

            history.append(dict(epoch=epoch, stage=1, train_loss=tr_loss, train_acc=tr_acc,
                                val_loss=val_loss, val_acc=val_acc, lr=lr_now))
            logger.info(
                f"[阶段1][{epoch}/{epochs1}] train_loss={tr_loss:.4f} train_acc={tr_acc:.4f} | "
                f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | lr={lr_now:.2e} | {time.time()-t0:.1f}s"
            )
            if val_acc > best_val_acc:
                best_val_acc, best_epoch = val_acc, epoch
                _save_checkpoint(model, save_dir / best_name, arch, class_names, image_size, cfg, epoch, val_acc, stage=1)
                logger.info(f"  -> 新的最佳验证准确率 {val_acc:.4f}，已保存 {best_name}")

    # ======================= 阶段二：解冻 layer3/4 微调 =======================
    if epochs2 > 0:
        unfrozen = unfreeze_last_blocks(model, arch, train_cfg.get("freeze_until", "layer2"))
        params = count_parameters(model)
        logger.info("-" * 78)
        logger.info(f"阶段二：解冻 {unfrozen} | 可训练参数 {params['trainable']:,} / {params['total']:,}")
        logger.info("-" * 78)

        optimizer = build_optimizer(model, lr2, train_cfg["weight_decay"])
        scheduler = build_scheduler(
            optimizer, epochs2, train_cfg.get("warmup_epochs", 1), train_cfg.get("cosine_eta_min", 1e-6)
        )
        scaler = torch.cuda.amp.GradScaler(enabled=use_amp)

        for epoch in range(1, epochs2 + 1):
            t0 = time.time()
            tr_loss, tr_acc = train_one_epoch(
                model, train_loader, criterion, optimizer, device, scaler, f"[阶段2] Epoch {epoch}/{epochs2}"
            )
            val_loss, val_acc = evaluate(model, val_loader, val_criterion, device)
            lr_now = optimizer.param_groups[0]["lr"]
            scheduler.step()

            global_epoch = epochs1 + epoch
            history.append(dict(epoch=global_epoch, stage=2, train_loss=tr_loss, train_acc=tr_acc,
                                val_loss=val_loss, val_acc=val_acc, lr=lr_now))
            logger.info(
                f"[阶段2][{epoch}/{epochs2}] train_loss={tr_loss:.4f} train_acc={tr_acc:.4f} | "
                f"val_loss={val_loss:.4f} val_acc={val_acc:.4f} | lr={lr_now:.2e} | {time.time()-t0:.1f}s"
            )
            if val_acc > best_val_acc:
                best_val_acc, best_epoch = val_acc, global_epoch
                _save_checkpoint(model, save_dir / best_name, arch, class_names, image_size, cfg, global_epoch, val_acc, stage=2)
                logger.info(f"  -> 新的最佳验证准确率 {val_acc:.4f}，已保存 {best_name}")
        _save_checkpoint(model, save_dir / f"last_{arch}.pth", arch, class_names, image_size, cfg,
                         epochs1 + epochs2, best_val_acc, stage=2)

    # ---------------- 产物 ----------------
    reports_dir = save_dir.parent / "reports"
    save_json(history, reports_dir / f"history_{arch}.json")
    if history:
        plot_training_curves(history, reports_dir / f"curves_{arch}.png")
    logger.info("=" * 78)
    logger.info(f"训练完成 | 最佳验证准确率 {best_val_acc:.4f} @ epoch {best_epoch}")
    logger.info(f"最佳权重: {save_dir / best_name}")
    logger.info(f"下一步: python -m src.evaluate --weight {save_dir / best_name} --arch {arch}")
    logger.info("=" * 78)
    shutdown_logging()  # 释放日志文件句柄，便于后续删除/重复训练


def _save_checkpoint(
    model: nn.Module,
    path: Path,
    arch: str,
    class_names,
    image_size: int,
    cfg: Dict,
    epoch: int,
    val_acc: float,
    stage: int,
) -> None:
    """保存"可自描述"的权重文件：推理时无需再看配置文件即可加载正确结构。"""
    torch.save(
        {
            "model_state_dict": model.state_dict(),
            "arch": arch,
            "num_classes": len(class_names),
            "class_names": list(class_names),
            "image_size": image_size,
            "val_acc": float(val_acc),
            "epoch": epoch,
            "stage": stage,
            "use_cbam": bool(cfg.get("model", {}).get("use_cbam", False)) or "cbam" in arch,
            "saved_at": datetime.now().isoformat(timespec="seconds"),
        },
        path,
    )


if __name__ == "__main__":
    os.environ.setdefault("OMP_NUM_THREADS", "4")
    main()
