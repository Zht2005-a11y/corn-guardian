# 玉米病虫害智能识别系统（MCDD + 第二数据集）—— 模型训练 + 后端推理服务

> 本科课程设计 / 学科竞赛答辩用完整工程。
> 交付范围：**数据预处理 → 模型训练（ResNet50 / MobileNetV3 / CBAM）→ 评估（混淆矩阵、P/R/F1）→ 推理封装（Grad-CAM、异常检测）→ FastAPI 后端服务 → 自检与联调脚本**。
> 前端（Streamlit / Web）由另一位同学负责，本仓库保证**模型能力**与**后端接口**稳定可用，接口契约见第 6 节。

---

## 0. 快速开始

> ⚠️ **每次打开新终端都要先 `conda activate corn`**，否则会用到 base 环境的 CPU 版 torch
> （`torch 2.14.1+cpu`），训练慢 20~30 倍。用 `python -c "import torch;print(torch.cuda.is_available())"`
> 确认输出 `True` 再开工。

```bash
conda activate corn                                  # ① 激活 GPU 环境（实测 torch 2.11.0+cu128）
cd corn_disease_system
pip install -r requirements.txt                      # 首次需先按第 2 节装 PyTorch
python -m scripts.prepare_dataset                    # ② 确认两个数据集都被正确识别
python -m scripts.train_full                         # ③ 训练全部模型 + 自动评估
uvicorn app.api:app --host 0.0.0.0 --port 8010        # ④ 启动后端识别服务
```

**训练已完成时只需 ④ + 验证：**

```bash
conda activate corn
cd corn_disease_system
uvicorn app.api:app --host 0.0.0.0 --port 8010        # 终端 A：启动服务

# 终端 B（同样先 conda activate corn）
python -m scripts.verify_api --port 8011   # 16 项真实 HTTP 联调，自动启停服务
```

> 端口说明：本机 8000 被 C-Lodop 打印控件（CLodopPrint32）占用，直接绑 8000 会报
> `[winerror 10013] 以一种访问权限不允许的方式做了一个访问套接字的尝试`。
> 因此默认端口改为 **8010**（`configs/config.yaml` 的 `server.port`）。
> 换机器后若 8010 也冲突，加 `--port 8020` 指定即可，或先 `netstat -ano | findstr :8010` 查占用。

验证：

```bash
python -m scripts.selftest --fast    # 9 项自检，约 10 秒（不训练）
python -m scripts.selftest           # 13 项全量自检，含真实训练 2 个 epoch
python -m scripts.verify_api         # 真实启动 uvicorn 后逐接口 HTTP 联调（16 项）
python -m scripts.model_compare --with-speed   # 三模型精度 + GPU 吞吐对比表
```

---

## 1. 项目结构

```
corn_disease_system/
├── configs/
│   └── config.yaml              # 全局配置：数据集、类别、超参、服务参数（唯一需要改的地方）
├── src/                         # 核心算法包
│   ├── config.py                # 配置加载 + 类别映射（英文/索引/中文）+ 类别名自动归一
│   ├── dataset.py               # 数据增强、多数据集合并、分层切分、DataLoader、加权采样
│   ├── models.py                # ResNet50 / MobileNetV3 / CBAM、冻结解冻、损失、优化器、调度器
│   ├── train.py                 # 两阶段训练主脚本（含断点续训）
│   ├── evaluate.py              # 测试集评估（Acc / P / R / F1 + 混淆矩阵 + 报告）
│   ├── metrics.py               # 指标计算、混淆矩阵与训练曲线绘图（中文字体自适应）
│   ├── gradcam.py               # Grad-CAM 热力图（可解释性）
│   ├── predictor.py             # 推理封装（单张/批量/异常检测/多模型对比/LRU 缓存）
│   └── knowledge_base.py        # 4 类病害专业知识库（症状/规律/防治）
├── app/
│   └── api.py                   # FastAPI 服务（单文件应用，启动即预加载模型）
├── scripts/
│   ├── prepare_dataset.py       # 数据集自检（数量统计 / 损坏图片检查）
│   ├── train_full.py            # 一键训练全部模型 + 自动评估汇总（答辩前跑这个）
│   ├── benchmark.py             # 参数量 / 单图耗时 / 吞吐对比
│   ├── selftest.py              # 端到端自检（13 项用例，`--fast` 为 9 项）
│   ├── verify_api.py            # 自动启停 uvicorn 的真实 HTTP 联调
│   ├── api_test.py              # 对已启动服务的接口冒烟测试
│   └── watch_log.py             # 跨平台日志查看（规避 Windows 终端编码问题）
├── outputs/                     # 运行产物（自动创建）
│   ├── checkpoints/             # best_corn_model.pth 等权重
│   ├── logs/                    # 训练日志
│   ├── reports/                 # 指标 JSON / 混淆矩阵 PNG / 曲线图 / 对比表 / 示例
│   └── inference/               # 推理与 Grad-CAM 输出图
├── requirements.txt
└── README.md
```

