# 微信小程序端：玉米叶部病斑多尺度自适应感知与飞防决策系统

按参考图 1:1 复刻的浅色自然风格微信小程序（原生小程序框架，非 uni-app），8 个业务页面全部独立实现，直接对接本仓库现有 FastAPI 后端（`model/corn_disease_system_20261021`，端口 8010），不重复实现模型推理与处方算法。

## 一、运行说明

1. 启动后端：双击仓库根目录 `run_backend.bat`（FastAPI: http://127.0.0.1:8010）。
2. 用微信开发者工具「导入项目」，目录选择 `miniprogram/`，AppID 可用测试号（默认 `touristappid`）。
3. 开发者工具右上角「详情 → 本地设置」勾选 **「不校验合法域名、web-view（业务域名）、TLS 版本以及 HTTPS 证书」**（本地 HTTP 后端必须）。
4. 编译即可运行。AI 问答流式输出、病害识别、历史记录、田间监测均为真实接口数据。

> 真机预览：把 `utils/config.js` 的 `BASE_URL` 改成电脑局域网 IP（如 `http://192.168.1.100:8010`），手机与电脑同一 Wi-Fi。

## 二、API 配置

所有请求经 `utils/api.js` 封装，基地址在 `utils/config.js`：

| 接口 | 用途 | 页面 |
|---|---|---|
| `POST /screen/predict` | 单张识别（Grad-CAM/病斑框/受损率/处方） | identify → result → spray |
| `POST /screen/predict/batch` | 批量巡田识别（≤24 张，汇总） | identify（批量模式） |
| `POST /screen/chat/stream` | 植保 AI 助手 SSE 流式问答 | chat（enableChunked 逐块解析） |
| `GET/DELETE /screen/history(/{id})` | 诊断历史查询/详情/删除 | history、首页最近记录 |
| `GET /screen/sessions(/{sid})` | 会话找回/恢复 | assistant 最近会话 |
| `GET /screen/telemetry` | 微气候时序/病害分布/抗逆雷达 | monitor、首页天气 |

## 三、页面清单（对照参考图 8 屏）

| 参考图 | 页面 | 说明 |
|---|---|---|
| P1 首页 | `pages/home` | 沉浸式玉米田主视觉 + 四功能宫格 + 天气卡 + 最近识别 |
| P2 病害识别 | `pages/identify` | 单张/批量/多模型对比/Base64 四模式 + 四类病害示例图 |
| P3 识别结果 | `pages/result` | 原图+热力图双图、置信度、受损率环形图、病斑定位框 |
| P4 飞防决策 | `pages/spray` | 绿色处方横幅、推荐药剂、作业参数、处方详情 |
| P5 植保 AI 助手 | `pages/assistant` | 单页对话设计：欢迎态（欢迎气泡+快捷问题+最近会话浮层）⇄ 对话态同页切换；**真实流式输出**（delta/tool_call/truncated/done 全事件）+ 停止生成 + 会话恢复 + 重试 + 新对话 |
| P7 田间监测 | `pages/monitor` | 微气候折线/病害柱状/六维雷达（Canvas 2D 手绘，零依赖） |
| P8 识别历史 | `pages/history` | 分类筛选、详情回看（含热力图）、删除/清空二次确认、下拉刷新 |
| 附加 | `pages/mine` | 统计 + 服务状态 + 后端地址（TabBar 四入口需要） |

TabBar 为自定义组件（`custom-tab-bar`），iconpark 风格线性图标以 base64 SVG 运行时渲染，选中态品牌绿。

## 四、素材版权

- 叶片示例图来自本地数据集 `dataset/MCDD/data/test/`（Blight/Common_Rust/Gray_Leaf_Spot/Healthy 各一张）；主视觉来自 Wikimedia Commons（自由许可）：Cornfield Alps（玉米田+蓝天）
- 图标：iconpark 官方线性风格（base64 SVG 内置 `utils/icons.js`）。

## 五、已实现 / 待接入

**已实现（真实后端）**：图片选择/拍摄上传、单张与批量推理、Grad-CAM 展示、病斑框按百分比坐标叠加、受损率环形图、飞防处方与作业参数、SSE 流式问答（含联网检索状态、停止、重试、会话找回）、历史管理与删除、遥测图表。

**待接入（已留清晰封装与占位）**：
- 微气候逐日统计接口：柱状图近 7 日趋势目前由后端分布占比确定性估算，页面已标注「演示数据」；后端提供逐日统计后替换 `monitor.js drawBar()`。
- 多模型对比的逐模型置信度：当前展示单模型 4 类别概率分布（`probabilities`），后端开放多模型列表后可在对比模式轮询。
- 数据来源卡片结构化输出：SSE 目前提供检索词（来源 360/搜狗/百度），后端输出结构化来源链接后可展示原文入口。
- 真实天气 API：首页天气取自 `/screen/telemetry`（后端为示范田演示值）。
- 微信正式 AppID 与合法域名备案（上线前在公众平台配置 request 合法域名）。
