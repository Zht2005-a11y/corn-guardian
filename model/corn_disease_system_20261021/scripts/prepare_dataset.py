"""数据集自检脚本：不训练，只统计各数据源 / 各类别图片数量并检查损坏图片。

用法：
    python -m scripts.prepare_dataset
    python -m scripts.prepare_dataset --check-corrupt      # 逐张解码检查（较慢但最可靠）
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import get_class_cn, get_class_names, load_config  # noqa: E402
from src.dataset import collect_samples  # noqa: E402


def check_corrupt(paths, verbose: bool = False):
    from PIL import Image

    bad = []
    for p in paths:
        try:
            with Image.open(p) as im:
                im.verify()
        except Exception as e:
            bad.append((p, str(e)))
            if verbose:
                print(f"[损坏] {p} -> {e}")
    return bad


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--config", default=None)
    ap.add_argument("--check-corrupt", action="store_true")
    args = ap.parse_args()

    cfg = load_config(args.config)
    class_names = get_class_names(cfg)
    train, test, info = collect_samples(cfg)

    print("=" * 70)
    print("数据集自检报告")
    print("=" * 70)
    for s in info["sources"]:
        if "error" in s:
            print(f"[!] {s['name']}: {s['error']}")
            continue
        print(f"[源] {s['name']}  root={s['root']}  use_for_train={s['use_for_train']}")
        print(f"     train={s['train_images']}  test={s['test_images']}  "
              f"跳过的类别={s['skipped_train_classes'] or '无'}")
    print("-" * 70)
    print(f"{'类别索引':<10}{'英文名':<18}{'中文名':<14}{'train':>8}{'test':>8}{'合计':>8}")
    for i, name in enumerate(class_names):
        tr = info["train_distribution"].get(name, 0)
        te = info["test_distribution"].get(name, 0)
        print(f"{i:<10}{name:<18}{get_class_cn(i):<14}{tr:>8}{te:>8}{tr + te:>8}")
    print("-" * 70)
    print(f"训练集合计 {info['train_total']}，测试集合计 {info['test_total']}，"
          f"总计 {info['train_total'] + info['test_total']}")
    print(f"类别索引映射（与 ImageFolder 一致）: { {i: n for i, n in enumerate(class_names)} }")

    if args.check_corrupt:
        all_paths = [p for p, _ in train] + [p for p, _ in test]
        print(f"\n正在检查 {len(all_paths)} 张图片 ...")
        bad = check_corrupt(all_paths)
        print(f"损坏图片 {len(bad)} 张")
        out = ROOT / "outputs" / "reports" / "corrupt_images.txt"
        if bad:
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text("\n".join(f"{p}\t{e}" for p, e in bad), encoding="utf-8")
            print(f"损坏清单已保存: {out}")


if __name__ == "__main__":
    main()