### 1.1 数据集（保持原样，无需移动文件）

当前配置已接入**两个数据集**：

```
① MCDD（官方 train/test 划分，4633 张）
D:/shape/Multimodal-Corn-Disease-Dataset-master/MCDD/data/
├── train/{Blight, Common_Rust, Gray_Leaf_Spot, Healthy}   3711
└── test /{Blight, Common_Rust, Gray_Leaf_Spot, Healthy}    922

② 第二数据集（老师提供，PlantVillage 风格，无官方划分，3852 张）
D:/shape/corn_dataset/raw/color/
├── Corn_(maize)___Northern_Leaf_Blight                     985   -> Blight
├── Corn_(maize)___Common_rust_                            1192   -> Common_Rust
├── Corn_(maize)___Cercospora_leaf_spot Gray_leaf_spot      513   -> Gray_Leaf_Spot
└── Corn_(maize)___healthy                                 1162   -> Healthy
```

合并后：**训练 + 验证 7563 张**（分层切出 1135 张做验证），**评估固定使用 MCDD 官方测试集 922 张**。
第二数据集在配置中 `evaluate: false`，只参与训练、不进入评估，避免"训练图当测试图"导致指标虚高。
文件夹名（`Corn_(maize)___...`）由 `normalize_class_name()` 自动归一，无需改动目录结构。

---

## 2. 环境配置

```bash
# 1) 虚拟环境（Python 3.10 / 3.11 推荐）
conda create -n corn python=3.10 -y
conda activate corn

# 2) 先装 PyTorch（版本按自己的 CUDA 选，命令从 https://pytorch.org 复制）
#    CUDA 11.8
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cu118
#    CPU only
pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu

# 3) 其余依赖
cd corn_disease_system
pip install -r requirements.txt

# 4) 验证
python -c "import torch;print(torch.__version__, torch.cuda.is_available())"
```

> **没有 GPU 也能跑**，但慢很多。本机实测（CPU、7563 张、batch=16）：
> 阶段一 1 个 epoch 约 1.5~2 分钟，阶段二约 3~5 分钟；完整 5+20 epoch 约 2~3 小时。
> 时间紧时：
> - `python -m scripts.train_full --only resnet50 --epochs-stage1 2 --epochs-stage2 4`；
> - 或先跑通链路 `--epochs-stage1 1 --epochs-stage2 1`，再到 GPU 机器上 `--resume` 续训。
> 有 GPU（8G 以上）时完整训练约 40~70 分钟。

---

## 3. 数据自检（先跑这一步）

```bash
python -m scripts.prepare_dataset --check-corrupt
```

本机实测输出：

