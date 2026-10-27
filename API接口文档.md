# 玉米病虫害智能识别系统 · 后端接口文档

> 服务框架：FastAPI　|　默认地址：`http://127.0.0.1:8010`　|　Swagger：`http://127.0.0.1:8010/docs`
> 文档基于当前代码快照整理（2026-10-22），行号会随代码编辑漂移，建议同时用函数名定位。

---

## 目录

1. [服务概览](#1-服务概览)
2. [前后端调用链路](#2-前后端调用链路)
3. [通用约定](#3-通用约定)
4. [接口总览](#4-接口总览)
5. [大屏接口（前端在用）](#5-大屏接口前端在用)
6. [基础接口](#6-基础接口)
7. [知识库接口](#7-知识库接口)
8. [识别接口](#8-识别接口)
9. [关键数据结构](#9-关键数据结构)
10. [前端调用位置速查](#10-前端调用位置速查)
11. [启动与联调](#11-启动与联调)
12. [已知注意事项](#12-已知注意事项)

---

## 1. 服务概览

| 项目 | 内容 |
|---|---|
| 主应用入口 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\api.py` |
| 大屏子路由 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\bigscreen_api.py` |
| 配置文件 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\configs\config.yaml` |
| 监听地址 | `0.0.0.0:8010`（避开被占用的 8000） |
| 模型 | `resnet50`（默认）、`mobilenet_v3_large`、`resnet50_cbam` |
| 类别 | `Blight` / `Common_Rust` / `Gray_Leaf_Spot` / `Healthy` |
| 启动脚本 | `D:\shijianzhou\sjzprogram\run_backend.bat`（conda 环境 `torch_gpu`） |
| 一键启动 | `D:\shijianzhou\sjzprogram\start_all.bat` |
| 问答大模型 | Agnes-3.0-Flash（`configs/config.yaml` 的 `llm` 段） |

模型在应用启动时以单例预加载：`api.py:91-108`（`lifespan`），全局变量 `api.py:88`。

---

## 2. 前后端调用链路

```
frontend/src/views/bigScreen/Layout.vue
   │  axios.get/post('/api/screen/xxx')
   ▼
frontend/vite.config.mjs:15-21  代理：'/api' → http://127.0.0.1:8010，rewrite 去掉 '/api'
   ▼
app/api.py:118-119  app.include_router(screen_router)
   ▼
app/bigscreen_api.py:24  APIRouter(prefix="/screen")
```

- 前端请求路径写 `/api/screen/...`，后端实际路径是 `/screen/...`。
- 前端只调用 4 个接口，全部位于
  `D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue`：
  - `GET  /api/screen/samples`　　`Layout.vue:519`
  - `POST /api/screen/predict`　　`Layout.vue:602`
  - `POST /api/screen/chat`　　　　`Layout.vue:675`
  - `GET  /api/screen/telemetry`　 `Layout.vue:710`
- 打包为 `dist` 静态部署后没有 Vite 代理，需要 Nginx 做同样的 `/api/` → `127.0.0.1:8010/` 转发。

---

## 3. 通用约定

### 3.1 统一响应包（`app/api.py:66-75`）

```json
{
  "code": 0,
  "message": "ok",
  "data": {},
  "request_id": "可选，异常时出现",
  "elapsed_ms": 0.0
}
```

- `code = 0` 表示成功；`data` 为业务数据。
- 响应头统一带有 `X-Request-Id`（请求追踪）与 `X-Elapsed-Ms`（服务端耗时），由中间件 `api.py:133-148` 写入。

### 3.2 错误返回

| 场景 | 状态码 | 响应体 | 代码位置 |
|---|---|---|---|
| 图片损坏 / 格式不支持 / 尺寸异常 | 400 | `{"code":400,"message":"...","data":null}` | `api.py:151-153` |
| 类别 key 不存在 | 400 | `{"code":400,"message":"...","data":null}` | `api.py:156-158` |
| 文件类型 / 大小 / 业务校验失败 | 400 / 413 | `{"detail":"..."}`（FastAPI 默认） | `api.py:171-185` |
| 模型尚未加载完成 | 503 | `{"detail":"模型尚未加载完成，请稍后重试"}` | `api.py:164-168` |
| 未捕获异常 | 500 | `{"code":500,"message":"服务器内部错误...","data":null}` | `api.py:137-144` |

### 3.3 上传限制

- 支持格式：`jpg / jpeg / png / bmp / webp`（`src/predictor.py:51`）。
- 单文件上限：`server.max_upload_mb = 10`（`configs/config.yaml:77`）。
- 最长边上限：`infer.max_image_side = 4096`。
- 批量上限：20 张（`api.py:60`、`api.py:342-343`）。
- 大屏接口走 base64 JSON，不受 multipart 10MB 限制，但仍校验图片尺寸与格式。

---

## 4. 接口总览

| # | 方法 | 后端路径 | 前端路径 | 前端是否调用 | 分组 |
|---|---|---|---|---|---|
| 1 | GET | `/screen/samples` | `/api/screen/samples` | ✅ | 大屏 |
| 2 | POST | `/screen/predict` | `/api/screen/predict` | ✅ | 大屏 |
| 3 | POST | `/screen/chat` | `/api/screen/chat` | ✅ | 大屏 |
| 4 | GET | `/screen/telemetry` | `/api/screen/telemetry` | ✅ | 大屏 |
| 4b | GET | `/screen/knowledge` | `/api/screen/knowledge` | ✅（侧边栏「病害图鉴」弹窗） | 大屏 |
| 5 | GET | `/` | — | ❌ | 基础 |
| 6 | GET | `/health` | — | ❌ | 基础 |
| 7 | GET | `/models` | — | ❌ | 基础 |
| 8 | GET | `/dataset/info` | — | ❌ | 基础 |
| 9 | POST | `/cache/clear` | — | ❌ | 基础 |
| 10 | GET | `/favicon.ico` | — | ❌（浏览器自动） | 基础 |
| 11 | GET | `/knowledge` | — | ❌ | 知识库 |
| 12 | GET | `/knowledge/{key}` | — | ❌ | 知识库 |
| 13 | POST | `/predict` | — | ❌ | 识别 |
| 14 | POST | `/predict/gradcam` | — | ❌ | 识别 |
| 15 | POST | `/predict/batch` | — | ❌ | 识别 |
| 16 | POST | `/predict/compare` | — | ❌ | 识别 |
| 17 | POST | `/predict/base64` | — | ❌ | 识别 |

---

## 5. 大屏接口（前端在用）

### 5.1 `GET /screen/samples` 获取典型大田样本

| 项目 | 内容 |
|---|---|
| 前端调用 | `D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue:519`（函数 `fetchPresetSamples`，`Layout.vue:517`） |
| 前端触发 | 页面 `onMounted`，`Layout.vue:843` → `Layout.vue:856` 自动拉取 |
| 后端定义 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\bigscreen_api.py:171-211`（`get_preset_samples()` 在 172） |
| 内部调用 | 读图转 base64 `bigscreen_api.py:55`（192 行调用）；知识库 `src\knowledge_base.py:152`（196 行调用）；测试集目录 `bigscreen_api.py:30` |

**请求参数**：无。

**响应示例**

```json
{
  "code": 0,
  "message": "ok",
  "data": [
    {
      "id": "blight",
      "name": "玉米大斑病",
      "scenario": "强日光直射",
      "diseaseName": "玉米大斑病 (Northern Corn Leaf Blight)",
      "class_name_en": "Blight",
      "pathogen": "真菌，大斑凸脐蠕孢……",
      "color": "#e28557",
      "imgData": "data:image/jpeg;base64,....",
      "filename": "xxx.jpg"
    }
  ]
}
```

**前端消费**：`Layout.vue:520-526` 写入 `presetSamples` 并 `selectPreset()`（`Layout.vue:532`），`imgData` 作为预览图（`Layout.vue:538`）；同时把 `backendOnline` 置为 `true`（顶部状态条）。

**备注**：样本取自 `dataset/MCDD/data/test/<类别>/` 下每类第一张图（`bigscreen_api.py:30`、`182-194`）。

---

### 5.2 `POST /screen/predict` 大屏综合诊断

| 项目 | 内容 |
|---|---|
| 前端调用 | `D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue:602`（函数 `runDetect`，`Layout.vue:595`） |
| 前端触发 | 「执行 AI 智能病害感知与精准诊断」按钮 `Layout.vue:186` |
| 后端定义 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\bigscreen_api.py:223-302`（`predict_screen()` 在 224） |
| 请求体模型 | `bigscreen_api.py:217-220`（`Base64PredictRequest`） |
| 内部调用 | 模型单例 `app\api.py:88` / `bigscreen_api.py:230`；推理 `src\predictor.py:505`（248 行调用）；病斑框 `bigscreen_api.py:63`（269 行调用）；无人机参数 `bigscreen_api.py:142`（273 行调用）；知识库 `src\knowledge_base.py:152`（266 行调用） |

**请求体**

```json
{
  "image_base64": "data:image/jpeg;base64,....",
  "filename": "leaf.jpg",
  "model": "resnet50_cbam"
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `image_base64` | string | 是 | 可带 `data:image/...;base64,` 前缀 |
| `filename` | string | 否 | 默认 `screen_upload.jpg` |
| `model` | string | 否 | 默认 `resnet50_cbam`；不存在时自动回退 `default_model`（`bigscreen_api.py:244-246`） |

**响应示例**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "diseaseName": "玉米大斑病 (Northern Corn Leaf Blight)",
    "class_name_en": "Blight",
    "class_name_cn": "玉米大斑病",
    "pathogen": "真菌，大斑凸脐蠕孢……",
    "severity": "中度 (II 级扩展期)",
    "damageRate": 23.5,
    "confidence": 96.8,
    "color": "#e28557",
    "boxes": [
      {"x": 30.2, "y": 18.4, "w": 38.0, "h": 30.0, "label": "大斑病灶 #1", "conf": "96.8%"}
    ],
    "prescription": "选用 ……，利用大田植保无人机实施傍晚超低空变量精准喷雾。",
    "droneParams": {
      "model": "大疆 T50 / T60",
      "volume": "1.6 L/亩",
      "dropletSize": "135 μm",
      "altitude": "2.2 米",
      "speed": "5.0 m/s"
    },
    "gradcam_base64": "data:image/png;base64,....",
    "leaf_score": 0.95,
    "probabilities": {"玉米大斑病": 0.968, "玉米南方锈病": 0.02, "玉米灰斑病": 0.008, "健康叶片": 0.004},
    "model_used": "resnet50_cbam",
    "inference_ms": 14.2
  }
}
```

**前端消费**

- 诊断报告四项指标：`Layout.vue:610-625`；
- 病斑 BBox 叠加：模板 `Layout.vue:124-142`；
- Grad-CAM 切换：`Layout.vue:146-147` + `toggleHeatmap()` `Layout.vue:590`；
- 处方与无人机参数：`Layout.vue:246-252`；
- 顶部模型名与耗时：`Layout.vue:628-629`；
- 同时向对话区推送诊断摘要：`Layout.vue:631-633`。

**备注**：`damageRate` / `severity` 由 Grad-CAM 高响应区域估算（`bigscreen_api.py:63-139`），非人工标注真值。

---

### 5.3 `POST /screen/chat` 植保专家问答

| 项目 | 内容 |
|---|---|
| 前端调用 | `D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue:675`（函数 `sendMessage`，`Layout.vue:660`） |
| 前端触发 | 回车 `Layout.vue:352`；发送按钮 `Layout.vue:356`；快捷问题 `Layout.vue:305-307` → `askPreset()` `Layout.vue:698` |
| 后端定义 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\bigscreen_api.py:314-353`（`chat_screen()` 在 315） |
| 请求体模型 | `bigscreen_api.py:308-311`（`ChatRequest`） |
| 内部调用 | 配置 `src\config.py:99`（324 行）；大模型 `src\llm_client.py:147` `ask_agnes`（333 行）；Prompt 拼装 `src\llm_client.py:43`；本地兜底 `src\llm_client.py:76` |

**请求体**

```json
{
  "message": "大斑病用什么药？",
  "context": {
    "diseaseName": "玉米大斑病 (Northern Corn Leaf Blight)",
    "severity": "中度 (II 级扩展期)",
    "damageRate": 23.5,
    "prescription": "选用 ……",
    "climate": {"temp": 28.4, "humidity": 84.2}
  },
  "history": [
    {"role": "user", "content": "你好"},
    {"role": "assistant", "content": "您好……"}
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|---|---|---|---|
| `message` | string | 是 | 为空返回 400（`bigscreen_api.py:321-322`） |
| `context` | object | 否 | 诊断上下文，字段见 `llm_client.py:49-70` |
| `history` | array | 否 | 前端取最近 6 条（`Layout.vue:669-672`），模型侧再截取 6 条（`llm_client.py:165-174`） |

**响应示例**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "reply": "【玉米大斑病专家防治指导】……",
    "model": "agnes-3.0-flash",
    "source": "agnes-ai",
    "usage": {}
  }
}
```

**前端消费**：取 `data.reply`（`Layout.vue:688-689`），经 `renderFormattedText()`（`Layout.vue:644-658`）转换 Markdown/换行后通过 `v-html` 渲染（模板 `Layout.vue:324`）。

**备注**：大模型不可达时由 `fallback_expert_reply`（`llm_client.py:76`）按关键词返回本地专家话术，保证页面可用。

---

### 5.4 `GET /screen/telemetry` 大屏遥测数据

| 项目 | 内容 |
|---|---|
| 前端调用 | `D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue:710`（函数 `initCharts`，`Layout.vue:708`） |
| 前端触发 | `onMounted` → `nextTick`，`Layout.vue:859-861`，只拉一次 |
| 后端定义 | `D:\shijianzhou\sjzprogram\model\corn_disease_system_20261021\app\bigscreen_api.py:359-402`（`get_telemetry()` 在 360） |
| 内部调用 | 无外部依赖，数据写死在 `bigscreen_api.py:364-383` |

**请求参数**：无。

**响应示例**

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "climate": {
      "hours": ["00:00", "02:00", "..."],
      "temperatures": [21.5, 20.8, "..."],
      "humidities": [86.2, 88.5, "..."],
      "lights": [0, 0, "..."],
      "currentTemp": 28.4,
      "currentHumidity": 84.2,
      "currentLight": 68.5,
      "windSpeed": 2.1
    },
    "distribution": [
      {"name": "玉米大斑病", "value": 38.5, "color": "#e28557"}
    ],
    "radar": [
      {"name": "强日光眩光抑制", "max": 100, "value": 96.8}
    ]
  }
}
```

**前端消费**

- 24 小时趋势图：`Layout.vue:726-763`（注意：曲线「发病风险指数」= `temperatures × 2.5`，`Layout.vue:745`）；
- 六维雷达：`Layout.vue:772-797`；
- 病害分布玫瑰图：`Layout.vue:803-829`；
- 窗口缩放只重绘不重拉：`handleResize()` `Layout.vue:836-840`。

---

## 6. 基础接口

### 6.1 `GET /`　服务首页与接口自述

- 后端：`api.py:197-216`（`index()` 在 198）
- 前端：未调用
- 响应：服务名、版本、`docs` 地址、`endpoints` 列表（`api.py:204-214`）

### 6.2 `GET /health`　健康检查

- 后端：`api.py:219-238`（`health()` 在 220）
- 前端：未调用；大屏顶部的在线状态实际来自 `/screen/samples` 是否成功
- 内部：`PREDICTOR.load_report`（`src/predictor.py:269/279`，`api.py:232` 使用）、缓存统计（`api.py:235`）
- 响应字段：`status`、`device`、`models{key:{loaded,arch,val_acc}}`、`default_model`、`cache{key:{size,capacity,hits,misses}}`、`timestamp`

### 6.3 `GET /models`　模型与类别

- 后端：`api.py:241-251`（`list_models()` 在 242）
- 前端：未调用
- 内部：`src/predictor.py:269`；`src/config.py:225` `get_class_names`、`src/config.py:233` `get_class_cn`
- 响应字段：`default_model`、`models`（即 `load_report`）、`class_names`、`class_names_cn`

### 6.4 `GET /dataset/info`　数据集统计

- 后端：`api.py:285-301`（`dataset_info()` 在 286）
- 前端：未调用
- 内部：`src/dataset.py:189` `collect_samples`（`api.py:291` 调用）、`src/config.py:225`
- 响应字段：`sources`、`class_names`、`train_total`、`test_total`、`train_distribution`、`test_distribution`

### 6.5 `POST /cache/clear`　清空预处理缓存

- 后端：`api.py:393-397`（`clear_cache()` 在 394）
- 前端：未调用（运维手动）
- 内部：`src/predictor.py:509` `clear_cache`（`api.py:396` 调用）
- 响应：`{"code":0,"data":{"cleared":true}}`

### 6.6 `GET /favicon.ico`

- 后端：`api.py:191-194`，返回 204，避免日志出现 404
- 前端：浏览器自动请求

---

## 7. 知识库接口

### 7.1 `GET /knowledge`

- 后端：`api.py:254-266`（`list_knowledge()` 在 255）
- 内部：`KNOWLEDGE_BASE`（`src/knowledge_base.py:10`，`api.py:264` 遍历）
- 响应示例：

```json
{
  "code": 0,
  "data": {
    "Blight": {
      "class_index": 0,
      "name_cn": "玉米大斑病",
      "name_en": "Northern Corn Leaf Blight",
      "pathogen": "真菌，大斑凸脐蠕孢……"
    }
  }
}
```

### 7.2 `GET /knowledge/{key}`

- 后端：`api.py:269-282`（`knowledge_detail()` 在 270）
- 内部：`src/knowledge_base.py:10`、`src/knowledge_base.py:152`
- `key` 支持英文名、中文名、索引：`Blight` / `玉米大斑病` / `0`（`api.py:273-281`）
- 响应：`{"key":"Blight", "name_cn":"...", "name_en":"...", "pathogen":"...", "symptoms":[...], "occurrence":[...], "control":{"agricultural":[...],"chemical":[...],"field":[...]}, "severity":"..."}`
- 类别不存在返回 404（`api.py:280-281`）

---

## 8. 识别接口

### 8.1 `POST /predict`　单图识别（multipart）

- 后端：`api.py:307-320`（`predict()` 在 308）
- 前端：未调用（大屏用 `/screen/predict`）
- 内部：`_predictor()` `api.py:164`；`_validate_upload()` `api.py:171`；`_read_file()` `api.py:177`；`predict_bytes` `src/predictor.py:381`（`api.py:316`）；`get_knowledge` `src/knowledge_base.py:152`（`api.py:317`）

**请求**

| 位置 | 参数 | 说明 |
|---|---|---|
| multipart | `file` | 图片文件 |
| query | `model` | 可选，模型 key |

**响应**：`src/predictor.py:347-368` 的结果字段，并追加 `knowledge`。字段包括：

```json
{
  "code": 0,
  "message": "ok",
  "data": {
    "filename": "a.jpg",
    "class_index": 0,
    "class_name_en": "Blight",
    "class_name": "玉米大斑病",
    "confidence": 0.968,
    "confidence_percent": "96.80%",
    "confidence_level": "high",
    "confidence_hint": "高置信度：识别结果可靠",
    "is_healthy": false,
    "is_valid_leaf": true,
    "warning": null,
    "top2": {"class_name": "玉米南方锈病", "confidence": 0.02},
    "probabilities": {"玉米大斑病": 0.968, "玉米南方锈病": 0.02, "玉米灰斑病": 0.008, "健康叶片": 0.004},
    "model": "resnet50",
    "inference_time_ms": 14.2,
    "image_size": [1024, 768],
    "knowledge": {"name_cn": "玉米大斑病", "...": "..."}
  },
  "elapsed_ms": 21.5
}
```

### 8.2 `POST /predict/gradcam`

- 后端：`api.py:323-332`（`predict_gradcam()` 在 324）
- 内部：`src/predictor.py:505` `predict_with_gradcam`（`api.py:331`）→ `src/predictor.py:489-503` `explain` → `src/gradcam.py:23/95/102`
- 请求：`file` + 可选 query `model`
- 响应：在 8.1 基础上多出：

```json
"gradcam": {
  "class_index": 0,
  "heatmap_base64": "data:image/png;base64,....",
  "overlay_base64": "data:image/png;base64,....",
  "format": "PNG(base64)"
}
```

### 8.3 `POST /predict/batch`

- 后端：`api.py:335-359`（`predict_batch()` 在 336）
- 内部：`src/predictor.py:413`（`api.py:356`）
- 请求：`files`（多文件，≤20），可选 query `model`
- 响应：`{"results":[...],"failed":[{"filename","error"}],"summary":{...}}`，`summary` 见 `src/predictor.py:460-474`（`total/success_count/avg_confidence/class_counts/disease_count/healthy_count/failed_count`）
- 单张格式错误不会中断整批（`api.py:345-353`）

### 8.4 `POST /predict/compare`

- 后端：`api.py:362-368`（`predict_compare()` 在 363）
- 内部：`src/predictor.py:477` `compare`（`api.py:367`）
- 响应：`{"results":[{各模型结果或error}], "models":["resnet50", ...]}`

### 8.5 `POST /predict/base64`

- 后端：`api.py:371-390`（`predict_base64()` 在 372），请求体 `Base64Request`（`api.py:78-82`）
- 请求体：

```json
{
  "image_base64": "....",
  "filename": "upload.jpg",
  "model": "resnet50",
  "gradcam": false
}
```

- 内部：`gradcam=true` 走 `src/predictor.py:505`（386 行），否则 `src/predictor.py:381`（388 行）并追加知识库（389 行）

---

## 9. 关键数据结构

### 9.1 病斑框 `boxes[]`（`app/bigscreen_api.py:63-139`）

| 字段 | 类型 | 说明 |
|---|---|---|
| `x` / `y` | float | 左上角百分比（0~100） |
| `w` / `h` | float | 宽高百分比 |
| `label` | string | 病灶名称，如「大斑病灶 #1」 |
| `conf` | string | 置信度文本，如 `96.8%` |

### 9.2 无人机参数 `droneParams`（`app/bigscreen_api.py:142-165`）

`model`、`volume`、`dropletSize`、`altitude`、`speed`

### 9.3 遥测 `climate`（`app/bigscreen_api.py:389-398`）

`hours[]`、`temperatures[]`、`humidities[]`、`lights[]`、`currentTemp`、`currentHumidity`、`currentLight`、`windSpeed`

### 9.4 问答请求 `ChatRequest`（`app/bigscreen_api.py:308-311`）

`message`、`context`、`history`

---

## 10. 前端调用位置速查

文件：`D:\shijianzhou\sjzprogram\frontend\src\views\bigScreen\Layout.vue`

| 功能 | 函数 | 函数行 | axios 行 | 触发位置 |
|---|---|---|---|---|
| 拉样本 | `fetchPresetSamples()` | 517 | 519 `axios.get` | `onMounted` 856 |
| 诊断 | `runDetect()` | 595 | 602 `axios.post` | 按钮 186 |
| 问答 | `sendMessage()` | 660 | 675 `axios.post` | 回车 352 / 按钮 356 / 快捷 305-307 |
| 遥测 | `initCharts()` | 708 | 710 `axios.get` | `nextTick` 859-861 |
| 快捷提问 | `askPreset()` | 698 | — | 305-307 |
| 选样本 | `selectPreset()` | 532 | — | 172 |
| 热力图切换 | `toggleHeatmap()` | 590 | — | 146-147 |

代理配置：`D:\shijianzhou\sjzprogram\frontend\vite.config.mjs:15-21`

---

## 11. 启动与联调

### 11.1 启动

```bat
:: 后端（8010）
D:\shijianzhou\sjzprogram\run_backend.bat

:: 前端（5173）
D:\shijianzhou\sjzprogram\run_frontend.bat

:: 或一键启动
D:\shijianzhou\sjzprogram\start_all.bat
```

### 11.2 接口自测

- Swagger：`http://127.0.0.1:8010/docs`
- 健康检查：`http://127.0.0.1:8010/health`
- 大屏样本：`http://127.0.0.1:8010/screen/samples`

### 11.3 数据与权重

- 数据集：`D:\shijianzhou\sjzprogram\dataset\MCDD\data\{train,test}\<类别>\`
- 权重：`model\corn_disease_system_20261021\outputs\checkpoints\`
  - `best_corn_model.pth`（resnet50）
  - `best_corn_mobilenetv3.pth`
  - `best_corn_model_cbam.pth`

---

## 12. 已知注意事项

1. **前端只接了 4 个接口**：其余接口留给 Swagger 演示、脚本与运维；若要让顶部状态更准确，可改调 `GET /api/health`。
2. **代理前缀**：前端必须写 `/api/screen/...`；生产环境需 Nginx 转发并去掉 `/api`。
3. **模型回退**：前端固定传 `model: 'resnet50_cbam'`，后端若找不到该 key 会自动回退 `default_model`（`bigscreen_api.py:244-246`），因此顶部模型名可能与预期不同。
4. **状态推断**：`backendOnline` 由 `/screen/samples` 成功与否决定，并不代表模型已加载；模型未就绪时 `/screen/predict` 返回 503。
5. **请求库混用**：`frontend/src/utils/spost/index.js` 是旧模板封装，依赖 `.env` 的 `VITE_APP_API_*` 且判断 `STATUS === '0000'`，与本项目 `{code, message, data}` 格式不兼容，不要用于这 4 个接口。
6. **错误提示较弱**：`Layout.vue` 三处调用只取 `res.data.data`，未判断 `code`；异常统一走 `catch` 通用提示。
7. **超时**：前端使用裸 `axios`，未设置 timeout；后端推理接口默认同步执行，图片较大时首帧会偏慢。
