# 玉米叶部病斑多尺度自适应感知与飞防决策系统

面向复杂大田环境（强日光直射、雨露水珠折射、泥水溅渍与杂草重叠）的玉米病害智能诊断与无人机精准飞防决策大屏系统。

---

## 🌟 系统核心特性与架构

1. **真实深度模型与 GPU 推理引擎**
   - 搭载 **ResNet50-CBAM**（卷积块空间与通道注意力机制）及 **MobileNetV3** 轻量化骨干网络；
   - 运行于本地 **NVIDIA RTX 4050 Laptop GPU (CUDA 11.8)**，单张图片边缘推理耗时仅 **14ms** 左右；
   - 覆盖 4 类真实大田玉米叶片：**玉米大斑病 (Northern Leaf Blight)**、**玉米普通锈病 (Common Corn Rust)**、**玉米灰斑病 (Gray Leaf Spot)**、**健康植株 (Healthy)**。

2. **多尺度病斑定位与 Grad-CAM 可视化**
   - **Grad-CAM 注意力焦点热力图**：真实反向梯度计算，直观呈现模型关注的病斑区域；
   - **自适应边界定位框 (Bounding Box)**：基于热力图高激活区域自动提取病斑坐标与范围并叠加标注；
   - **受损率与等级评估**：计算叶面积受损率（damageRate），判定发病等级（轻度 / 中度 / 重度 / 危急）。

3. **无人机变量精准施药指导单**
   - 结合病害知识库与发病程度，自适应生成大田无人机飞防处方；
   - 推荐对路药剂（如嘧菌酯、戊唑醇、氟硅唑）及喷雾参数（推荐机型如大疆 T50/T60、亩施液量、雾滴粒径、作业高度与速度）。

4. **Agnes-3.0-Flash 驱动的植保专家智能大模型**
   - 接入 **Agnes-3.0-Flash** 大语言模型（`https://apihub.agnes-ai.cn/v1`）；
   - **打字机流式输出 (Server-Sent Events / SSE)**：采用开源标准的 `fetch` + `ReadableStream` 机制，回答逐字平滑吐出，彻底告别整块等待的顿挫感；
   - **智能联网搜索工具调用 (Tool Calling)**：原生接入 `web_search` 工具。当农户或机手提问涉及实时玉米市场收购价格、期货行情、突发灾情政策等超出模型预训练数据的内容时，大模型自主发起 `tool_call` 实时联网搜索互联网信息并融合输出；
   - **多源感知深度融合**：将前端当前 ResNet50-CBAM 识别的病害名称、置信度、受损率、侵染级别、飞防处方及示范区 24h 微气候（温湿度气象）作为上下文自动注入大模型 Prompt；
   - **多轮会话记忆**：支持多轮上下文连贯问答；
   - **智能双轨容错**：在网络出现抖动或极端断网时，自动无缝降级至本地权威玉米植保专家知识库，确保大屏演示 100% 高可用。

5. **现代化响应式大屏系统 (Vue 3 + Vite + ECharts)**
   - **彻底剔除所有内置 mock 假数据**，所有数据 100% 由后端 API 驱动；
   - 示范区 24h 微气候时序折线图（温湿度光照）与病害发生频次分布统计；
   - 复杂田间抗逆六维雷达能力评估图；
   - 优化按钮交互，界面干净利落。

---

## ⚙️ 环境配置（首次运行必读）

本仓库**不包含**数据集、模型权重与真实密钥，需在本地补齐：

```bash
# 1. 复制配置模板
cd model/corn_disease_system_20261021/configs
cp config.example.yaml config.yaml

# 2. 配置大模型密钥（二选一）
#    方式 A：写入 config.yaml 的 llm.api_key
#    方式 B：设置环境变量（推荐，config.yaml 中 api_key 留空即可）
export AGNES_API_KEY="你的密钥"        # Windows: set AGNES_API_KEY=...
```

需要自行准备的资源：