```
[源] MCDD    root=.../MCDD/data             use_for_train=True
     train=3711  test=922   跳过的类别=无
[源] PV_CORN root=D:/shape/corn_dataset/raw  use_for_train=True
     train=3852  test=0     跳过的类别=无
----------------------------------------------------------------------
类别索引  英文名             中文名         train    test    合计
0        Blight            玉米大斑病      2261     315    2576
1        Common_Rust       玉米普通锈病    2237     261    2498
2        Gray_Leaf_Spot    玉米灰斑病       973     114    1087
3        Healthy           健康叶片        2092     232    2324
----------------------------------------------------------------------
训练集合计 7563，测试集合计 922，总计 8485
```

> - **类别索引**：`Blight=0 … Healthy=3`，与 `ImageFolder` 排序一致，权重和接口都依赖它，**不要改 `class_names` 顺序**；
> - `PV_CORN` 的 `test` 为 0 是设计如此（`evaluate: false`）；
> - "跳过的类别=无" 说明所有文件夹名都被成功归一；若出现非空值，去 `src/config.py` 的 `CLASS_ALIASES` 加别名。

---

## 4. 模型训练

### 4.1 三种训练方式

```bash
# ① 只训练主模型 ResNet50（最常用）
python -m src.train

# ② 一键训练全部模型 + 自动评估（ResNet50 + MobileNetV3 + CBAM），答辩前跑
python -m scripts.train_full
python -m scripts.train_full --skip-cbam
python -m scripts.train_full --only resnet50 --epochs-stage2 30

# ③ 只训练某个变体
python -m src.train --arch mobilenet_v3_large --best-name best_corn_mobilenetv3.pth
python -m src.train --use-cbam --best-name best_corn_model_cbam.pth
```

### 4.2 两阶段迁移学习流程

| 阶段 | 冻结策略 | 学习率 | 说明 |
|---|---|---|---|
| 阶段一 | 冻结整个骨干，只训练 `fc`（8196 个参数） | 1e-3，余弦退火 | 快速收敛，几个 epoch 即达可用精度 |
| 阶段二 | 解冻 `layer3`、`layer4` + `fc`（2207 万参数）；BN 统计量冻结 | 1e-4，warmup 1 → 余弦退火 | 微调提升精度，约 +1~3% |

### 4.3 完整超参数表

| 项目 | 取值 | 说明 |
|---|---|---|
| 输入尺寸 | 224×224 | ImageNet 标准输入 |
| 训练增强 | RandomResizedCrop(0.6~1.0, ratio 0.85~1.15)、水平翻转 p=0.5、垂直翻转 p=0.2、±30° 旋转、亮度/对比度/饱和度抖动、RandomErasing p=0.15 | `dataset.build_train_transform` |
| 测试变换 | Resize(256, BICUBIC) → CenterCrop(224) → Normalize | 无随机性，结果可复现 |
| 归一化 | mean=[0.485,0.456,0.406] std=[0.229,0.224,0.225] | 与预训练权重一致 |
| 数据划分 | 合并训练数据分层抽样 15%（seed=42，本机 1135/7563），测试固定 922 | 官方数据无 val |
| batch size | 32（显存不足改 16） | `--batch-size` |
| 优化器 | AdamW（1D 参数不衰减） | weight_decay=1e-4 |
| 损失 | CrossEntropy（label_smoothing=0.1） | 可切加权 CE |
| 调度器 | 阶段一余弦退火；阶段二 warmup + 余弦退火，eta_min=1e-6 | `models.build_scheduler` |
| 混合精度 | AMP（仅 CUDA 生效） | 提速 1.5~2×，显存减半 |
| 梯度裁剪 | max_norm=5.0 | 防止解冻后梯度爆炸 |
| epoch | 5 + 20 | 可按时间调整 |
| 权重选择 | 验证集准确率最高 → `best_corn_model.pth` | 同时保存 `last_<arch>.pth` 用于续训 |

### 4.4 常用命令

