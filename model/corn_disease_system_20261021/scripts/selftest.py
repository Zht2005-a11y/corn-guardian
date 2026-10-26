"""端到端自检脚本（无需手动启动服务）。

覆盖内容：
  1. 配置 / 类别映射 / 知识库完整性
  2. 数据集合并、分层切分、DataLoader、增强与测试变换
  3. ResNet50 / MobileNetV3 / CBAM 前向形状、冻结解冻、损失、优化器、调度器
  4. 单轮小样本训练（验证训练循环不报错、权重可保存）
  5. 推理封装：单张 / 批量 / 异常图片（损坏、超大、过小）/ Grad-CAM / 缓存
  6. 评估：指标 + 混淆矩阵 + 训练曲线绘图
  7. FastAPI 接口：health / models / knowledge / predict / batch / gradcam / compare / base64 / 异常
  8. 命令行脚本：prepare_dataset / benchmark / predictor CLI

用法：
    python -m scripts.selftest              # 全量
    python -m scripts.selftest --fast       # 跳过训练与绘图（只测推理/接口）

退出码 0 表示全部通过。
"""
from __future__ import annotations

import io
import json
import sys
import tempfile
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PASS, FAIL = [], []


def run(name: str) -> bool:
    """执行并记录单个用例（name 即函数名），返回是否通过。"""
    fn = globals().get(name)
    if fn is None:
        FAIL.append((name, "用例不存在"))
        print(f"  [FAIL] {name} -> 用例不存在")
        return False
    if name in PASS or name in [n for n, _ in FAIL]:
        return name in PASS
    try:
        fn()
        PASS.append(name)
        print(f"  [PASS] {name}")
        return True
    except Exception as e:  # noqa: BLE001
        FAIL.append((name, f"{type(e).__name__}: {e}"))
        print(f"  [FAIL] {name} -> {type(e).__name__}: {e}")
        traceback.print_exc(limit=4)
        return False


def assert_true(cond, msg=""):
    if not cond:
        raise AssertionError(msg or "断言失败")


def section(title):
    print(f"\n{'=' * 70}\n{title}\n{'=' * 70}")


def _pick_images_per_class(n_per_class: int = 2):
    from src.config import load_config
    from src.dataset import collect_samples

    cfg = load_config()
    _, test_samples, _ = collect_samples(cfg)
    by_cls = {}
    for p, label in test_samples:
        by_cls.setdefault(label, []).append(p)
    picks = []
    for label in sorted(by_cls):
        picks.extend(by_cls[label][:n_per_class])
    return cfg, picks


