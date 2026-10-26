"""后端接口冒烟测试：一次性验证健康检查、单图、批量、Grad-CAM、知识库等接口。

前置：后端已启动（uvicorn app.api:app --port 8010）
用法：
    python -m scripts.api_test
    python -m scripts.api_test --base-url http://127.0.0.1:8010 --image path/to/leaf.jpg
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.config import load_config  # noqa: E402
from src.dataset import collect_samples  # noqa: E402


def show(title: str, resp: requests.Response) -> None:
    print(f"\n=== {title} | HTTP {resp.status_code} ===")
    try:
        body = resp.json()
    except ValueError:
        print(resp.text[:500])
        return
    data = body.get("data")
    if isinstance(data, dict):
        # 只打印关键字段，避免 Grad-CAM base64 刷屏
        data = {k: (v if not (isinstance(v, str) and len(v) > 100) else f"<{len(v)} chars>")
                for k, v in data.items()}
    print(json.dumps({"code": body.get("code"), "message": body.get("message"), "data": data},
                     ensure_ascii=False, indent=2)[:1500])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default="http://127.0.0.1:8010")
    ap.add_argument("--image", default=None, help="测试图片；缺省时从测试集自动取 2 张")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    images = []
    if args.image:
        images = [Path(args.image)]
    else:
        cfg = load_config()
        _, test_samples, _ = collect_samples(cfg)
        # 每个类别取一张，便于验证分类结果是否合理
        seen = set()
        for p, label in test_samples:
            if label not in seen:
                seen.add(label)
                images.append(Path(p))
            if len(images) >= 4:
                break
    print(f"测试图片: {[p.name for p in images]}")

    show("健康检查 /health", requests.get(f"{base}/health", timeout=10))
    show("模型列表 /models", requests.get(f"{base}/models", timeout=10))
    show("知识库 /knowledge/Blight", requests.get(f"{base}/knowledge/Blight", timeout=10))

    if images:
        with open(images[0], "rb") as f:
            show("单图识别 /predict", requests.post(f"{base}/predict", files={"file": (images[0].name, f)}, timeout=30))

        with open(images[0], "rb") as f:
            show("Grad-CAM /predict/gradcam",
                 requests.post(f"{base}/predict/gradcam", files={"file": (images[0].name, f)}, timeout=60))

        files = [("files", (p.name, open(p, "rb"))) for p in images]
        try:
            show("批量识别 /predict/batch", requests.post(f"{base}/predict/batch", files=files, timeout=60))
        finally:
            for _, (_, fh) in files:
                fh.close()

        with open(images[0], "rb") as f:
            show("多模型对比 /predict/compare",
                 requests.post(f"{base}/predict/compare", files={"file": (images[0].name, f)}, timeout=60))

        # 异常图片（损坏文件）
        show("异常：损坏图片 /predict",
             requests.post(f"{base}/predict", files={"file": ("bad.jpg", b"not-an-image")}, timeout=20))


if __name__ == "__main__":
    main()