```bash
# 类别不均衡时（灰斑病样本最少）：加权采样 + 加权交叉熵
python -m src.train --balance-sampler --class-weighted-loss

# 换数据集根目录 / 调 epoch / 断点续训 / 纯 CPU
python -m src.train --data-root "D:/另份数据/data" --epochs-stage2 30
python -m src.train --resume outputs/checkpoints/last_resnet50.pth
python -m src.train --device cpu --num-workers 0

python -m src.train --help     # 全部参数
```

### 4.5 产物

```
outputs/checkpoints/best_corn_model.pth      # 自描述权重：含 arch / class_names / image_size / val_acc
outputs/checkpoints/last_resnet50.pth        # 最后一个 epoch，用于续训
outputs/logs/train_YYYYmmdd_HHMMSS.log       # 每 epoch 的 loss / acc / lr / 耗时
outputs/reports/history_resnet50.json
outputs/reports/curves_resnet50.png          # 训练曲线（带阶段二分界线）
outputs/reports/dataset_info_resnet50.json   # 各数据源、各类别样本数
```

> 权重"自描述"，后端加载时按 `arch` 自动重建网络，**不需要额外配置文件**。

---

## 5. 模型评估

```bash
# 测试集评估（Acc / 逐类 P-R-F1 / 混淆矩阵）
python -m src.evaluate --weight outputs/checkpoints/best_corn_model.pth

# 两模型对比（精度 + 单图耗时）
python -m src.evaluate --weight outputs/checkpoints/best_corn_model.pth \
                       --compare outputs/checkpoints/best_corn_mobilenetv3.pth

# 纯速度/参数量对比（不需要权重）
python -m scripts.benchmark
```

输出（`outputs/reports/`）：

```
metrics_resnet50_test.json         # 供前端"系统说明页"读取
report_resnet50_test.txt           # 可直接贴进论文的表格
confusion_matrix_resnet50.png      # 混淆矩阵（中文坐标轴）
confusion_matrix_norm_resnet50.png # 归一化混淆矩阵
model_comparison.json / benchmark.json
```

`metrics_*.json` 结构：

```json
{
  "accuracy": 0.98, "macro_precision": 0.98, "macro_recall": 0.98,
  "macro_f1": 0.98, "weighted_f1": 0.98, "num_samples": 922,
  "per_class": [{"class_index":0,"class_name":"玉米大斑病","precision":0.99,"recall":0.98,"f1":0.98,"support":315}],
  "confusion_matrix": [[...]], "labels": ["玉米大斑病","玉米普通锈病","玉米灰斑病","健康叶片"],
  "avg_latency_ms": 12.3
}
```

### 实测结果（MCDD 官方测试集 922 张，RTX 4060 训练完成）

| 模型 | 参数量 | Accuracy | Macro-F1 | Weighted-F1 | 单图耗时 |
|---|---|---|---|---|---|
| **ResNet50** | 23.52M | **98.16%** | 97.71% | 98.14% | 47.0 ms |
| MobileNetV3-Large | 4.21M | 98.05% | 97.41% | 98.03% | 43.9 ms |
| **ResNet50 + CBAM** | 24.17M | **98.37%** | **97.98%** | 98.37% | 45.5 ms |

ResNet50 逐类：大斑病 F1 0.9765 / 锈病 0.9884 / 灰斑病 0.9459 / 健康叶片 0.9978。
灰斑病召回最低（0.9211，样本量最少），CBAM 将其召回提升至 0.9386 —— 可作为答辩中"注意力模块对小类有效"的论据。

完整结果见 `outputs/reports/`：
`final_summary.json`（三模型汇总）、`model_comparison_full.md`（含 GPU 吞吐）、
`metrics_*.json`（逐类指标）、`confusion_matrix_*.png`（中文混淆矩阵）、`curves_*.png`（训练曲线）、
`测试报告.md`（含接口测试 16/16 明细与复现性验证）。

### 5.1 可落地的优化方案