| 资源 | 位置 | 说明 |
|---|---|---|
| 模型权重 | `model/corn_disease_system_20261021/outputs/checkpoints/*.pth` | 未入库，需训练产出或自行放置 |
| 数据集 | `dataset/` | MCDD 玉米病害数据集，按 `configs` 中 `data.sources` 配置路径 |

> 仓库已通过 `.gitignore` 排除：`configs/config.yaml`（含密钥）、`*.pth` 权重、`dataset/`、`node_modules/`、`dist/`。

---

## 🚀 一键启动

在项目根目录下，双击运行：

```bash
start_all.bat
```

脚本将自动：
1. 启动后端推理引擎服务（`http://localhost:8010`，API 文档：`http://localhost:8010/docs`）；
2. 启动前端大屏工作台（`http://localhost:5173`）；
3. 自动在浏览器中打开大屏系统。

---

## 🔐 登录认证

大屏与全部业务接口（`/screen/*`、`/predict*` 等）默认需要登录，未登录会自动跳转登录页并记住原访问地址。

**演示账号**（首次启动自动创建，登录页可一键填充）：

| 账号 | 密码 | 角色 |
|---|---|---|
| `admin` | `corn@2026` | 系统管理员 |
| `agronomist` | `field@2026` | 农艺师 |

登录页也支持自助注册（右下角「立即注册」）。

**实现要点**（详见 `model/corn_disease_system_20261021/app/auth.py`）：

- 密码用标准库 `pbkdf2_hmac(sha256, 210000 轮)` 加盐哈希，不引第三方加密库；
- 令牌为 HMAC-SHA256 自签的三段式（等价于 HS256 JWT），默认 12 小时，勾选「记住我」后 7 天；
- 服务端用 `revoked_tokens` 表记录已注销令牌，退出登录后立即失效；
- 同一账号连续 5 次密码错误锁定 5 分钟，账号不存在与密码错误返回同一提示，避免枚举账号；
- 前端令牌存 `localStorage`，axios 拦截器统一注入 `Authorization: Bearer`，遇 401 自动清理并跳登录页；
- 用户数据落在 `history/auth.db`、签名密钥落在 `history/auth_secret.key`，该目录已在 `.gitignore` 中排除。

**可配置环境变量**：

| 变量 | 作用 |
|---|---|
| `CORN_AUTH_SECRET` | 固定令牌签名密钥（多实例部署时必须一致；不设则自动生成并落盘） |
| `CORN_AUTH_ADMIN_PASSWORD` | 首次初始化时 `admin` 的密码 |
| `CORN_AUTH_ALLOW_REGISTER` | 设为 `0` 关闭自助注册 |

> 首次部署后请立即修改默认密码（或通过 `CORN_AUTH_ADMIN_PASSWORD` 指定），生产环境建议配合 HTTPS 使用。

---

## 📁 目录结构

```text
sjzprogram/
├── dataset/                  # MCDD 玉米病害多模态数据集（train / test 图片与标注 CSV）
├── model/                    # 模型工程与权重目录
│   └── corn_disease_system_20261021/
│       ├── app/
│       │   ├── api.py        # FastAPI 后端服务核心入口
│       │   └── bigscreen_api.py # 大屏专属 API（样本库、Grad-CAM 推理、BBox、问答、遥测）
│       ├── configs/          # 系统配置文件 (config.yaml)
│       ├── outputs/          # 训练产物与预训练权重 (checkpoints/*.pth)
│       ├── scripts/          # 测试与验证脚本
│       └── src/              # 模型定义、Grad-CAM、知识库与预测器
├── frontend/                 # Vue 3 前端大屏工程
│   ├── src/views/bigScreen/Layout.vue # 诊断大屏主工作台（已完全接入后端）
│   └── vite.config.mjs       # Vite 配置（含后端代理）
├── start_all.bat             # 全栈一键启动脚本
├── run_backend.bat           # 后端单启动脚本
├── run_frontend.bat          # 前端单启动脚本
└── README.md                 # 项目运行说明文档
```