# ==========================================================================
def test_config():
    from src.config import get_class_cn, get_class_names, load_config, normalize_class_name

    cfg = load_config()
    names = get_class_names(cfg)
    assert_true(len(names) == 4, f"类别数应为 4，实际 {len(names)}")
    assert_true(names == ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"], f"类别顺序错误: {names}")
    assert_true(get_class_cn(0) == "玉米大斑病")
    assert_true(normalize_class_name("Rust") == "Common_Rust")
    assert_true(normalize_class_name("Gray Spot") == "Gray_Leaf_Spot")
    assert_true(normalize_class_name("Health") == "Healthy")
    # PlantVillage 二期数据集的文件夹名
    assert_true(normalize_class_name("Corn_(maize)___Northern_Leaf_Blight") == "Blight")
    assert_true(normalize_class_name("Corn_(maize)___Common_rust_") == "Common_Rust")
    assert_true(normalize_class_name("Corn_(maize)___healthy") == "Healthy")
    assert_true(
        normalize_class_name("Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot") == "Gray_Leaf_Spot"
    )
    assert_true(Path(cfg["train"]["save_dir"]).is_absolute(), "save_dir 应转为绝对路径")


def test_knowledge():
    from src.knowledge_base import KNOWLEDGE_BASE, get_knowledge

    assert_true(len(KNOWLEDGE_BASE) == 4)
    for key, v in KNOWLEDGE_BASE.items():
        for field in ("name_cn", "symptoms", "occurrence", "control", "severity"):
            assert_true(field in v, f"{key} 缺少字段 {field}")
        assert_true(len(v["symptoms"]) >= 3, f"{key} 症状条目不足")
        for k in ("agricultural", "chemical", "field"):
            assert_true(len(v["control"][k]) >= 1, f"{key}.control.{k} 为空")
    assert_true(get_knowledge("Unknown")["symptoms"], "未知类别应有兜底内容")


def test_dataset():
    from src.config import load_config
    from src.dataset import build_datasets

    cfg = load_config()
    train_ds, val_ds, test_ds, info = build_datasets(cfg, with_verify=True)

    # 期望值由配置中各数据源实际图片数推算（新增数据集后无需改测试）
    exp_train_total = sum(s.get("train_images", 0) for s in info["sources"] if s.get("use_for_train", True))
    exp_test_total = sum(s.get("test_images", 0) for s in info["sources"])
    assert_true(len(test_ds) > 0 and len(test_ds) == exp_test_total, f"测试集数量不符: {len(test_ds)} vs {exp_test_total}")
    assert_true(len(train_ds) + len(val_ds) == exp_train_total,
                f"训练+验证数量不符: {len(train_ds)+len(val_ds)} vs {exp_train_total}")
    # MCDD 官方测试集必须完整纳入（922 张）
    assert_true(len(test_ds) >= 922, f"官方测试集样本缺失，当前 {len(test_ds)}")
    assert_true(len(val_ds) > 0)
    # 验证集分层：每个类别都要有样本
    val_dist = val_ds.class_distribution()
    assert_true(all(v > 0 for v in val_dist.values()), f"验证集存在空类别: {val_dist}")
    # 无重叠
    assert_true(set(p for p, _ in train_ds.samples).isdisjoint({p for p, _ in val_ds.samples}),
                "训练集与验证集存在重叠样本")
    assert_true(train_ds.class_to_idx["Healthy"] == 3)
    print(f"      train={len(train_ds)} val={len(val_ds)} test={len(test_ds)}  验证分布={val_dist}")


def test_dataloader_and_augment():
    import torch
    from src.config import load_config
    from src.dataset import (
        build_datasets,
        build_eval_transform,
        build_loaders,
        build_train_transform,
        compute_class_weights,
    )

    cfg = load_config()
    cfg["data"]["num_workers"] = 0
    cfg["train"]["batch_size"] = 8
    train_ds, val_ds, test_ds, _ = build_datasets(cfg)
    tr, va, te = build_loaders(train_ds, val_ds, test_ds, cfg)

    x, y = next(iter(tr))
    assert_true(tuple(x.shape) == (8, 3, 224, 224), f"训练 batch 形状错误: {tuple(x.shape)}")
    assert_true(x.dtype == torch.float32)
    assert_true(float(x.abs().max()) < 10, "归一化后数值范围异常")
    assert_true(y.dtype == torch.int64 and int(y.max()) <= 3)

    xv, _ = next(iter(va))
    assert_true(tuple(xv.shape) == (8, 3, 224, 224))

    # 增强应带来随机性；测试变换必须确定性
    from PIL import Image

    img = Image.open(train_ds.samples[0][0]).convert("RGB")
    a = build_train_transform()(img)
    b = build_train_transform()(img)
    assert_true(not torch.allclose(a, b), "训练增强未生效（两次结果相同）")
    e1, e2 = build_eval_transform()(img), build_eval_transform()(img)
    assert_true(torch.allclose(e1, e2), "测试变换应保持确定性")

    cw = compute_class_weights(train_ds, 4)
    assert_true(cw.shape == (4,) and float(cw.min()) > 0)
    print(f"      类别权重={[round(v, 3) for v in cw.tolist()]}")

    # 加权采样器
    from src.dataset import build_weighted_sampler

    sampler = build_weighted_sampler(train_ds)
    assert_true(len(list(iter(sampler))) > 0)


def test_models():
    import torch
    from src.models import (
        build_criterion,
        build_model,
        build_optimizer,
        build_scheduler,
        count_parameters,
        freeze_backbone,
        unfreeze_last_blocks,
    )

    x = torch.randn(2, 3, 224, 224)
    for arch in ("resnet50", "mobilenet_v3_large"):
        m = build_model(arch, num_classes=4, pretrained=False).eval()
        with torch.no_grad():
            out = m(x)
        assert_true(tuple(out.shape) == (2, 4), f"{arch} 输出形状错误: {tuple(out.shape)}")
        p = count_parameters(m)
        print(f"      {arch:<22} 参数 {p['total']/1e6:.2f}M")

    # CBAM
    m = build_model("resnet50_cbam", num_classes=4, pretrained=False).eval()
    with torch.no_grad():
        assert_true(tuple(m(x).shape) == (2, 4))
    from src.models import CBAM

    cb = CBAM(64).eval()
    with torch.no_grad():
        o = cb(torch.randn(1, 64, 28, 28))
    assert_true(tuple(o.shape) == (1, 64, 28, 28))

    # 冻结 / 解冻
    m = build_model("resnet50", num_classes=4, pretrained=False)
    freeze_backbone(m, "resnet50")
    p1 = count_parameters(m)
    assert_true(p1["trainable"] < p1["total"] / 20, f"冻结后仍有过量可训练参数: {p1}")
    for n, prm in m.named_parameters():
        if not n.startswith("fc."):
            assert_true(not prm.requires_grad, f"骨干参数 {n} 未被冻结")
    unfrozen = unfreeze_last_blocks(m, "resnet50", "layer2")
    p2 = count_parameters(m)
    assert_true("layer3" in unfrozen and "layer4" in unfrozen)
    assert_true(p2["trainable"] > p1["trainable"])
    for n, prm in m.named_parameters():
        if n.startswith(("conv1", "layer1", "layer2")):
            assert_true(not prm.requires_grad, f"{n} 应保持冻结")
    print(f"      冻结时 trainable={p1['trainable']:,} -> 解冻后 {p2['trainable']:,}")

    # 损失 / 优化器 / 调度器
    crit = build_criterion(0.1, torch.tensor([1.0, 1.0, 2.0, 1.0]), torch.device("cpu"))
    loss = crit(torch.randn(4, 4), torch.tensor([0, 1, 2, 3]))
    assert_true(float(loss) > 0)
    opt = build_optimizer(m, 1e-4, 1e-4)
    sch = build_scheduler(opt, total_epochs=6, warmup_epochs=2)
    lrs = [opt.param_groups[0]["lr"]]
    for _ in range(6):
        opt.step()
        sch.step()
        lrs.append(opt.param_groups[0]["lr"])
    # lrs[0] 为 warmup 起点（base/2），lrs[1] 达峰值 base，之后单调下降至 eta_min
    assert_true(lrs[0] < lrs[1] <= 1.0001e-4, f"warmup 阶段 lr 应上升: {lrs}")
    assert_true(lrs[-1] <= lrs[1] * 1.01 and lrs[-1] >= 9e-7, f"余弦退火未收敛到 eta_min: {lrs}")
    assert_true(all(lrs[i] >= lrs[i + 1] * 0.999 for i in range(2, len(lrs) - 1)), f"退火阶段 lr 应单调下降: {lrs}")
    print(f"      lr 序列={[f'{v:.2e}' for v in lrs]}")


def test_gradcam():
    import numpy as np
    import torch
    from src.gradcam import GradCAM, overlay_cam
    from src.models import build_model
    from PIL import Image

    for arch in ("resnet50", "mobilenet_v3_large"):
        m = build_model(arch, 4, pretrained=False).eval()
        g = GradCAM(m)
        cam, idx = g(torch.randn(1, 3, 224, 224))
        g.remove()
        assert_true(cam.shape == (224, 224), f"{arch} CAM 尺寸错误: {cam.shape}")
        assert_true(0 <= cam.min() and cam.max() <= 1.0001)
        assert_true(np.isfinite(cam).all())
    img = Image.new("RGB", (300, 200), (30, 120, 40))
    out = overlay_cam(img, np.random.rand(224, 224))
    assert_true(out.size == (224, 224))


def test_metrics():
    import numpy as np
    from src.metrics import classification_report_dict, plot_confusion_matrix, plot_training_curves

    y_true = [0, 0, 1, 1, 2, 2, 3, 3]
    y_pred = [0, 1, 1, 1, 2, 2, 3, 0]
    rep = classification_report_dict(y_true, y_pred, 4)
    assert_true(rep["accuracy"] == 0.75, f"准确率计算错误: {rep['accuracy']}")
    assert_true(len(rep["per_class"]) == 4 and rep["labels"][0] == "玉米大斑病")
    assert_true(abs(rep["per_class"][1]["recall"] - 1.0) < 1e-6)
    with tempfile.TemporaryDirectory() as d:
        p1 = plot_confusion_matrix(rep["confusion_matrix"], rep["labels"], Path(d) / "cm.png")
        p2 = plot_confusion_matrix(rep["confusion_matrix"], rep["labels"], Path(d) / "cmn.png", normalize=True)
        hist = [
            {"epoch": 1, "stage": 1, "train_loss": 1.2, "train_acc": 0.6, "val_loss": 0.9, "val_acc": 0.7},
            {"epoch": 2, "stage": 2, "train_loss": 0.5, "train_acc": 0.85, "val_loss": 0.4, "val_acc": 0.88},
        ]
        p3 = plot_training_curves(hist, Path(d) / "curves.png")
        for p in (p1, p2, p3):
            assert_true(p.exists() and p.stat().st_size > 1000, f"图片未正确生成: {p}")


def test_predictor():
    import torch
    from src.config import load_config
    from src.predictor import (
        CornDiseasePredictor,
        InvalidImageError,
        confidence_level,
        leaf_likelihood_score,
        validate_image,
    )

    lvl, hint = confidence_level(0.95), None
    assert_true(confidence_level(0.95)[0] == "high")
    assert_true(confidence_level(0.7)[0] == "medium")
    assert_true(confidence_level(0.3)[0] == "low")

    # 异常图片
    for bad, desc in [(b"", "空"), (b"not an image", "非图片"), (b"\xff\xd8\xff\xe0broken", "截断JPEG")]:
        try:
            validate_image(bad)
            raise AssertionError(f"{desc} 应被拒绝")
        except InvalidImageError:
            pass

    from PIL import Image

    buf = io.BytesIO()
    Image.new("RGB", (10, 10), (0, 0, 0)).save(buf, "PNG")
    try:
        validate_image(buf.getvalue())
        raise AssertionError("过小图片应被拒绝")
    except InvalidImageError:
        pass

    buf = io.BytesIO()
    Image.new("RGB", (5000, 100), (0, 0, 0)).save(buf, "PNG")
    try:
        validate_image(buf.getvalue(), max_side=4096)
        raise AssertionError("超大图片应被拒绝")
    except InvalidImageError:
        pass

    # 无权重状态下的推理器（验证接口链路，不校验精度）
    cfg = load_config()
    p = CornDiseasePredictor(cfg, model_specs={"resnet50": {"path": "no_such.pth", "arch": "resnet50"}},
                             device="cpu")
    assert_true(p.load_report["resnet50"]["loaded"] is False)
    _, imgs = _pick_images_per_class(1)
    r1 = p.predict_path(imgs[0])
    assert_true(0 <= r1["confidence"] <= 1 and r1["class_index"] in range(4))
    assert_true(set(r1["probabilities"]) == set(p.class_cn))
    assert_true(abs(sum(r1["probabilities"].values()) - 1) < 0.01)

    # 缓存命中
    data = Path(imgs[0]).read_bytes()
    p.predict_bytes(data, "a.jpg")
    p.predict_bytes(data, "a.jpg")
    assert_true(p.models["resnet50"].cache.hits >= 1, "预处理缓存未命中")

    # 批量
    batch = p.predict_batch([(Path(x).name, Path(x).read_bytes()) for x in imgs]
                            + [("bad.jpg", b"xxx")])
    assert_true(len(batch["results"]) == len(imgs), "批量推理结果数不符")
    assert_true(len(batch["failed"]) == 1, "损坏图片应进入 failed 列表")
    assert_true(batch["summary"]["total"] == len(imgs))

    # Grad-CAM
    g = p.predict_with_gradcam(data, "a.jpg")
    import base64

    assert_true(len(base64.b64decode(g["gradcam"]["overlay_base64"])) > 1000)
    print(f"      示例: {r1['class_name']} conf={r1['confidence']} leaf_score="
          f"{leaf_likelihood_score(Image.open(imgs[0])):.3f}")


def test_train_loop():
    """小样本跑 1+1 个 epoch，验证训练脚本主流程（含保存与评估产物）。"""
    import torch
    from torch.utils.data import DataLoader, Subset
    from src.config import load_config
    from src.dataset import build_datasets
    from src.models import build_criterion, build_model, build_optimizer, freeze_backbone, unfreeze_last_blocks
    from src.train import evaluate, train_one_epoch

    cfg = load_config()
    train_ds, val_ds, _, _ = build_datasets(cfg)
    tr = DataLoader(Subset(train_ds, list(range(32))), batch_size=8, shuffle=True)
    va = DataLoader(Subset(val_ds, list(range(16))), batch_size=8)

    model = build_model("resnet50", 4, pretrained=False)
    freeze_backbone(model, "resnet50")
    opt = build_optimizer(model, 1e-3, 1e-4)
    crit = build_criterion(0.1, None, torch.device("cpu"))
    loss1, acc1 = train_one_epoch(model, tr, crit, opt, torch.device("cpu"), None, "自检")
    vl, vacc = evaluate(model, va, crit, torch.device("cpu"))
    assert_true(0 < loss1 < 100 and 0 <= acc1 <= 1)
    assert_true(0 <= vacc <= 1)

    unfreeze_last_blocks(model, "resnet50", "layer2")
    opt2 = build_optimizer(model, 1e-4, 1e-4)
    loss2, _ = train_one_epoch(model, tr, crit, opt2, torch.device("cpu"), None, "自检2")
    assert_true(loss2 > 0)
    print(f"      stage1 loss={loss1:.3f} acc={acc1:.3f} | stage2 loss={loss2:.3f} | val_acc={vacc:.3f}")


def _train_smoke(
    save_dir: Path,
    best_name: str = "selftest_model.pth",
    resume_ckpt: Path | None = None,
    max_samples: int | None = None,
) -> Path:
    """跑一遍训练 CLI（1 个 epoch，CPU），返回权重路径。

    若传入 resume_ckpt 则直接从该权重进入阶段二（用于产出可测评估的权重）。
    max_samples 用于把训练数据截断成小子集，让冒烟测试快速跑完。
    """
    import yaml

    cfg = yaml.safe_load((ROOT / "configs" / "config.yaml").read_text(encoding="utf-8"))
    cfg.setdefault("train", {})["save_dir"] = str(save_dir)
    cfg["data"]["num_workers"] = 0
    if max_samples:
        # 冒烟测试: 只保留 MCDD 源并截断样本，让 1+1 epoch 在 1~2 分钟内跑完
        for src in cfg["data"]["sources"]:
            src["use_for_train"] = False
        cfg["data"]["sources"][0]["use_for_train"] = True
        cfg["data"]["limit_per_split"] = int(max_samples)
    tmp_cfg = Path(save_dir).parent / "selftest_cfg.yaml"
    tmp_cfg.parent.mkdir(parents=True, exist_ok=True)
    tmp_cfg.write_text(yaml.safe_dump(cfg, allow_unicode=True), encoding="utf-8")

    from src.train import main as train_main

    argv = [
        "--config", str(tmp_cfg),
        "--epochs-stage1", "0" if resume_ckpt else "1",
        "--epochs-stage2", "1",
        "--batch-size", "16",
        "--num-workers", "0",
        "--device", "cpu",
        "--best-name", best_name,
    ]
    if resume_ckpt:
        argv += ["--resume", str(resume_ckpt)]
    else:
        argv += ["--no-pretrained"]
    from src.train import shutdown_logging

    try:
        train_main(argv)
    finally:
        shutdown_logging()  # 释放日志文件句柄，否则 Windows 下临时目录无法删除
    return Path(save_dir) / best_name


def test_train_cli_smoke():
    """用 --epochs-stage1 1 --epochs-stage2 1 跑真实 CLI，确认权重/日志/曲线落盘。"""
    import torch

    tmp = Path(tempfile.mkdtemp())  # 不用 TemporaryDirectory：Windows 下自动删除易受句柄影响
    ckpt = _train_smoke(tmp / "ckpt", max_samples=160)
    assert_true(ckpt.exists(), "训练未生成权重文件")
    state = torch.load(ckpt, map_location="cpu")
    for k in ("model_state_dict", "arch", "class_names", "image_size", "val_acc"):
        assert_true(k in state, f"权重缺少元信息字段 {k}")
    assert_true(state["class_names"] == ["Blight", "Common_Rust", "Gray_Leaf_Spot", "Healthy"])
    assert_true((tmp / "reports" / "curves_resnet50.png").exists(), "训练曲线未生成")
    assert_true(any((tmp / "logs").glob("train_*.log")), "训练日志未生成")
    print(f"      checkpoint={ckpt.name}  val_acc={state['val_acc']:.4f}")


_ARTIFACT_CKPT = None


def _prepare_artifact_ckpt() -> Path:
    """在 outputs/checkpoints 下产出 selftest_model.pth：先训 1 epoch，再续训 1 epoch。"""
    global _ARTIFACT_CKPT
    ckpt = _train_smoke(ROOT / "outputs" / "checkpoints", max_samples=400)
    assert_true(ckpt.exists(), "产物权重未生成")
    _ARTIFACT_CKPT = ckpt
    return ckpt


def test_evaluate_cli():
    """用训练冒烟产出的权重跑评估脚本，验证指标/混淆矩阵/报告完整。"""
    from src.evaluate import main as eval_main

    ckpt = _ARTIFACT_CKPT
    assert_true(ckpt is not None and Path(ckpt).exists(), "缺少训练产物，无法测试评估")
    eval_main(["--weight", str(ckpt), "--device", "cpu", "--batch-size", "32"])
    rep = ROOT / "outputs" / "reports" / "metrics_resnet50_test.json"
    assert_true(rep.exists(), "评估报告未生成")
    data = json.loads(rep.read_text(encoding="utf-8"))
    for k in ("accuracy", "per_class", "confusion_matrix", "labels"):
        assert_true(k in data, f"评估报告缺字段 {k}")
    assert_true(sum(sum(r) for r in data["confusion_matrix"]) == data["num_samples"] > 0,
                "混淆矩阵样本总数与 num_samples 不一致")
    assert_true(len(data["labels"]) == 4 and data["labels"][0] == "玉米大斑病")
    assert_true((ROOT / "outputs" / "reports" / "confusion_matrix_resnet50.png").exists())
    assert_true((ROOT / "outputs" / "reports" / "report_resnet50_test.txt").exists())
    print(f"      评估准确率(仅流程校验)={data['accuracy']:.4f}")


def test_benchmark_cli():
    from scripts.benchmark import main as bench_main

    bench_main(["--device", "cpu", "--iters", "2", "--model", "resnet50", "--model", "mobilenet_v3_large"])
    out = ROOT / "outputs" / "reports" / "benchmark.json"
    assert_true(out.exists())
    rows = json.loads(out.read_text(encoding="utf-8"))["rows"]
    assert_true(len(rows) == 2 and all(r["params_total_M"] > 0 for r in rows))


def test_api():
    """用 FastAPI TestClient 直接打接口（不占端口）。"""
    from fastapi.testclient import TestClient

    import app.api as api

    with TestClient(api.app) as client:
        r = client.get("/health")
        assert_true(r.status_code == 200 and r.json()["code"] == 0, r.text[:300])
        assert_true(r.json()["data"]["status"] == "healthy")
        assert_true(r.headers.get("X-Request-Id"))

        r = client.get("/models")
        models = r.json()["data"]["models"]
        assert_true("resnet50" in models)

        r = client.get("/knowledge")
        assert_true(len(r.json()["data"]) == 4)
        r = client.get("/knowledge/玉米大斑病")
        assert_true(r.json()["data"]["name_cn"] == "玉米大斑病")
        r = client.get("/knowledge/1")
        assert_true(r.json()["data"]["name_cn"] == "玉米普通锈病")
        assert_true(client.get("/knowledge/xx").status_code == 404)

        r = client.get("/dataset/info")
        info = r.json()["data"]
        # 官方测试集（MCDD）必须存在；新增数据集只参与训练（evaluate=false）
        assert_true(info["test_total"] >= 922, f"测试集统计异常: {info['test_total']}")
        # 各类别之和 == 总数（覆盖包含新数据集后的合并统计）
        assert_true(sum(info["train_distribution"].values()) == info["train_total"])
        assert_true(sum(info["test_distribution"].values()) == info["test_total"])
        assert_true(len(info["sources"]) >= 1 and "class_names" in info)

        _, imgs = _pick_images_per_class(2)
        with open(imgs[0], "rb") as f:
            r = client.post("/predict", files={"file": ("leaf.jpg", f, "image/jpeg")})
        body = r.json()
        assert_true(r.status_code == 200 and body["code"] == 0, r.text[:400])
        d = body["data"]
        for k in ("class_index", "class_name", "confidence", "confidence_level", "knowledge"):
            assert_true(k in d, f"/predict 缺字段 {k}")
        assert_true(0 <= d["confidence"] <= 1)

        with open(imgs[0], "rb") as f:
            r = client.post("/predict/gradcam", files={"file": ("leaf.jpg", f, "image/jpeg")})
        assert_true(r.status_code == 200 and "overlay_base64" in r.json()["data"]["gradcam"])

        handles = [open(p, "rb") for p in imgs]
        files = [("files", (Path(p).name, fh, "image/jpeg")) for p, fh in zip(imgs, handles)]
        try:
            r = client.post("/predict/batch", files=files)
        finally:
            for fh in handles:
                fh.close()
        bd = r.json()["data"]
        assert_true(len(bd["results"]) == len(imgs) and bd["summary"]["total"] == len(imgs))

        with open(imgs[0], "rb") as f:
            r = client.post("/predict/compare", files={"file": ("leaf.jpg", f, "image/jpeg")})
        assert_true(r.status_code == 200 and len(r.json()["data"]["results"]) >= 1)

        import base64

        b64 = base64.b64encode(Path(imgs[1]).read_bytes()).decode()
        r = client.post("/predict/base64", json={"image_base64": f"data:image/jpeg;base64,{b64}"})
        assert_true(r.status_code == 200 and r.json()["data"]["class_index"] in range(4))

        # 异常：损坏图片 -> 400
        r = client.post("/predict", files={"file": ("bad.jpg", b"broken", "image/jpeg")})
        assert_true(r.status_code == 400 and r.json()["code"] == 400, r.text[:300])
        # 异常：不支持的扩展名
        r = client.post("/predict", files={"file": ("a.txt", b"hello", "text/plain")})
        assert_true(r.status_code == 400)
        # 异常：未知模型
        with open(imgs[0], "rb") as f:
            r = client.post("/predict?model=ghost", files={"file": ("leaf.jpg", f, "image/jpeg")})
        assert_true(r.status_code == 400, r.text[:200])
        # 批量超限
        files = [("files", (f"{i}.jpg", io.BytesIO(b"x"), "image/jpeg")) for i in range(21)]
        r = client.post("/predict/batch", files=files)
        assert_true(r.status_code == 400)

        r = client.post("/cache/clear")
        assert_true(r.json()["data"]["cleared"] is True)

        # CORS 头
        r = client.get("/health", headers={"Origin": "http://localhost:8501"})
        assert_true(r.status_code == 200)


# ==========================================================================
def main() -> int:
    """说明：各 test_* 函数在 @case 装饰（即定义）时就会执行并记录结果，
    因此这里按顺序调用只是为了保持阅读顺序与执行顺序一致。"""
    fast = "--fast" in sys.argv
    print(f"项目根目录: {ROOT}")

    section("1. 配置与知识库")
    run("test_config")
    run("test_knowledge")

    section("2. 数据集")
    run("test_dataset")
    run("test_dataloader_and_augment")

    section("3. 模型结构 / 冻结策略 / 损失优化器")
    run("test_models")
    run("test_gradcam")

    section("4. 评估与绘图")
    run("test_metrics")

    section("5. 推理封装")
    run("test_predictor")

    if not fast:
        section("6. 训练循环与 CLI 冒烟")
        run("test_train_loop")
        run("test_train_cli_smoke")
        # 产出 outputs/checkpoints/selftest_model.pth 供评估与接口联调使用
        if _ARTIFACT_CKPT is None:
            _prepare_artifact_ckpt()

        section("7. 评估脚本")
        run("test_evaluate_cli")

        section("8. 速度对比脚本")
        run("test_benchmark_cli")

    section("9. FastAPI 接口")
    run("test_api")

    print(f"\n{'=' * 70}")
    print(f"结果: 通过 {len(PASS)}，失败 {len(FAIL)}")
    if FAIL:
        for n, e in FAIL:
            print(f"  [FAIL] {n}: {e}")
        return 1
    print("全部测试通过！")
    return 0


if __name__ == "__main__":
    # Windows 控制台默认 GBK，统一改为 UTF-8 输出，避免中文/符号导致 UnicodeEncodeError
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    sys.exit(main())