1. **CBAM 注意力**（已实现，`--use-cbam`）：在 `layer3`/`layer4` 后加通道+空间注意力，让模型聚焦病斑区域，病斑小、背景杂时通常 +1~2% Acc，代价是推理慢约 5%。
2. **标签平滑**（已实现，`label_smoothing=0.1`）：抑制过度自信，改善相邻病斑（大斑病 vs 灰斑病）的误判。
3. **类别加权 / 加权采样**（已实现）：合并后灰斑病 1087 张（约为主类 42%），实测类别权重 `[0.836, 0.845, 1.943, 0.904]`，用 `--class-weighted-loss` / `--balance-sampler` 可提升小类召回。
4. **进阶**：CutMix / MixUp、Test-Time Augmentation（多尺度 + 翻转投票）、分层学习率、5-fold 交叉验证选模型。

### 5.2 训练常见问题排查

| 现象 | 可能原因 | 解决办法 |
|---|---|---|
| 训练 Acc 99% 但测试 Acc 低 | 过拟合 / 数据泄漏 | 加大增强、提高 dropout、减小 lr；确认验证集来自 train 切分，测试集未参与训练 |
| Acc 卡在 25%（随机猜） | lr 过大、归一化错误、标签错位 | lr 降到 1e-4；检查 mean/std；核对 `class_names` 顺序 |
| 阶段二一开始 Acc 暴跌 | 解冻后 lr 过大 / BN 统计量被小 batch 污染 | 已内置 BN 统计量冻结 + warmup + 梯度裁剪，必要时再降 lr |
| loss 变 NaN | AMP 溢出 / lr 过大 | `train.amp: false`，或降 lr |
| 显存不足 | batch 太大 | `--batch-size 16`，或换 MobileNetV3 |
| Windows DataLoader 卡住 | `num_workers` 过大 | `--num-workers 0` |
| 某些类别 recall 很低 | 类别不均衡 | `--balance-sampler --class-weighted-loss` |
| 绘图中文变方块 | 缺中文字体 | 装 SimHei / 微软雅黑；`metrics.setup_chinese_font()` 自动探测 |

---

## 6. 后端推理服务（FastAPI）

### 6.1 启动

```bash
uvicorn app.api:app --host 0.0.0.0 --port 8010     # 或 python app/api.py
```

- 启动时按 `config.yaml → server.models` **单例预加载**所有模型并 warmup；
- 找不到权重时打印 `[警告] 未找到权重，使用随机初始化（仅用于联调）`，接口照常可用，**前端可并行开发**；
- Swagger 文档：<http://127.0.0.1:8010/docs>

### 6.2 接口清单

统一响应：`{ "code": 0, "message": "ok", "data": {...}, "request_id": "...", "elapsed_ms": 32.5 }`

| 方法 | 路径 | 说明 |
|---|---|---|
| GET | `/health` | 健康检查：设备、模型加载状态、LRU 缓存命中 |
| GET | `/models` | 可用模型 + 类别中英文映射 |
| GET | `/knowledge`、`/knowledge/{key}` | 4 类病害知识库（key 可用英文名 / 中文名 / 索引） |
| GET | `/dataset/info` | 各数据源与各类别图片统计 |
| POST | `/predict` | 单图识别（字段 `file`） |
| POST | `/predict/gradcam` | 单图识别 + Grad-CAM 热力图（base64） |
| POST | `/predict/batch` | 多图批量识别（字段 `files`，≤20 张） |
| POST | `/predict/compare` | 同一张图跑所有模型，返回结果 + 耗时 |
| POST | `/predict/base64` | base64 图片（适配小程序 / 不便传文件的场景） |
| POST | `/cache/clear` | 清空预处理缓存 |

`/predict` 返回示例：

