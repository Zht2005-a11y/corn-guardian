"""生成「叶片门控」用的类别特征中心（一次性离线脚本）。

背景：模型是 4 分类软分类器，永远会输出一个病名，无法表达「这不是叶片」。
不重新训练的前提下，最有效的补救是用**特征空间距离**判断输入是否落在已知分布内：
把训练集图片过一遍已训练模型，取 avgpool 后的 2048 维特征，算每类中心，
推理时算输入特征到最近类中心的余弦距离，距离过大即判为非目标图像。

产物：assets/gate/centroids.npz（约 32KB，随仓库提交，避免每次启动重算）
重新生成：python scripts/build_gate_centroids.py --per-class 200
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import numpy as np
from PIL import Image

from src.predictor import get_predictor

CLASSES = ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"]
OUT = ROOT / "assets" / "gate" / "centroids.npz"


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-class", type=int, default=200, help="每类抽样张数（越多越稳，越慢）")
    ap.add_argument("--train-dir", default=str(ROOT.parent.parent / "dataset" / "MCDD" / "data" / "train"))
    ap.add_argument("--out", default=str(OUT))
    args = ap.parse_args()

    train = Path(args.train_dir)
    if not train.exists():
        raise SystemExit(f"训练集目录不存在: {train}")

    predictor = get_predictor()
    key, wrapper = predictor._resolve_model("resnet50_cbam")

    centroids, counts = {}, {}
    for cls in CLASSES:
        d = train / cls
        files = sorted(d.glob("*"))[: args.per_class]
        if not files:
            print(f"  跳过 {cls}（无图片）")
            continue
        feats = []
        for f in files:
            try:
                img = Image.open(f).convert("RGB")
                tensor = wrapper.preprocess(img, None)
                with torch.no_grad():
                    wrapper.logits(tensor.to(wrapper.device))
                feats.append(wrapper._feat.cpu().numpy()[0])
            except Exception as e:  # noqa: BLE001
                print(f"    skip {f.name}: {e}")
        F = np.array(feats, dtype=np.float32)
        F = F / (np.linalg.norm(F, axis=1, keepdims=True) + 1e-8)
        c = F.mean(axis=0)
        c /= np.linalg.norm(c) + 1e-8
        centroids[cls] = c.astype(np.float32)
        counts[cls] = len(F)
        print(f"  {cls:<15} {len(F):>4} 张 -> 中心已算")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    np.savez(out, **centroids)
    print(f"\n已写入 {out}")
    print("各类样本数:", counts)


if __name__ == "__main__":
    import torch  # noqa: F401  （顺序保证：先导入 torch 再调用）
    main()
