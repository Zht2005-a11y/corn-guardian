"""真实 HTTP 服务联调脚本（启动 uvicorn 子进程后逐接口验证，最后自动关闭）。

与 scripts/api_test.py 的区别：
    api_test.py 需要手动先启动后端；
    verify_api.py 一键完成"启动 → 逐接口请求 → 关闭"，适合写进 CI 或答辩前一键自检。

用法：
    python -m scripts.verify_api
    python -m scripts.verify_api --port 8010 --weight outputs/checkpoints/best_corn_model.pth
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests  # noqa: E402

from src.config import load_config  # noqa: E402
from src.dataset import collect_samples  # noqa: E402

CHECKS: list[tuple[str, bool]] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    CHECKS.append((name, cond))
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f"  {detail}" if detail else ""))


def wait_ready(base: str, timeout: float = 60.0) -> bool:
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            if requests.get(f"{base}/health", timeout=2).status_code == 200:
                return True
        except requests.RequestException:
            time.sleep(0.5)
    return False


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--port", type=int, default=8010)
    ap.add_argument("--images", nargs="*", default=None, help="测试图片路径；缺省从测试集取各类别一张")
    args = ap.parse_args()

    import subprocess

    base = f"http://127.0.0.1:{args.port}"
    log = ROOT / "outputs" / "logs" / "verify_api_server.log"
    log.parent.mkdir(parents=True, exist_ok=True)
    proc = subprocess.Popen(
        [sys.executable, "-X", "utf8", "-m", "uvicorn", "app.api:app",
         "--host", "127.0.0.1", "--port", str(args.port), "--log-level", "warning"],
        cwd=str(ROOT), stdout=log.open("w", encoding="utf-8"), stderr=subprocess.STDOUT,
    )
    try:
        print(f"启动服务 pid={proc.pid} -> {base}")
        if not wait_ready(base):
            print("服务启动超时，日志见:", log)
            return 1
        print("服务就绪\n")

        img_dir = ROOT / "outputs" / "inference"
        if args.images:
            images = [Path(p) for p in args.images]
        else:
            cfg = load_config()
            _, test_samples, _ = collect_samples(cfg)
            seen, images = set(), []
            for p, label in test_samples:
                if label not in seen:
                    seen.add(label)
                    images.append(Path(p))

        # ---- 基础接口 ----
        r = requests.get(f"{base}/health").json()
        check("GET /health", r["code"] == 0 and r["data"]["status"] == "healthy",
              f"device={r['data']['device']}")
        r = requests.get(f"{base}/models").json()
        check("GET /models", r["code"] == 0 and "resnet50" in r["data"]["models"])
        r = requests.get(f"{base}/dataset/info").json()
        check("GET /dataset/info", r["code"] == 0 and r["data"]["test_total"] > 0,
              f"train={r['data']['train_total']} test={r['data']['test_total']}")
        r = requests.get(f"{base}/knowledge/玉米灰斑病").json()
        check("GET /knowledge/{中文名}", r["code"] == 0 and r["data"]["name_cn"] == "玉米灰斑病")

        # ---- 单图识别 ----
        for p in images:
            t0 = time.perf_counter()
            with open(p, "rb") as f:
                r = requests.post(f"{base}/predict", files={"file": (p.name, f, "image/jpeg")}, timeout=60)
            dt = (time.perf_counter() - t0) * 1000
            ok = r.status_code == 200 and r.json()["code"] == 0
            d = r.json().get("data", {}) if ok else {}
            if ok:
                d_ok = all(k in d for k in ("class_name", "confidence", "confidence_level",
                                            "class_index", "knowledge", "is_valid_leaf"))
            else:
                d_ok = False
            # 随机初始化/弱模型只校验链路；训练好后可用 --expect-acc 校验精度
            check(f"POST /predict {p.name}", ok and d_ok,
                  f"{d.get('class_name')} {d.get('confidence')} ({dt:.0f} ms)")

        # ---- Grad-CAM ----
        with open(images[0], "rb") as f:
            r = requests.post(f"{base}/predict/gradcam", files={"file": (images[0].name, f, "image/jpeg")}, timeout=90)
        g = r.json().get("data", {}).get("gradcam", {}) if r.status_code == 200 else {}
        check("POST /predict/gradcam", bool(g.get("overlay_base64")), f"{len(g.get('overlay_base64', ''))} chars")

        # 保存一张热力图，方便直接放进 PPT
        if g.get("overlay_base64"):
            import base64
            import re

            img_dir.mkdir(parents=True, exist_ok=True)  # 首次运行时目录可能不存在
            safe_stem = re.sub(r"[^\w\-]+", "_", images[0].stem)  # 文件名可能含空格/括号
            out = img_dir / f"gradcam_{safe_stem}.png"
            out.write_bytes(base64.b64decode(g["overlay_base64"]))
            print(f"      Grad-CAM 示例已保存: {out}")

        # ---- 批量 ----
        handles = [open(p, "rb") for p in images]
        try:
            files = [("files", (p.name, fh, "image/jpeg")) for p, fh in zip(images, handles)]
            r = requests.post(f"{base}/predict/batch", files=files, timeout=120)
        finally:
            for fh in handles:
                fh.close()
        bd = r.json().get("data", {})
        check("POST /predict/batch", r.status_code == 200 and
              len(bd.get("results", [])) == len(images),
              f"{bd.get('summary', {}).get('class_counts')}")

        # ---- 多模型对比 ----
        with open(images[0], "rb") as f:
            r = requests.post(f"{base}/predict/compare", files={"file": (images[0].name, f, "image/jpeg")}, timeout=90)
        rs = r.json().get("data", {}).get("results", [])
        check("POST /predict/compare", r.status_code == 200 and len(rs) >= 1,
              "; ".join(f"{x.get('model')}:{x.get('confidence', x.get('error'))}" for x in rs))

        # ---- base64 ----
        import base64

        b64 = base64.b64encode(images[1].read_bytes() if len(images) > 1 else images[0].read_bytes()).decode()
        r = requests.post(f"{base}/predict/base64",
                          json={"image_base64": f"data:image/jpeg;base64,{b64}"}, timeout=60)
        check("POST /predict/base64", r.status_code == 200 and r.json()["code"] == 0)

        # ---- 异常 ----
        r = requests.post(f"{base}/predict", files={"file": ("bad.jpg", b"broken")}, timeout=30)
        check("异常：损坏图片 -> 400", r.status_code == 400 and r.json()["code"] == 400)
        r = requests.get(f"{base}/knowledge/not_exist")
        check("异常：未知知识库 -> 404", r.status_code == 404)
        r = requests.post(f"{base}/predict/batch", files=[], timeout=30)
        check("异常：空批量 -> 422/400", r.status_code in (400, 422))
        r = requests.get(f"{base}/health")
        check("响应头 X-Request-Id", bool(r.headers.get("X-Request-Id")),
              r.headers.get("X-Request-Id", ""))
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()

    failed = [n for n, ok in CHECKS if not ok]
    print(f"\n结果: 通过 {len(CHECKS) - len(failed)}/{len(CHECKS)}")
    if failed:
        print("失败项:", failed)
        return 1
    print("真实 HTTP 联调全部通过！")
    return 0


if __name__ == "__main__":
    sys.exit(main())