```json
{
  "code": 0, "message": "ok",
  "data": {
    "filename": "leaf.jpg", "class_index": 1, "class_name_en": "Common_Rust",
    "class_name": "玉米普通锈病", "confidence": 0.9731, "confidence_percent": "97.31%",
    "confidence_level": "high", "confidence_hint": "高置信度：识别结果可靠",
    "is_healthy": false, "is_valid_leaf": true, "warning": null,
    "top2": {"class_name": "玉米大斑病", "confidence": 0.0182},
    "probabilities": {"玉米大斑病": 0.0182, "玉米普通锈病": 0.9731, "玉米灰斑病": 0.0042, "健康叶片": 0.0045},
    "model": "resnet50", "inference_time_ms": 11.8, "image_size": [1024, 768],
    "knowledge": {"name_cn": "玉米普通锈病", "symptoms": ["..."], "occurrence": ["..."], "control": {"agricultural": ["..."], "chemical": ["..."], "field": ["..."]}}
  }
}
```

批量返回 `data: { results: [...], failed: [...], summary: {total, class_counts, disease_count, healthy_count, avg_confidence} }`，
前端导出 CSV 直接用 `results` 的 `filename / class_name / confidence`。

### 6.3 性能与健壮性

- **模型单例**：`lifespan` 中加载一次，请求只做前向；
- **预热 warmup**：首轮 cuDNN 算法选择 / 显存分配不计入用户请求；
- **预处理缓存**：按图片内容 MD5 做 LRU（默认 256 条），同一图片重复识别不再解码+归一化；
- **批量推理**：多图拼 batch 前向，比逐张循环快 2~4 倍；
- **输入限制**：单文件 ≤10MB、最长边 ≤4096px、最小边 ≥32px，超限返回 413/400；
- **CORS**：默认放行所有来源，方便 Streamlit / 前端同学跨域调用；
- **错误处理**：损坏图片 → 400、未知模型 → 400、服务未就绪 → 503、未捕获异常 → 500（不含堆栈），响应头带 `X-Request-Id`。

### 6.4 前端对接示例

```python
import requests

# 单图
with open("leaf.jpg", "rb") as f:
    r = requests.post("http://127.0.0.1:8010/predict", files={"file": ("leaf.jpg", f)}).json()
print(r["data"]["class_name"], r["data"]["confidence"], r["data"]["confidence_level"])

# 批量
files = [("files", ("a.jpg", open("a.jpg", "rb"))), ("files", ("b.jpg", open("b.jpg", "rb")))]
print(requests.post("http://127.0.0.1:8010/predict/batch", files=files).json()["data"]["summary"])

# 指定模型（模型对比功能）
requests.post("http://127.0.0.1:8010/predict?model=mobilenet_v3_large",
              files={"file": ("leaf.jpg", open("leaf.jpg", "rb"))})
```

```bash
curl.exe -X POST http://127.0.0.1:8010/predict -F "file=@D:/test/leaf.jpg"
```

### 6.5 服务自测

```bash
python -m scripts.verify_api          # 自动启停服务，逐接口验证，并把 Grad-CAM 示例存入 outputs/inference
python -m scripts.api_test            # 服务已在运行时使用
```

---

## 7. 命令行快速识别（不上服务也能演示）

```bash
python -m src.predictor "D:/test/leaf.jpg"                 # 单张，输出 JSON
python -m src.predictor "D:/test/leaf.jpg" --gradcam       # 单张 + Grad-CAM（存 outputs/inference/）
python -m src.predictor "D:/test/pics"                     # 整个目录批量
python -m src.predictor "D:/test/leaf.jpg" --model mobilenet_v3_large
```

---

## 8. 多数据集扩展

编辑 `configs/config.yaml` 的 `data.sources` 追加一项即可，训练时自动合并：

```yaml
data:
  sources:
    - name: MCDD
      root: "D:/shape/Multimodal-Corn-Disease-Dataset-master/MCDD/data"
      train_dir: train
      test_dir: test
      use_for_train: true
      evaluate: true          # 参与官方测试集评估
    - name: DATASET_V3
      root: "D:/shape/DatasetV3/data"
      train_dir: train
      test_dir: test          # 若没有独立测试集，与 train_dir 指向同一目录并设 evaluate: false
      use_for_train: true
      evaluate: false
```

