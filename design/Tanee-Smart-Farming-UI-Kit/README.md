# Tanee — Smart Farming App UI Kit（完整源码包）

> 来源：[Figma Community — [Freebie] Tanee - Smart Farming App UI Kit](https://www.figma.com/community/file/1589911798189831497/freebie-tanee-smart-farming-app-ui-kit)
> 作者：Nija Works（<https://www.nijaworks.com>）
> 整理时间：2026-10-22

这个文件夹里放的是这个免费 UI Kit 的**全部可导出内容**：原始切图、矢量图标、页面级 PNG 预览、完整的结构化设计数据（JSON），以及从设计里统计出来的设计令牌（Design Tokens）。

---

## 1. 目录结构

```
Tanee-Smart-Farming-UI-Kit/
├── Tanee-Smart-Farming-UI-Kit.fig   可编辑源文件（Figma 本地副本，50.6 MB）
├── png/      6 个页面级预览图（2388×1668，封面为 1920×1080）
├── raw/      12 个原始位图素材（封面/仪表盘/登录/注册/找回密码 的背景照片等）
├── svg/      65 个矢量图标（按页面分目录）
├── json/     2 个完整页面设计数据（节点树，含位置、尺寸、颜色、字体、布局）
├── tokens/   从上面 JSON 汇总出的设计令牌
└── preview.html  本地预览画廊（双击用浏览器打开）
```

总计 **87 个资源文件 + README 和预览页，共 89 个文件，约 107.5 MB**。

| 目录 | 文件数 | 大小 | 说明 |
|------|-------:|-----:|------|
| `.fig` | 1 | 50.6 MB | 可编辑源文件（Figma 本地副本） |
| `png/` | 6 | ~8.9 MB | 每个界面一张整页 PNG |
| `raw/` | 12 | ~45 MB | Figma 里原样上传的图片填充（JPEG/PNG） |
| `svg/` | 65 | ~93 KB | 矢量图标，可直接放进代码 |
| `json/` | 2 | 152 KB | 完整节点树（含全部文字与样式） |
| `tokens/` | 1 | 4.4 KB | 颜色/字体/圆角/阴影/间距统计 |

### png/

| 文件 | 对应界面 |
|------|----------|
| `00-Cover-Detail.jpg` | 社区封面图（1920×1080，实际为 JPEG） |
| `01-Greenhouse-Monitoring-Dashboard.png` | 温室监测仪表盘（主界面） |
| `02-Splash-Screen.png` | 启动页 |
| `03-Login-Empty.png` | 登录页（空状态） |
| `04-Forgot-Password-Empty.png` | 找回密码页（空状态） |
| `05-Signup-Empty.png` | 注册页（空状态） |

### raw/

各页面里作为图片填充（image fill）使用的原始位图，按页面分目录存放：

```
raw/cover/    image-1..4    (4 张)
raw/dashboard/ image-1..2   (2 张)
raw/login/    image-1..2    (2 张)
raw/forgot/   image-1..2    (2 张)
raw/signup/   image-1..2    (2 张)
```

### svg/

```
svg/cover/      3 个
svg/dashboard/ 20 个
svg/login/     18 个
svg/forgot/    11 个
svg/signup/    11 个
svg/splash/     2 个
```

> ⚠️ Figma 单次节点导出 SVG 有 **20 个/节点** 的上限，`dashboard` 正好取到 20 个，可能有个别装饰性矢量被截断。需要的图标在 JSON 里有完整的位置和颜色信息，也可以直接从 Figma 单独导出。

---

## 2. 五个界面

所有界面画板尺寸统一为 **1194 × 834**（横向平板/网页布局）。

| 界面 | 主要内容 |
|------|----------|
| **Greenhouse Monitoring Dashboard** | 温室监测主仪表盘：告警徽标（3 Alert）、4 个温湿度/土壤传感器卡片（PL-70T、PL-02J 等）、Spinach Garden 08 温室概览（ID、面积 200 m²、Weilburg, Germany）、日期时间、天气（24°C / Sunny / H:46°C L:52°C）、Plant Health 94% Good、趋势图与温室分区图。 |
| **Splash Screen** | 启动页：品牌字标 “Smart Farm” + 插画背景。 |
| **Login / Empty** | 登录页：主张 “Grow Smarter, Farm Better”、副文案、Email / Password 输入框、Remember me、Forgot Password?、Log in、Google / Apple 第三方登录、Sign up 引导。 |
| **Forgot Password / Empty** | 找回密码页：主张 “Real-Time Insights Access”、返回按钮、Email 输入、Send 按钮。 |
| **Sign up / Empty** | 注册页：主张 “Seamless Device Control”、Full Name / Email / Password / Confirm Password、Sign up、Log in 引导。 |

Getting Started 页另外包含 2 个画板：`Detail_1`（1920×1080，对应 `png/00-Cover-Detail.jpg`）和 `Information & License`（1208×2069）。授权页没有单独的渲染图，但它的全部文字内容都在 `json/getting-started.json` 里。

---

## 3. JSON 设计数据

两个文件的格式完全一致，是一棵**压缩键名**的节点树，根节点为：

```json
{
  "page": "🎨 Design",
  "id": "0:1",
  "keymap": { ... },
  "children": [ /* 顶层画板 */ ]
}
```

### 3.1 校验信息

| 文件 | 字符数 | 字节数 | djb2 哈希 | 顶层画板 |
|------|-------:|-------:|----------:|----------|
| `json/design-page.json` | 124,675 | 124,734 | `1119180056` | 5 |
| `json/getting-started.json` | 27,249 | 27,266 | `313780569` | 2 |

哈希算法（与生成脚本一致）：

```js
let h = 5381;
for (let i = 0; i < s.length; i++) h = ((h * 33) ^ s.charCodeAt(i)) >>> 0;
```

### 3.2 节点统计

| 页面 | 节点总数 | TEXT | INSTANCE | VECTOR | 顶层画板 |
|------|--------:|-----:|---------:|-------:|---------:|
| 🎨 Design | 496 | 139 | 98 | 77 | 5 |
| 👋🏻 Getting Started | 106 | 20 | 15 | 21 | 2 |

### 3.3 键名对照（keymap）

| 键 | 含义 | 键 | 含义 |
|----|------|----|------|
| `i` | id | `n` | name（图层名） |
| `t` | type（FRAME/TEXT/INSTANCE/…） | `ch` | children |
| `x` / `y` | 相对父级坐标 | `w` / `h` | 宽 / 高 |
| `vi` | visible=false 时才出现 | `op` | opacity |
| `bm` | blendMode | `mk` | isMask |
| `rt` | rotation | `c` | clipsContent |
| `f` | fills（填充） | `s` | strokes |
| `sw` / `sa` | 描边宽度 / 对齐 | `scp` / `sj` / `sd` / `sml` | 描边端点/连接/虚线/斜接 |
| `e` | effects（阴影、模糊） | `r` | cornerRadius |
| `rc` | 四角独立圆角 | `al` | autoLayout（模式、padding、gap、对齐、换行） |
| `la` / `lg` / `lp` | 布局对齐 / 伸缩 / 定位 | `co` | constraints |
| `tx` | characters（文字内容） | `fo` | fontName |
| `fs` / `lh` / `ls` | 字号 / 行高 / 字距 | `an` / `av` | 水平 / 垂直对齐 |
| `tc` / `td` / `tr` | 大小写 / 装饰线 / 自适应 | `mc` | mainComponent（实例主组件） |
| `dc` | description | `gs` / `gt` | 渐变 stops / transform |
| `sm` | scaleMode | `ih` / `it` / `sf` | 图片 hash / transform / 缩放 |
| `off` / `spr` | 阴影偏移 / 扩散 | | |

填充/描边的颜色一律是 `[r, g, b, a]` 数组（0–255，alpha 0–1），渐变额外带 `gs`（`[[位置,[r,g,b,a]], ...]`）和 `gt`。

> 说明：为了控制体积，**组件实例的变体属性（componentProperties）没有导出**；但每个 INSTANCE 都保留了完整的、已解析的子节点树（尺寸、文字覆盖、颜色都是最终渲染值），所以视觉信息是完整的。

---

## 4. 设计令牌（tokens/design-tokens.json）

从上面两个 JSON 全量统计得到，包含：颜色、渐变、字体、字号、行高、字距、圆角、效果、自动布局间距、节点类型计数。

### 主色板

| 色值 | 出现次数 | 用途 |
|------|--------:|------|
| `#FFFFFF` | 134 | 背景/卡片 |
| `#333333` | 90 | 主文字 |
| `#A4A4A4` | 52 | 次要文字 |
| `#ECECEC` | 27 | 分隔线/边框 |
| `#F4F4F4` | 20 | 浅底 |
| `#181B25` | 11 | 深底/深色文字 |
| `#17B26A` | 3 | 成功/主绿 |
| `#F9AD19` | 3 | 警告黄 |
| `#EB4335` | 1 | 错误红 |

主渐变：`#35C56E → #2E9055`（线性，出现 19 次，是品牌绿）。

### 字体

| 字体 | 出现次数 |
|------|--------:|
| Satoshi Medium | 81 |
| Satoshi Regular | 41 |
| Satoshi Bold | 20 |
| Inter Medium | 7 |
| Inter Regular | 6 |
| Plus Jakarta Sans SemiBold | 1 |

> Satoshi 是商业字体，需自行获取授权；免费替代可用 Inter / Manrope。

### 字号 / 行高 / 字距

- 常用字号：12 (65)、14 (40)、24 (14)、32 (8)、16 (7)、40 (7)
- 常用行高：160% (104)、140% (21)、16 px (10)
- 常用字距：-2% (133)

### 圆角

- `8` (61 次) 最常用，其次 `99999`（全圆胶囊，13 次）、`32` (7)、`2/4/12` (各 6)

### 效果

- `BACKGROUND_BLUR r=32` ×12（毛玻璃卡片）
- `DROP_SHADOW r=8 off=0,2` ×3
- `LAYER_BLUR r=300` ×2（背景光晕）

### 间距

- `gap 4` ×96、`gap 8` ×43、`gap 16` ×21，padding 以 `12`、`16` 为主 —— 4pt 栅格。

---

## 5. `.fig` 可编辑源文件

根目录下的 **`Tanee-Smart-Farming-UI-Kit.fig`**（50.6 MB）就是从 Figma 导出的本地副本，**这才是真正可编辑的完整源文件**——包含组件实例、自动布局、文字样式、颜色样式、效果样式（`shadow-xs` ~ `shadow-xl` 等）和全部原始图片。

打开方式：

1. Figma 桌面版或网页版，进入任意文件的编辑器；
2. 菜单 **文件 → 导入…**（或直接把 `.fig` 拖进 Figma 窗口）；
3. 选择这个 `.fig`，它会作为新文件出现在你的草稿箱里。

`.fig` 本身是一个 ZIP 容器：

```
canvas.fig       1.5 MB   画布数据（fig-kiwi 二进制格式）
thumbnail.png    34 KB    缩略图
meta.json        368 B    元数据
images/          37 张   全部嵌入图片
```

已验证：`raw/` 下的 **12 张图片全部包含在容器里，字节数逐一相等**（12448 / 28960 / 116256 / 254878 / 272082 / 289029 / 295184 / 4,870,997 / 9,061,208 / 9,298,431 / 9,781,750 / 10,967,911），其余 25 张是文件内其他位置的图片填充；`meta.json` 的 `render_coordinates`（x=-4123, y=123, w=3233, h=2069）也与 JSON 里 `Detail_1`（-2810,123）和 `Information & License`（-4123,123）的坐标完全吻合——确认这份 `.fig` 就是本包数据来源的那份文件。

社区页面上作者还提供了 **“Get Full Version Here”**（完整版付费，本免费版只含上面这 5 个界面 + Getting Started 说明页）。

> 注意：`🧩 Design System`、`↳ Style Guide`、`↳ Component`、`↳ Icon`、`↳ Asset` 这 5 个页面在免费版里是**空的**（没有组件主件），但文件里的样式定义是完整的，实例也能正常渲染。

---

## 6. 授权（License）

来自作品内的 `Information & License` 页面：

| ✅ 允许 | ❌ 禁止 |
|--------|--------|
| 用于个人或商业项目 | 在其他平台转售或重新分发该文件 |
| 为自己的设计修改和改编 | 打包进付费 UI Kit 或素材市场 |
| 用于客户项目（署名可选） | |

版权：`© 2025 nijaworks. All rights reserved.` — 作者 **Nija Works**（<https://www.nijaworks.com>）。
本包仅做整理与格式转换，不改变上述授权条款。如果你要把这套设计公开发布或再分发，请先联系作者。

---

## 7. 预览

双击 `preview.html` 即可在浏览器里查看全部界面和素材统计（纯本地文件，不联网）。