类别名归一规则（`normalize_class_name`）已覆盖：
大小写 / 空格 / 连字符、常见前缀（`Corn_(maize)___`、`Corn_`、`Maize_`）、别名表（`Rust` / `Gray_Spot` / `Health` / `Northern_Leaf_Blight` / `NLB` …）、包含式匹配。
实在对不上就往 `CLASS_ALIASES` 加一行，**不需要改代码结构**。
加入新数据后先跑 `python -m scripts.prepare_dataset`，确认"跳过的类别=无"再训练。

---

## 9. 答辩要点（可直接引用）

- **任务**：玉米 4 类叶部状态（大斑病 / 普通锈病 / 灰斑病 / 健康）细粒度识别；
  训练数据 **7563 张（MCDD 3711 + 第二数据集 3852，多源合并）**，评估固定 MCDD 官方测试集 **922 张**；
- **方法**：ResNet50 ImageNet 迁移学习 + 两阶段微调（冻结骨干 → 解冻 layer3/4）+ 农业场景定制增强 + 标签平滑 + AdamW + 余弦退火 + AMP；
- **对比**：MobileNetV3-Large 参数量 4.21M（ResNet50 23.52M，约 1/5.6），推理更快，适合边缘部署；
  数据由 `scripts/benchmark.py` 与 `evaluate.py --compare` 生成（`outputs/reports/benchmark.json`）；
- **可解释性**：Grad-CAM 热力图证明模型关注的是病斑区域而非背景（病害叶片热力集中在病斑，健康叶片分散）；
- **工程化**：自描述权重、模型单例、LRU 缓存、批量推理、异常图片拦截、统一响应格式、CORS、13 项自检脚本；
- **扩展性**：多数据集配置化合并，新增数据只改 yaml，不动代码。

---

## 10. 常见运行报错

| 报错 | 原因 | 解决 |
|---|---|---|
| `ModuleNotFoundError: No module named 'src'` | 不在项目根目录运行 | `cd corn_disease_system` 后再执行 `python -m ...` |
| `FileNotFoundError: 配置文件不存在` | 工作目录不对 | 同上，或用 `--config` 指定绝对路径 |
| `RuntimeError: 未扫描到任何训练图片` | yaml 里数据路径错 | 检查 `data.sources[].root`，Windows 路径用 `/` 或 `\\` |
| 首次训练卡在 `Downloading resnet50-...pth` | 需下载预训练权重 | 保持联网；离线可手动放到 `~/.cache/torch/hub/checkpoints/`，或 `--no-pretrained` |
| `CUDA out of memory` | 显存不足 | `--batch-size 16`，或换 MobileNetV3 |
| `Error loading "*.pth"` | 权重与 arch 不匹配 | 加载时显式 `--arch`；`/models` 接口的 `arch` 字段即真实结构 |
| 服务启动日志出现 `[警告] 未找到权重` | 路径不对 / 还没训练 | 检查 `server.models.*.path`（相对 `corn_disease_system/`），或先训练 |
| `422 Unprocessable Entity` | 上传字段名不对 | 单图 `file`，批量 `files` |
| `PermissionError: [WinError 32] ...train_xxx.log` | 日志文件句柄未释放 | 已在 `train.setup_logging` 中关闭旧 handler；再次出现可关掉占用该日志的程序 |
| Windows 终端中文乱码 / `UnicodeEncodeError` | 控制台默认 GBK | `chcp 65001` 或 `python -X utf8 ...`；日志本身统一 UTF-8 写入 |
| 中文坐标轴显示方块 | 无中文字体 | 装微软雅黑 / SimHei；Linux 装 `fonts-noto-cjk` |
