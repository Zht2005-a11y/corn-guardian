<template>
  <div class="tanee-app-root">
    <!-- Scalable Artboard Wrapper (Auto-fits 1194x834 artboard to screen) -->
    <div
      class="tanee-scalable-viewport"
      :style="{ transform: `scale(${scaleFactor})`, width: boardWidth + 'px' }"
    >
      <div class="tanee-dashboard-artboard" :class="themeClass">
        <!-- ════════════════════ 1. SIDEBAR (103px × 834px) ════════════════════ -->
        <aside class="tanee-sidebar">
          <!-- Top Brand Logo -->
          <div class="brand-frame">
            <div class="brand-logo-circle" @click="activeNav = 'home'" title="玉米叶部病斑多尺度自适应感知与飞防决策系统">
              <img src="/tanee/svg/dashboard/icon-9.svg" alt="Tanee Logo" class="brand-union-icon"/>
            </div>
          </div>

          <!-- Upper Menu Navigation (4 icons: Home, Tower, Chart, Map) -->
          <div class="menu-container upper">
            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'home' }"
              @click="activeNav = 'home'; showDiagWorkstation = false"
              title="总览仪表盘"
            >
              <img src="/tanee/svg/dashboard/icon-16.svg" alt="Home" class="nav-svg-icon white-filter"/>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'sensors' }"
              @click="activeNav = 'sensors'; activeModal = 'device'"
              title="物联网传感器"
            >
              <!-- Computer Tower / Server Icon -->
              <svg class="nav-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                <rect x="5" y="2" width="10" height="16" rx="2"/>
                <line x1="8" y1="5" x2="12" y2="5"/>
                <line x1="8" y1="8" x2="12" y2="8"/>
                <circle cx="10" cy="14" r="1" fill="#333333"/>
              </svg>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'charts' }"
              @click="activeNav = 'charts'; activeModal = 'telemetry'"
              title="遥测数据分析"
            >
              <img src="/tanee/svg/dashboard/icon-15.svg" alt="Charts" class="nav-svg-icon"/>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'map' }"
              @click="activeNav = 'map'; showDiagWorkstation = false"
              title="田间地块地图"
            >
              <!-- Map Trifold Icon -->
              <svg class="nav-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                <path d="M2.5 4.5L7.5 2.5L12.5 4.5L17.5 2.5V15.5L12.5 17.5L7.5 15.5L2.5 17.5V4.5Z"/>
                <line x1="7.5" y1="2.5" x2="7.5" y2="15.5"/>
                <line x1="12.5" y1="4.5" x2="12.5" y2="17.5"/>
              </svg>
            </button>
          </div>

          <!-- Lower Menu Navigation (Pinned to bottom: Theme, User) -->
          <div class="menu-container lower">
            <div class="theme-menu-wrap">
              <button
                class="nav-item-btn"
                :class="{ active: themeMenuOpen }"
                @click.stop="themeMenuOpen = !themeMenuOpen"
                title="切换界面配色"
              >
                <!-- Sun / Brightness Icon -->
                <svg class="nav-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                  <circle cx="10" cy="10" r="3"/>
                  <path d="M10 2V4M10 16V18M2 10H4M16 10H18M4.34 4.34L5.76 5.76M14.24 14.24L15.66 15.66M4.34 15.66L5.76 14.24M14.24 5.76L15.66 4.34"/>
                </svg>
              </button>

              <transition name="pop-fade">
                <div v-if="themeMenuOpen" class="theme-popover">
                  <h6>界面配色</h6>
                  <button
                    v-for="t in themeOptions"
                    :key="t.id"
                    class="theme-option-row"
                    :class="{ active: themeMode === t.id }"
                    @click="setTheme(t.id)"
                  >
                    <span class="theme-swatch" :class="'sw-' + t.id"></span>
                    <span class="theme-name">{{ t.name }}</span>
                    <svg v-if="themeMode === t.id" class="theme-check" viewBox="0 0 16 16" fill="none" stroke="#17B26A" stroke-width="2.2">
                      <path d="M3.5 8.5L6.5 11.5L12.5 5.5"/>
                    </svg>
                  </button>
                </div>
              </transition>
              <div v-if="themeMenuOpen" class="theme-popover-mask" @click="themeMenuOpen = false"></div>
            </div>

            <button class="nav-item-btn" @click="activeModal = 'profile'" title="个人中心">
              <img src="/tanee/svg/dashboard/icon-20.svg" alt="User Profile" class="nav-svg-icon"/>
            </button>
          </div>
        </aside>

        <!-- ════════════════════ 2. BODY (1091px × 834px) ════════════════════ -->
        <main class="tanee-body">
          <!-- 2.1 Header (1091px × 76px) -->
          <header class="tanee-header">
            <h1 class="header-title">玉米叶部病斑多尺度自适应感知与飞防决策系统</h1>

            <div class="header-right-tools">
              <!-- 3 Alert Button (Figma Exact: 110x32, gradient #666 to #1a1a1a, radius 8px) -->
              <button class="alerts-pill-btn" @click="activeModal = 'alerts'" title="农场告警">
                <div class="notif-box">
                  <img src="/tanee/svg/dashboard/icon-7.svg" alt="告警" class="bell-svg"/>
                </div>
                <span class="alerts-txt">3 条告警</span>
                <svg class="arrow-up-right-svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 12L12 4M12 4H6M12 4V10"/>
                </svg>
              </button>

              <!-- Sector Selector (Figma Exact: text 'Sector:' + pill 'Spinach Garden 08 ▾') -->
              <div class="sector-selector-wrap">
                <span class="sector-label-txt">分区：</span>
                <button class="sector-dropdown-btn" @click="toggleSector">
                  <span class="sector-name-txt">{{ currentSector }}</span>
                  <svg class="caret-down-svg" viewBox="0 0 16 16" fill="none" stroke="#333333" stroke-width="2">
                    <path d="M4 6L8 10L12 6"/>
                  </svg>
                </button>
              </div>
            </div>
          </header>

          <!-- 2.2 Main Content (1091px × 758px, 16px Padding, 2 Columns) -->
          <div class="main-content-layout">
            <!-- ──────── LEFT COLUMN (525.5px × 726px): 核心功能 · 图片导入与智能检测工作台 ──────── -->
            <div class="content-column left-col">
              <!-- Card 1: 视觉感知与图像导入交互工作台 (525.5px × 446px) -->
              <div class="ai-detection-workbench">
                <!-- Workbench Header -->
                <div class="wb-header-bar">
                  <div class="wb-title-group">
                    <div class="wb-title-icon-box">
                      <svg viewBox="0 0 20 20" fill="none" stroke="#17B26A" stroke-width="2">
                        <circle cx="10" cy="10" r="7"/>
                        <path d="M10 6v8M6 10h8"/>
                      </svg>
                    </div>
                    <div class="wb-title-text-wrap">
                      <h3 class="wb-main-title">玉米叶部病斑多尺度自适应感知</h3>
                      <span class="wb-model-tag">ResNet50-CBAM · 注意力机制</span>
                    </div>
                  </div>

                  <div class="wb-header-actions">
                    <div class="wb-status-badge" :class="{ detecting: isDetecting, waiting: !isDetecting && !isDetected }">
                      <span class="status-pulse-dot"></span>
                      <span class="status-txt">{{ isDetecting ? 'AI 推理计算中...' : (isDetected ? `就绪 · ${inferenceSpeed}` : '待诊断 · 请点击开始诊断') }}</span>
                    </div>
                    <!-- 隐藏的文件上传 Input -->
                    <input
                      type="file"
                      ref="fileInputRef"
                      class="hidden-file-input"
                      accept="image/*"
                      @change="handleFileUpload"
                    />
                    <button class="wb-upload-btn" @click="triggerUpload" title="导入本地叶片图片">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M8 10V2M8 2L5 5M8 2L11 5"/>
                        <path d="M2 10v3a1 1 0 001 1h10a1 1 0 001-1v-3"/>
                      </svg>
                      <span>导入图片</span>
                    </button>
                  </div>
                </div>

                <!-- Central Visual Inspection Canvas -->
                <div
                  class="detection-canvas-container"
                  @dragover.prevent
                  @drop="handleFileDrop"
                  :title="isDetecting ? '正在推理...' : '支持拖拽本地图片直接导入'"
                >
                  <!-- 紧凑包裹图像的画布舞台：确保多尺度标注框与叶片真实显示区域 1:1 精确对齐 -->
                  <div class="canvas-image-stage">
                    <!-- Raw Leaf Image -->
                    <img
                      :src="previewUrl"
                      alt="Corn Leaf"
                      class="leaf-raw-image"
                      :class="{ dimmed: showHeatmap && currentSample?.gradcam_base64 }"
                    />

                    <!-- Grad-CAM Attention Heatmap Layer -->
                    <img
                      v-if="showHeatmap && currentSample?.gradcam_base64"
                      :src="currentSample.gradcam_base64"
                      alt="Grad-CAM Heatmap"
                      class="leaf-gradcam-layer"
                    />

                    <!-- Multi-Scale Lesion Bounding Boxes -->
                    <div v-if="showBBoxes && currentSample?.boxes?.length" class="leaf-bbox-overlay">
                      <div
                        v-for="(box, idx) in currentSample.boxes"
                        :key="idx"
                        class="leaf-single-box"
                        :style="{ left: box.x + '%', top: box.y + '%', width: box.w + '%', height: box.h + '%' }"
                      >
                        <span class="bbox-label">{{ box.label || '病斑' }} {{ box.conf ? `${box.conf}` : '' }}</span>
                      </div>
                    </div>

                    <!-- AI Laser Scanline (Active while detecting) -->
                    <div v-if="isDetecting" class="ai-scanline-laser">
                      <div class="laser-beam"></div>
                    </div>
                  </div>

                  <!-- Canvas Top Overlay Chips -->
                  <div class="canvas-top-overlay">
                    <span class="canvas-filename-chip">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                        <path d="M3 2h7l4 4v8a1 1 0 01-1 1H3a1 1 0 01-1-1V3a1 1 0 011-1z"/>
                      </svg>
                      {{ currentSample?.name || '典型样本' }}
                    </span>
                    <span v-if="isDetected && currentSample?.confidence" class="canvas-conf-chip">
                      置信度: {{ currentSample.confidence }}%
                    </span>
                  </div>

                  <!-- Floating Canvas Bottom Toolbar -->
                  <div class="canvas-floating-toolbar">
                    <div class="view-layers-group">
                      <button
                        class="layer-toggle-btn"
                        :class="{ active: !showHeatmap && !showBBoxes }"
                        @click="showHeatmap = false; showBBoxes = false"
                        title="只看原始叶片"
                      >
                        原图
                      </button>
                      <button
                        class="layer-toggle-btn"
                        :class="{ active: showBBoxes }"
                        @click="showBBoxes = !showBBoxes"
                        title="切换多尺度病斑检测框"
                      >
                        病斑框
                      </button>
                      <button
                        class="layer-toggle-btn"
                        :class="{ active: showHeatmap }"
                        @click="showHeatmap = !showHeatmap"
                        title="切换 Grad-CAM 自适应热力图"
                      >
                        热力图
                      </button>
                    </div>

                    <button
                      class="canvas-action-btn"
                      :class="{ 'pulse-highlight': !isDetected && !isDetecting }"
                      @click="runDetect"
                      :disabled="isDetecting"
                      title="触发 AI 多尺度检测"
                    >
                      <svg v-if="!isDetecting" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M8 1L9.4 6.6L15 8L9.4 9.4L8 15L6.6 9.4L1 8L6.6 6.6L8 1Z"/>
                      </svg>
                      <span class="btn-spinner" v-else></span>
                      <span>{{ isDetecting ? '诊断中...' : '开始诊断' }}</span>
                    </button>
                  </div>
                </div>

                <!-- Bottom Strip: Preset Samples Selector -->
                <div class="wb-samples-footer">
                  <span class="preset-label-txt">典型样本库:</span>
                  <div class="preset-samples-scroll">
                    <button
                      v-for="s in presetSamples"
                      :key="s.id"
                      class="preset-sample-pill"
                      :class="{ active: currentSampleId === s.id }"
                      @click="selectPreset(s)"
                    >
                      <img :src="s.imgData" class="pill-thumb-img"/>
                      <span class="pill-sample-name">{{ s.name }}</span>
                    </button>
                  </div>
                  <button class="quick-cam-btn" @click="triggerCameraCapture" title="从当前航拍轮播抓拍">
                    <img src="/tanee/svg/dashboard/icon-3.svg" alt="Capture" class="quick-cam-icon"/>
                    <span>抓拍导入</span>
                  </button>
                </div>
              </div>

              <!-- Card 2: 诊断评估与飞防决策结果面板 (525.5px × 272px) -->
              <div class="diagnosis-decision-card">
                <!-- Header: Disease Title + Severity Tag -->
                <div class="dd-header-row">
                  <div class="dd-disease-info">
                    <h4 class="dd-disease-title">{{ isDetected ? (currentSample?.diseaseName || '玉米大斑病 (Northern Corn Leaf Blight)') : (isDetecting ? 'AI 正在推理中...' : '待检测样本（等待诊断）') }}</h4>
                    <span class="dd-pathogen-txt">{{ isDetected ? (currentSample?.pathogen || '病原菌：真菌，大斑凸脐蠕孢 (Exserohilum turcicum)') : (isDetecting ? '深度卷积注意力网络正在提取叶片表征特征...' : '尚未执行 AI 推理，请点击上方【开始诊断】按钮') }}</span>
                  </div>
                  <div class="dd-severity-badge" :style="{ backgroundColor: isDetected ? (currentSample?.color || '#e28557') : (isDetecting ? '#3b82f6' : '#667085') }">
                    {{ isDetected ? (currentSample?.severity || '中度 (II 级扩展期)') : (isDetecting ? '推理中...' : '待诊断') }}
                  </div>
                </div>

                <!-- Two-Column Grid: Metrics & Aerial Defense Prescription -->
                <div class="dd-content-grid">
                  <!-- Left: Multi-scale Quantitative Metrics -->
                  <div class="dd-metrics-subcol">
                    <div class="dd-stat-tile">
                      <div class="stat-top-row">
                        <span class="stat-lbl">识别置信度</span>
                        <strong class="stat-val text-green">{{ isDetected ? `${currentSample?.confidence ?? 0}%` : '--' }}</strong>
                      </div>
                      <div class="stat-progress-line">
                        <div class="stat-progress-bar" :style="{ width: isDetected ? `${currentSample?.confidence ?? 0}%` : '0%' }"></div>
                      </div>
                    </div>

                    <div class="dd-stat-tile">
                      <div class="stat-top-row">
                        <span class="stat-lbl">受损叶面积比率</span>
                        <strong class="stat-val text-orange">{{ isDetected ? `${currentSample?.damageRate ?? 0}%` : '--' }}</strong>
                      </div>
                      <div class="stat-progress-line">
                        <div class="stat-progress-bar orange" :style="{ width: isDetected ? `${currentSample?.damageRate ?? 0}%` : '0%' }"></div>
                      </div>
                    </div>

                    <div class="dd-stat-tile">
                      <div class="stat-top-row">
                        <span class="stat-lbl">感知模型</span>
                        <strong class="stat-val-sm">ResNet50-CBAM</strong>
                      </div>
                    </div>

                    <div class="dd-stat-tile">
                      <div class="stat-top-row">
                        <span class="stat-lbl">推理延迟</span>
                        <strong class="stat-val-sm">{{ isDetected ? (inferenceSpeed || '14.2ms') : '--' }}</strong>
                      </div>
                    </div>
                  </div>

                  <!-- Right: UAV Aerial Defense Prescription -->
                  <div class="dd-flight-subcol">
                    <div class="flight-head-row">
                      <span class="flight-tag-icon">🚁 飞防作业决策与施药处方</span>
                    </div>

                    <p class="flight-prescription-txt" :class="{ 'waiting-txt': !isDetected }">
                      {{
                        isDetected
                          ? (currentSample?.prescription || '选用 40% 氟硅唑·多菌灵可湿性粉剂 1000倍液 或 苯醚甲环唑·嘧菌酯，利用大田植保无人机实施傍晚超低空微滴变量精准喷雾。')
                          : (isDetecting
                              ? '正在结合病斑注意力多尺度特征评估施药剂量与无人机航行参数...'
                              : '图片已成功载入。请点击上方【开始诊断】按钮，系统将调用 ResNet50-CBAM 模型进行病斑多尺度定位与无人机处方生成。')
                      }}
                    </p>

                    <!-- Drone Parameter Grid -->
                    <div class="drone-params-row">
                      <div class="d-param-item">
                        <span class="dp-k">推荐机型</span>
                        <span class="dp-v">{{ isDetected ? (currentSample?.droneParams?.model || '大疆 T50/T60') : '--' }}</span>
                      </div>
                      <div class="d-param-item">
                        <span class="dp-k">亩喷施量</span>
                        <span class="dp-v">{{ isDetected ? (currentSample?.droneParams?.volume || '1.6 L/亩') : '--' }}</span>
                      </div>
                      <div class="d-param-item">
                        <span class="dp-k">雾滴粒径</span>
                        <span class="dp-v">{{ isDetected ? (currentSample?.droneParams?.droplet_size || currentSample?.droneParams?.dropletSize || '135 μm') : '--' }}</span>
                      </div>
                      <div class="d-param-item">
                        <span class="dp-k">作业航高</span>
                        <span class="dp-v">{{ isDetected ? (currentSample?.droneParams?.flight_height || currentSample?.droneParams?.altitude || '2.2 米') : '--' }}</span>
                      </div>
                      <div class="d-param-item">
                        <span class="dp-k">航行速度</span>
                        <span class="dp-v">{{ isDetected ? (currentSample?.droneParams?.speed || '5.0 m/s') : '--' }}</span>
                      </div>
                    </div>

                    <!-- Weather Flight Suitability Notice -->
                    <div class="flight-weather-notice" :class="{ 'notice-waiting': !isDetected }">
                      <span class="check-icon">{{ isDetected ? '✓' : 'ℹ' }}</span>
                      <span>{{ isDetected ? '当前风速 2m/s、温度 19°C 满足低空飞防窗口，无漂移药害风险' : '待诊断完成后，系统将根据病斑受损率与气象窗口生成施药决策' }}</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            <!-- ──────── RIGHT COLUMN (525.5px × 726px): 原左侧组件 (天气/地块 + 6大指标) + 轮播图 ──────── -->
            <div class="content-column right-col-reordered">
              <!-- Top Row: Weather & Plot Card (258.75px) + Carousel Live Box (258.75px) -->
              <div class="weather-carousel-row">
                <!-- Weather & Plot Card -->
                <div class="weather-plot-card" @click="activeModal = 'telemetry'">
                  <!-- Location & Time Bar -->
                  <div class="wp-top-bar">
                    <div class="wp-loc-tag">
                      <svg class="pin-svg" viewBox="0 0 16 16" fill="none" stroke="#333333" stroke-width="2">
                        <path d="M8 14C8 14 13 9.5 13 6C13 3.23858 10.7614 1 8 1C5.23858 1 3 3.23858 3 6C3 9.5 8 14 8 14Z"/>
                        <circle cx="8" cy="6" r="2" fill="#333333"/>
                      </svg>
                      <span class="loc-text">德国 · 魏尔堡</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow" @click.stop="activeModal = 'telemetry'">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>

                  <div class="wp-datetime-str">2024年9月10日 周二 09:37</div>

                  <!-- Big Temperature & Status -->
                  <div class="wp-temp-center">
                    <div class="temperature-big">24°C</div>
                    <div class="weather-inline-row">
                      <div class="sun-icon-box">
                        <svg viewBox="0 0 24 24" fill="none">
                          <circle cx="12" cy="12" r="5" fill="#F1CB1D"/>
                          <path d="M12 2v2m0 16v2M2 12h2m16 0h2M4.93 4.93l1.41 1.41m11.32 11.32l1.41 1.41M4.93 19.07l1.41-1.41m11.32-11.32l1.41-1.41" stroke="#F1CB1D" stroke-width="2.5" stroke-linecap="round"/>
                        </svg>
                      </div>
                      <span class="weather-status-txt">晴</span>
                      <span class="hl-range-txt">46°C / 52°C</span>
                    </div>
                  </div>

                  <!-- Mini Plot Sector Info Box -->
                  <div class="wp-plot-pill">
                    <div class="wp-plot-head">
                      <span class="plot-name">{{ currentSector }}</span>
                      <span class="plot-status-dot">● 遥测在线</span>
                    </div>
                    <div class="wp-plot-meta">
                      <span>编号: <strong>PL-02J</strong></span>
                      <span>面积: <strong>200 m²</strong></span>
                    </div>
                  </div>
                </div>

                <!-- Camera Live Carousel Card (Exact Original) -->
                <div class="camera-live-box" @mouseenter="pauseCarousel" @mouseleave="resumeCarousel">
                  <!-- 自动轮播画面层（横向滑动切换） -->
                  <div class="cam-carousel-stage">
                    <div
                      ref="trackRef"
                      class="cam-slide-track"
                      :class="{ 'no-anim': noTransition }"
                      :style="{ transform: `translateX(-${trackPos * 100}%)` }"
                    >
                      <img
                        v-for="feed in cameraFeeds"
                        :key="feed.src"
                        :src="feed.src"
                        :alt="feed.name"
                        class="camera-bg-image"
                      />
                      <!-- 尾部首帧克隆：末张正向滑入后瞬间归零，实现无缝循环 -->
                      <img :src="cameraFeeds[0].src" :alt="cameraFeeds[0].name" class="camera-bg-image" aria-hidden="true"/>
                    </div>
                  </div>

                  <!-- Gradient Shading Overlays -->
                  <div class="camera-shade top-shade"></div>
                  <div class="camera-shade bottom-shade"></div>

                  <!-- Top Overlay: Signal icon + Camera 1 + Arrow button -->
                  <div class="cam-overlay-row top-row">
                    <div class="cam-title-badge">
                      <svg class="cam-signal-icon" viewBox="0 0 16 16" fill="currentColor">
                        <path d="M1 11h2v3H1zM5 8h2v6H5zM9 5h2v9H9zM13 2h2v12h-2z"/>
                      </svg>
                      <span class="cam-label-txt">{{ cameraFeeds[cameraIndex].name }}</span>
                    </div>
                    <button class="cam-frosted-btn" @click="activeModal = 'telemetry'" title="查看遥测与画面">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>

                  <!-- Bottom Overlay: 1/4 and 4 square frosted buttons (◀, 📷, 🔔, ▶) -->
                  <div class="cam-overlay-row bottom-row">
                    <span class="cam-counter-txt">{{ cameraIndex + 1 }}/{{ cameraFeeds.length }}</span>
                    <div class="cam-dots">
                      <span
                        v-for="(f, i) in cameraFeeds"
                        :key="'dot-' + i"
                        class="cam-dot"
                        :class="{ active: i === cameraIndex }"
                        @click="cameraGo(i)"
                      ></span>
                    </div>
                    <div class="cam-controls-group">
                      <button class="cam-square-btn" @click="cameraPrev" title="上一画面">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M10 12L6 8L10 4"/>
                        </svg>
                      </button>
                      <button class="cam-square-btn" @click="triggerCameraCapture" title="抓拍并推理">
                        <img src="/tanee/svg/dashboard/icon-3.svg" alt="Capture" class="cam-btn-svg"/>
                      </button>
                      <button class="cam-square-btn" @click="activeModal = 'alerts'" title="查看告警">
                        <img src="/tanee/svg/dashboard/icon-7.svg" alt="Alerts" class="cam-btn-svg"/>
                      </button>
                      <button class="cam-square-btn" @click="cameraNext" title="下一画面">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                          <path d="M6 12L10 8L6 4"/>
                        </svg>
                      </button>
                    </div>
                  </div>
                </div>
              </div>

              <!-- Bottom Row: Metrics Matrix (525.5px × 470px, 2 Rows × 3 Columns) -->
              <div class="metrics-cards-grid">
                <!-- Card 1: Plant Health (Emerald Green Gradient #35C56E -> #2E9055) -->
                <div class="metric-card plant-health-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <img src="/tanee/svg/dashboard/icon-5.svg" alt="Plant Health" class="m-svg-icon white-svg"/>
                      <span class="m-label white-txt">植株健康</span>
                    </div>
                    <button class="m-corner-arrow-btn frosted-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num white-txt">{{ currentSample && isDetected ? Math.max(10, Math.round(100 - currentSample.damageRate)) : 94 }}</span>
                      <span class="val-unit white-txt">%</span>
                    </div>
                    <div class="status-pill-white">
                      <span class="status-pill-txt">良好</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc white-txt">作物长势旺盛，健康状态优异</p>
                </div>

                <!-- Card 2: Wind (Fills: #FFFFFF) -->
                <div class="metric-card default-metric-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <img src="/tanee/svg/dashboard/icon-14.svg" alt="Wind" class="m-svg-icon"/>
                      <span class="m-label dark-txt">风速</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num dark-txt">2</span>
                      <span class="val-unit muted-txt">m/s</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">请保持温室内空气充分流通</p>
                </div>

                <!-- Card 3: Temperature (Fills: #FFFFFF) -->
                <div class="metric-card default-metric-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <img src="/tanee/svg/dashboard/icon-13.svg" alt="Temperature" class="m-svg-icon"/>
                      <span class="m-label dark-txt">温度</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num dark-txt">19</span>
                      <span class="val-unit muted-txt">°C</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">建议稳定维持在 15°C 至 20°C</p>
                </div>

                <!-- Card 4: pH Level (Fills: #FFFFFF) -->
                <div class="metric-card default-metric-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <svg class="m-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                        <circle cx="10" cy="10" r="7"/>
                        <path d="M7 8V12M10 8V12M13 8V12M7 10H13"/>
                      </svg>
                      <span class="m-label dark-txt">pH 值</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num dark-txt">7.6</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">可施加酸性堆肥平衡 pH 值</p>
                </div>

                <!-- Card 5: Humidity (Fills: #FFFFFF) -->
                <div class="metric-card default-metric-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <svg class="m-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                        <path d="M10 3C10 3 4.5 9 4.5 13C4.5 16.0376 6.96243 18.5 10 18.5C13.0376 18.5 15.5 16.0376 15.5 13C15.5 9 10 3 10 3Z"/>
                      </svg>
                      <span class="m-label dark-txt">空气湿度</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num dark-txt">82</span>
                      <span class="val-unit muted-txt">%</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">湿度适宜，可有效抑制霉菌滋生</p>
                </div>

                <!-- Card 6: Soil Moisture (Fills: #FFFFFF) -->
                <div class="metric-card default-metric-card" @click="activeModal = 'telemetry'">
                  <div class="m-card-top">
                    <div class="m-title-flex">
                      <svg class="m-svg-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
                        <path d="M3 6C4.5 5 6.5 5 8 6C9.5 7 11.5 7 13 6C14.5 5 16.5 5 18 6"/>
                        <path d="M3 10C4.5 9 6.5 9 8 10C9.5 11 11.5 11 13 10C14.5 9 16.5 9 18 10"/>
                        <path d="M3 14C4.5 13 6.5 13 8 14C9.5 15 11.5 15 13 14C14.5 13 16.5 13 18 14"/>
                      </svg>
                      <span class="m-label dark-txt">土壤水分</span>
                    </div>
                    <button class="m-corner-arrow-btn grey-arrow">
                      <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                        <path d="M4 12L12 4H6M12 4V10"/>
                      </svg>
                    </button>
                  </div>
                  <div class="m-value-flex">
                    <div class="val-num-unit">
                      <span class="val-num dark-txt">65</span>
                      <span class="val-unit muted-txt">%</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">请持续监测，保持水分稳定</p>
                </div>
              </div>
            </div>
          </div>
        </main>

        <!-- ════════════════════ Dynamic Island · Agnes AI 植保问答（顶部灵动岛） ════════════════════
             收起：黑色胶囊常挂顶部（标题与工具栏之间），点击丝滑展开为问答面板。
             面板内容常驻挂载（display 不销毁），流式输出不受展开/收起影响。 -->
        <div
          ref="islandEl"
          class="dyn-island"
          :class="{ open: islandOpen }"
          role="button"
          :aria-expanded="islandOpen"
          :title="islandOpen ? '' : '点击展开 AI 植保问答'"
        >
          <!-- 收起态：胶囊 -->
          <div ref="pillEl" class="dyn-island-pill" @click="openIsland">
            <span class="pill-live-dot"></span>
            <span class="pill-title-txt">AI 问答</span>
            <svg class="pill-sparkle" viewBox="0 0 16 16" fill="currentColor">
              <path d="M8 1L9.4 6.6L15 8L9.4 9.4L8 15L6.6 9.4L1 8L6.6 6.6L8 1Z"/>
            </svg>
          </div>

          <!-- 展开态：AI 问答面板（常驻 DOM） -->
          <div ref="panelEl" class="dyn-island-panel">
          <div class="di-head">
            <span class="di-avatar-pill">AI</span>
            <div class="di-head-txt">
              <h4>AI 植保问答助手</h4>
              <small>● 实时在线 · 专属植保知识库</small>
            </div>
              <button class="di-collapse-btn" @click="closeIsland" title="收起灵动岛">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 10L8 5L13 10"/>
                </svg>
              </button>
            </div>
            <div class="di-messages" ref="chatBodyRef">
              <div
                v-for="(msg, i) in messages"
                :key="i"
                class="di-msg-row"
                :class="msg.role"
              >
                <div
                  class="di-msg-bubble"
                  :class="{ streaming: msg.role === 'ai' && aiTyping && i === messages.length - 1 }"
                >
                  <div v-if="msg.searchQuery" class="di-search-tag">🔍 已检索知网植保库: {{ msg.searchQuery }}</div>
                  <div v-if="msg.role === 'user'" class="msg-plain">{{ msg.text }}</div>
                  <div v-else class="msg-md" v-html="renderMsg(msg)"></div>
                </div>
              </div>
              <div v-if="isThinking" class="di-msg-row ai">
                <div class="di-msg-bubble thinking">
                  <span class="think-dot"></span>
                  <span class="think-dot"></span>
                  <span class="think-dot"></span>
                  <span class="think-label">AI 正在思考</span>
                </div>
              </div>
              <div v-if="toolStatus" class="di-tool-status">
                <div class="spinner-dot"></div>
                <span>{{ toolStatus }}</span>
              </div>
            </div>
            <div class="di-quick-row">
              <span
                v-for="(q, qi) in fastQuestions"
                :key="qi"
                class="di-quick-pill"
                @click="askQuestion(q)"
              >
                {{ q }}
              </span>
            </div>
            <div class="di-input-bar">
              <input
                v-model="inputText"
                @keyup.enter="sendMessage"
                placeholder="询问对症药剂、气象抑制阈值或无人机施药参数..."
                class="di-input"
              />
              <button class="di-send-btn" @click="sendMessage" :disabled="aiTyping">发送</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════ 3. INTERACTIVE DRAWERS & MODALS ════════════════════ -->

    <!-- Alerts Drawer (3 Alerts) -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'alerts'" @click.self="activeModal = null">
      <div class="tanee-modal-card">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-7.svg" alt="Alert" class="modal-head-icon"/>
            <h4>3 条活跃告警</h4>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body">
          <div class="alert-box-item warning">
            <div class="alert-item-head">
              <strong>⚠️ 湿度传感器 HIH-9370 信号中断</strong>
              <span class="alert-time">08:02 AM</span>
            </div>
            <p>Smart Farm 01 温室 08 号分区传感器上报链路抖动，当前采用临界均值补插算法填补空缺遥测点。</p>
          </div>
          <div class="alert-box-item urgent">
            <div class="alert-item-head">
              <strong>🚨 Plot PL-02J 玉米灰斑病菌孢子负荷预警</strong>
              <span class="alert-time">09:15 AM</span>
            </div>
            <p>空气孢子捕捉量突破 124 粒/m³，叶面结露持续超 6.5 小时，已进入初侵染高危敏感窗口期！</p>
          </div>
          <div class="alert-box-item info">
            <div class="alert-item-head">
              <strong>ℹ️ 滴灌水肥一体机自动注液平衡完成</strong>
              <span class="alert-time">07:30 AM</span>
            </div>
            <p>已向根际灌注螯合微肥 50g/株，实测土壤 pH 值由 7.8 稳定调整至标准适宜区间 7.6。</p>
          </div>
        </div>
      </div>
    </div>

    <!-- Telemetry & Radar Drawer -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'telemetry'" @click.self="activeModal = null">
      <div class="tanee-modal-card large">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-15.svg" alt="Charts" class="modal-head-icon"/>
            <h4>24h 微气候遥测与雷达分析</h4>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body charts-grid-layout">
          <div class="chart-tile-box">
            <h5>温湿度与发病指数 24h 动态曲线</h5>
            <div ref="trendRef" class="chart-canvas-div"></div>
          </div>
          <div class="chart-tile-box">
            <h5>多维生态指征雷达分析</h5>
            <div ref="radarRef" class="chart-canvas-div"></div>
          </div>
        </div>
      </div>
    </div>

    <!-- Personal Center Modal（个人中心） -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'profile'" @click.self="activeModal = null">
      <div class="tanee-modal-card profile-modal-card">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-20.svg" alt="Profile" class="modal-head-icon"/>
            <h4>个人中心</h4>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body profile-body">
          <div class="profile-id-card">
            <div class="profile-avatar-circle">农</div>
            <div class="profile-id-info">
              <h3>植保管理员</h3>
              <div class="profile-role-tags">
                <span class="role-tag green">系统管理员</span>
                <span class="role-tag gray">飞防调度员</span>
              </div>
              <p>玉米叶部病斑多尺度自适应感知与飞防决策系统</p>
            </div>
          </div>
          <div class="profile-stats-grid">
            <div class="profile-stat-cell"><strong>12</strong><span>今日诊断（次）</span></div>
            <div class="profile-stat-cell"><strong>47</strong><span>累计任务（个）</span></div>
            <div class="profile-stat-cell"><strong>8.6</strong><span>巡田里程（km）</span></div>
          </div>
          <div class="profile-info-rows">
            <div class="profile-info-row"><span>登录账号</span><strong>admin@tanee.cn</strong></div>
            <div class="profile-info-row"><span>所属单位</span><strong>智慧农业示范田 08 分区</strong></div>
            <div class="profile-info-row"><span>上次登录</span><strong>今天 08:02 · 示范田边缘网关</strong></div>
          </div>
          <div class="profile-action-bar">
            <button class="profile-secondary-btn">编辑资料</button>
            <button class="profile-primary-btn">退出登录</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import axios from 'axios'
import gsap from 'gsap'
import { marked } from 'marked'
import * as echarts from 'echarts'

// ── State ─────────────────────────────────────────────────────────────
const activeNav = ref('home')
const activeModal = ref(null)
const showDiagWorkstation = ref(false)
const scaleFactor = ref(1)
const boardWidth = ref(1194)

const currentSector = ref('菠菜园 08 区')
const presetSamples = ref([])
const currentSampleId = ref('')
const fileInputRef = ref(null)
const currentSample = ref({
  id: 'blight',
  name: '玉米大斑病',
  diseaseName: '玉米大斑病 (Northern Corn Leaf Blight)',
  class_name_en: 'Blight',
  class_name_cn: '玉米大斑病',
  pathogen: '真菌，大斑凸脐蠕孢 (Exserohilum turcicum)',
  severity: '中度 (II 级扩展期)',
  damageRate: 23.5,
  confidence: 96.8,
  color: '#e28557',
  prescription: '选用 40% 氟硅唑·多菌灵可湿性粉剂 1000倍液 或 苯醚甲环唑·嘧菌酯，利用大田植保无人机实施傍晚超低空微滴变量精准喷雾。',
  droneParams: {
    model: '大疆 T50 / T60',
    volume: '1.6 L/亩',
    dropletSize: '135 μm',
    altitude: '2.2 米',
    speed: '5.0 m/s'
  },
  boxes: [
    { x: 30.2, y: 18.4, w: 38.0, h: 30.0, label: '大斑病灶 #1', conf: '96.8%' }
  ],
  gradcam_base64: ''
})
const previewUrl = ref('/tanee/raw/dashboard/image-2.jpeg')

const isDetecting = ref(false)
const isDetected = ref(true)
const showHeatmap = ref(false)
const showBBoxes = ref(true)
const inferenceSpeed = ref('14.2ms')

function triggerUpload() {
  if (fileInputRef.value) {
    fileInputRef.value.click()
  }
}

function handleFileUpload(e) {
  const file = e.target.files?.[0]
  if (!file) return
  processUploadedFile(file)
  e.target.value = ''
}

function handleFileDrop(e) {
  e.preventDefault()
  const file = e.dataTransfer.files?.[0]
  if (file && file.type.startsWith('image/')) {
    processUploadedFile(file)
  }
}

function processUploadedFile(file) {
  const reader = new FileReader()
  reader.onload = (event) => {
    const base64 = event.target.result
    previewUrl.value = base64
    currentSampleId.value = 'upload_' + Date.now()
    currentSample.value = {
      id: currentSampleId.value,
      name: file.name,
      diseaseName: '待检测叶片',
      class_name_en: 'Custom',
      class_name_cn: '自定义导入',
      pathogen: '待诊断',
      severity: '待诊断',
      damageRate: 0,
      confidence: 0,
      color: '#667085',
      imgData: base64,
      boxes: [],
      gradcam_base64: '',
      prescription: '',
      droneParams: null
    }
    isDetected.value = false
    showHeatmap.value = false
    // 导入图片后保持待诊断状态，不自动执行推理，等待用户点击“开始诊断”按钮
  }
  reader.readAsDataURL(file)
}

const currentSampleIndex = computed(() => {
  if (!presetSamples.value.length || !currentSampleId.value) return 0
  const idx = presetSamples.value.findIndex(s => s.id === currentSampleId.value)
  return idx >= 0 ? idx : 0
})

// ── 摄像头画面自动轮播 ────────────────────────────────────────────────
const cameraFeeds = [
  { src: '/tanee/raw/dashboard/image-2.jpeg', name: '温室实景' },
  { src: '/tanee/raw/dashboard/image-3.jpeg', name: '玉米田航拍' },
  { src: '/tanee/raw/dashboard/image-4.jpeg', name: '玉米苗情' },
  { src: '/tanee/raw/dashboard/image-5.jpeg', name: '植保无人机' }
]
const cameraIndex = ref(0)
let carouselTimer = null
const CAROUSEL_INTERVAL = 4000

const trackPos = ref(0)
const noTransition = ref(false)
const trackRef = ref(null)
let snapTimer = null
let snapCleanup = null

// 归零瞬跳：必须先让"无过渡 + 0%"状态完成一次绘制（双重 rAF），再恢复过渡，
// 否则浏览器会按上一帧画面(-400%)启动过渡，出现倒滑动画
function snapBackInstantly() {
  cancelSnapBack()
  noTransition.value = true
  trackPos.value = 0
  nextTick(() => {
    requestAnimationFrame(() => {
      requestAnimationFrame(() => {
        noTransition.value = false
      })
    })
  })
}

// 等滑动动画真正结束（transitionend）再归零，超时兜底
function armSnapBack() {
  cancelSnapBack()
  const el = trackRef.value
  if (!el) {
    snapTimer = setTimeout(snapBackInstantly, 700)
    return
  }
  const onEnd = (e) => {
    if (e.propertyName !== 'transform') return
    snapBackInstantly()
  }
  el.addEventListener('transitionend', onEnd)
  snapTimer = setTimeout(snapBackInstantly, 900)
  snapCleanup = () => el.removeEventListener('transitionend', onEnd)
}

function cancelSnapBack() {
  clearTimeout(snapTimer)
  if (snapCleanup) {
    snapCleanup()
    snapCleanup = null
  }
}

// 统一滑动入口：末张→首张时先正向滑到尾部克隆位，动画结束后瞬间归零，避免倒滑
function slideTo(next) {
  cancelSnapBack()
  const count = cameraFeeds.length

  if (trackPos.value === count && next !== 0) {
    // 正停在克隆位：先无动画归零，绘制完成后再正常滑向目标
    cancelSnapBack()
    noTransition.value = true
    trackPos.value = 0
    cameraIndex.value = next
    nextTick(() => {
      requestAnimationFrame(() => {
        requestAnimationFrame(() => {
          noTransition.value = false
          trackPos.value = next
        })
      })
    })
    return
  }

  const current = trackPos.value === count ? 0 : trackPos.value
  cameraIndex.value = next

  if (current === count - 1 && next === 0) {
    trackPos.value = count
    armSnapBack()
    return
  }

  trackPos.value = next
}

function cameraNext() {
  slideTo((cameraIndex.value + 1) % cameraFeeds.length)
  restartCarousel()
}

function cameraPrev() {
  slideTo((cameraIndex.value - 1 + cameraFeeds.length) % cameraFeeds.length)
  restartCarousel()
}

function cameraGo(i) {
  slideTo(i)
  restartCarousel()
}

function restartCarousel() {
  clearInterval(carouselTimer)
  carouselTimer = setInterval(() => {
    slideTo((cameraIndex.value + 1) % cameraFeeds.length)
  }, CAROUSEL_INTERVAL)
}

function pauseCarousel() {
  clearInterval(carouselTimer)
}

function resumeCarousel() {
  restartCarousel()
}

// Tasks
const tasks = ref([
  {
    name: '灌溉浇水',
    desc: '早晨为作物浇灌约 1 英寸水量',
    time: '07:00 - 07:30',
    completed: true
  },
  {
    name: '施用有机肥',
    desc: '在植株根部施加有机肥，每株 50g',
    time: '07:30 - 10:00',
    completed: true
  },
  {
    name: '虫害巡查',
    desc: '检查叶片是否存在蚜虫等虫害迹象',
    time: '10:00 - 11:00',
    completed: false
  },
  {
    name: '松土透气',
    desc: '小心松动植株周围土壤，避免损伤根系',
    time: '14:00 - 15:00',
    completed: false
  }
])

function toggleTask(i) {
  tasks.value[i].completed = !tasks.value[i].completed
}

function toggleSector() {
  currentSector.value = currentSector.value === '菠菜园 08 区' ? '玉米田 04 区' : '菠菜园 08 区'
}

// ── API: Load Samples ─────────────────────────────────────────────────
async function loadSamples() {
  try {
    const res = await axios.get('/api/screen/samples')
    if (res.data?.data?.length) {
      presetSamples.value = res.data.data
      if (!currentSample.value) {
        selectPreset(presetSamples.value[0], false)
      }
    }
  } catch (e) {
    console.error('加载预置样本失败:', e)
  }
}

function selectPreset(s, autoDetect = true) {
  currentSampleId.value = s.id
  currentSample.value = { ...s }
  previewUrl.value = s.imgData
  isDetected.value = false
  showHeatmap.value = false
  if (autoDetect) {
    runDetect()
  }
}

function prevSample() {
  if (!presetSamples.value.length) return
  let idx = currentSampleIndex.value - 1
  if (idx < 0) idx = presetSamples.value.length - 1
  selectPreset(presetSamples.value[idx])
}

function nextSample() {
  if (!presetSamples.value.length) return
  let idx = currentSampleIndex.value + 1
  if (idx >= presetSamples.value.length) idx = 0
  selectPreset(presetSamples.value[idx])
}

function triggerCameraCapture() {
  const currentFeed = cameraFeeds[cameraIndex.value]
  previewUrl.value = currentFeed.src
  currentSampleId.value = 'cam_' + cameraIndex.value
  currentSample.value = {
    id: currentSampleId.value,
    name: `${currentFeed.name} (实时抓拍)`,
    diseaseName: '大田监测抓拍叶片',
    class_name_en: 'Field_Capture',
    class_name_cn: '航拍抓拍',
    pathogen: '待诊断',
    severity: '待诊断',
    damageRate: 0,
    confidence: 0,
    color: '#667085',
    imgData: currentFeed.src,
    boxes: [],
    gradcam_base64: '',
    prescription: '',
    droneParams: null
  }
  isDetected.value = false
  showHeatmap.value = false
  // 抓拍导入后保持待诊断状态，等待用户点击“开始诊断”
}

// ── API: Run Detect ───────────────────────────────────────────────────
async function runDetect() {
  if (!previewUrl.value || isDetecting.value) return
  isDetecting.value = true

  try {
    const res = await axios.post('/api/screen/predict', {
      image_base64: previewUrl.value,
      filename: currentSample.value?.name || 'leaf.jpg',
      model: 'resnet50_cbam'
    })

    if (res.data?.data) {
      const data = res.data.data
      currentSample.value = {
        ...currentSample.value,
        diseaseName: data.diseaseName,
        class_name_en: data.class_name_en,
        class_name_cn: data.class_name_cn,
        pathogen: data.pathogen,
        severity: data.severity,
        damageRate: data.damageRate,
        confidence: data.confidence,
        color: data.color || '#17B26A',
        prescription: data.prescription,
        boxes: data.boxes || [],
        gradcam_base64: data.gradcam_base64
      }
      isDetected.value = true
      inferenceSpeed.value = data.inference_ms + 'ms'
    }
  } catch (err) {
    console.error('推理检测失败:', err)
  } finally {
    isDetecting.value = false
  }
}

// ── Agnes-3.0 AI Chat ─────────────────────────────────────────────────
const messages = ref([
  {
    role: 'ai',
    text: '您好！我是 <strong>AI 植保问答助手</strong>，已连接示范田 24h 微气候传感器与田间监测数据。请问有什么可以协助您？',
    searchQuery: ''
  }
])
const inputText = ref('')
const aiTyping = ref(false)
const toolStatus = ref('')
const chatBodyRef = ref(null)

marked.setOptions({ gfm: true, breaks: true })

// 思考中：消息已发出、首个 delta 未到、也无联网检索提示
const isThinking = computed(
  () =>
    aiTyping.value &&
    !toolStatus.value &&
    messages.value[messages.value.length - 1]?.role === 'user'
)

// AI 回复按 markdown 渲染（流式分片同样适用）；用户消息纯文本防注入
function renderMsg(msg) {
  if (msg.role === 'user') return ''
  if (!msg.text) return ''
  return marked.parse(msg.text)
}

const fastQuestions = [
  '玉米灰斑病用什么药最有效？',
  '当前温湿度下喷药会不会产生药害？',
  '如何调配无人机变量施药处方？'
]

async function sendMessage() {
  const query = inputText.value.trim()
  if (!query || aiTyping.value) return

  // 多轮上下文：携带之前的对话（跳过固定欢迎语、不含本轮问题），后端按标准 messages 结构包装
  const history = messages.value
    .slice(1)
    .filter(m => m.text)
    .slice(-6)
    .map(m => ({ role: m.role, content: m.text }))

  messages.value.push({ role: 'user', text: query })
  inputText.value = ''
  aiTyping.value = true
  toolStatus.value = ''

  await nextTick()
  if (chatBodyRef.value) {
    chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  }

  let hasAiMsg = false

  try {
    const response = await fetch('/api/screen/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        message: query,
        history,
        // 当前诊断上下文（字段与后端 build_context_block 对齐；undefined 字段 JSON 序列化时自动省略）
        context: isDetected.value ? {
          diseaseName: currentSample.value?.diseaseName || '玉米灰斑病',
          damageRate: currentSample.value?.damageRate ?? 28.4,
          confidence: currentSample.value?.confidence ?? undefined,
          severity: currentSample.value?.severity ?? undefined,
          prescription: currentSample.value?.prescription ?? undefined
        } : {
          status: '待诊断',
          note: '用户已导入图片，但尚未触发 AI 诊断'
        }
      })
    })

    const reader = response.body.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue
        const jsonStr = line.slice(6).trim()
        if (!jsonStr || jsonStr === '[DONE]') continue

        try {
          const evt = JSON.parse(jsonStr)
          if (evt.type === 'tool_call') {
            toolStatus.value = `正在联网检索：「${evt.query}」...`
          } else if (evt.type === 'stop_hook') {
            // Stop Hook（回合结束钩子）：block=回答被打回重答，allow=校验通过即将结束
            toolStatus.value = evt.action === 'block'
              ? '回答未通过停止校验，正在重新组织更完整的回答...'
              : ''
          } else if (evt.type === 'delta') {
            if (!hasAiMsg) {
              hasAiMsg = true
              messages.value.push({
                role: 'ai',
                text: '',
                searchQuery: toolStatus.value ? toolStatus.value.replace(/.*「(.*)」.*/, '$1') : ''
              })
            }
            toolStatus.value = ''
            const lastMsg = messages.value[messages.value.length - 1]
            lastMsg.text += evt.content
            const body = chatBodyRef.value
            if (body && body.scrollHeight - body.scrollTop - body.clientHeight < 80) {
              body.scrollTop = body.scrollHeight
            }
          }
        } catch (e) {
          console.warn('解析流式消息异常:', e)
        }
      }
    }
  } catch (err) {
    console.error('流式问答失败:', err)
    if (!hasAiMsg) {
      messages.value.push({
        role: 'ai',
        text: '⚠️ 问答服务响应超时，建议参考嘧菌酯对路药剂并严控田间湿度。'
      })
    }
  } finally {
    aiTyping.value = false
  }
}

function askQuestion(q) {
  inputText.value = q
  sendMessage()
}

// ── 顶部灵动岛（Dynamic Island · AI 问答） ─────────────────────────────
// GSAP 驱动胶囊 ⇄ 面板的形变（宽度/高度/圆角/水平位置同步补间）。
// 面板 DOM 常驻挂载，仅做透明度切换，流式输出在收起时仍持续接收。
const islandOpen = ref(false)
const islandEl = ref(null)
const pillEl = ref(null)
const panelEl = ref(null)
let islandTween = null

const ISLAND_COLLAPSED = { width: 112, height: 34, left: 730, radius: 17 }
const ISLAND_EXPANDED = { width: 560, height: 620, left: 505, radius: 22 }

function openIsland() {
  if (islandOpen.value) return
  islandOpen.value = true
  if (islandTween) islandTween.kill()
  islandTween = gsap.to(islandEl.value, {
    width: ISLAND_EXPANDED.width,
    height: ISLAND_EXPANDED.height,
    left: ISLAND_EXPANDED.left,
    borderRadius: ISLAND_EXPANDED.radius,
    duration: 0.45,
    ease: 'power2.out'
  })
  gsap.to(pillEl.value, { opacity: 0, scale: 0.9, duration: 0.14, ease: 'power2.out' })
  gsap.fromTo(
    panelEl.value,
    { opacity: 0, y: -12 },
    { opacity: 1, y: 0, duration: 0.3, delay: 0.16, ease: 'power3.out' }
  )
}

function closeIsland() {
  if (!islandOpen.value) return
  islandOpen.value = false
  if (islandTween) islandTween.kill()
  gsap.to(panelEl.value, { opacity: 0, y: -10, duration: 0.14, ease: 'power2.in' })
  islandTween = gsap.to(islandEl.value, {
    width: ISLAND_COLLAPSED.width,
    height: ISLAND_COLLAPSED.height,
    left: ISLAND_COLLAPSED.left,
    borderRadius: ISLAND_COLLAPSED.radius,
    duration: 0.4,
    delay: 0.08,
    ease: 'power2.inOut'
  })
  gsap.to(pillEl.value, { opacity: 1, scale: 1, duration: 0.26, delay: 0.24, ease: 'power3.out' })
}

// ── 界面配色（主题切换，localStorage 持久化） ──────────────────────────
const themeMenuOpen = ref(false)
const themeMode = ref(localStorage.getItem('tanee-theme') || 'light')
const themeOptions = [
  { id: 'light', name: '浅色 · 标准' },
  { id: 'dark', name: '夜间 · 深色' },
  { id: 'green', name: '护眼 · 青绿' }
]
const themeClass = computed(() => (themeMode.value !== 'light' ? 'theme-' + themeMode.value : ''))

function setTheme(id) {
  themeMode.value = id
  localStorage.setItem('tanee-theme', id)
  themeMenuOpen.value = false
}

// ── ECharts Telemetry ─────────────────────────────────────────────────
const trendRef = ref(null)
const radarRef = ref(null)
let trendChart = null
let radarChart = null

async function initCharts() {
  try {
    const res = await axios.get('/api/screen/telemetry')
    const t = res.data?.data
    if (!t) return

    if (trendRef.value) {
      trendChart = echarts.init(trendRef.value)
      trendChart.setOption({
        backgroundColor: '#ffffff',
        grid: { top: 30, bottom: 20, left: 36, right: 16 },
        tooltip: { trigger: 'axis' },
        xAxis: { type: 'category', data: t.climate.hours, axisLabel: { fontSize: 10 } },
        yAxis: { type: 'value', min: 0, max: 100 },
        series: [
          { name: '发病指数', type: 'line', smooth: true, data: t.climate.temperatures.map(v => Math.round(v * 2.5)), itemStyle: { color: '#17B26A' } },
          { name: '湿度(%)', type: 'line', smooth: true, data: t.climate.humidities, itemStyle: { color: '#3b82f6' } }
        ]
      })
    }

    if (radarRef.value) {
      radarChart = echarts.init(radarRef.value)
      radarChart.setOption({
        backgroundColor: '#ffffff',
        radar: {
          indicator: t.radar.map(r => ({ name: r.name, max: r.max })),
          radius: '65%'
        },
        series: [
          {
            type: 'radar',
            data: [{ value: t.radar.map(r => r.value), name: '实测能力', itemStyle: { color: '#17B26A' } }]
          }
        ]
      })
    }
  } catch (e) {
    console.error('加载遥测图表失败:', e)
  }
}

// ── Resize / Viewport Scaling ─────────────────────────────────────────
function handleResize() {
  const w = window.innerWidth
  const h = window.innerHeight
  // 纵向等比缩放，画板宽度按比例反算以铺满浏览器；窗口过窄时按宽度缩放防止内容溢出
  scaleFactor.value = Math.min(w / 1194, h / 834)
  boardWidth.value = Math.max(1194, Math.round(w / scaleFactor.value))
}

onMounted(() => {
  handleResize()
  window.addEventListener('resize', handleResize)
  loadSamples()
  restartCarousel()
  // 灵动岛入场：从顶部缓缓落下
  if (islandEl.value) {
    gsap.from(islandEl.value, { y: -26, opacity: 0, duration: 0.6, delay: 0.35, ease: 'power3.out' })
  }
  nextTick(() => {
    initCharts()
  })
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  clearInterval(carouselTimer)
  cancelSnapBack()
  if (islandTween) islandTween.kill()
  trendChart && trendChart.dispose()
  radarChart && radarChart.dispose()
})
</script>

<style lang="scss" scoped>
/* ==========================================================================
   Tanee Smart Farming App UI Kit (1:1 Exact Match with Figma Community Source)
   Artboard: 1194px × 834px | Canvas: #DCDCDC | Cards: #ECECEC | Nested: #F4F4F4
   Design Tokens from: tokens/design-tokens.json & json/design-page.json
   ========================================================================== */

.tanee-app-root {
  width: 100vw;
  height: 100vh;
  background-color: #dcdcdc;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
  font-family: 'Satoshi', 'Inter', 'Microsoft YaHei', 'PingFang SC', -apple-system, BlinkMacSystemFont, sans-serif;
  color: #333333;
}

.tanee-scalable-viewport {
  width: 1194px;
  height: 834px;
  transform-origin: center center;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tanee-dashboard-artboard {
  width: 100%;
  height: 834px;
  background-color: #dcdcdc;
  display: flex;
  flex-direction: row;
  position: relative;
  box-sizing: border-box;
}

/* ════════════════════ 1. SIDEBAR (103px) ════════════════════ */
.tanee-sidebar {
  width: 103px;
  height: 834px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  flex-shrink: 0;
}

.brand-frame {
  width: 103px;
  height: 78px;
  display: flex;
  align-items: center;
  justify-content: center;

  .brand-logo-circle {
    width: 46px;
    height: 46px;
    border-radius: 9999px;
    background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
    display: flex;
    align-items: center;
    justify-content: center;
    cursor: pointer;
    box-shadow: 0 4px 12px rgba(53, 197, 110, 0.35);

    .brand-union-icon {
      width: 22px;
      height: 22px;
    }
  }
}

.menu-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;

  &.upper {
    margin-top: 48px;
  }

  &.lower {
    margin-bottom: 24px;
  }
}

.nav-item-btn {
  width: 60px;
  height: 60px;
  border-radius: 12px;
  border: none;
  background: #ffffff;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;

  .nav-svg-icon {
    width: 20px;
    height: 20px;
  }

  &.active {
    background: #1e2024;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

    .white-filter {
      filter: brightness(0) invert(1);
    }
  }

  &:hover:not(.active) {
    background: #f8f8f8;
  }
}

/* ════════════════════ 2. BODY (1091px) ════════════════════ */
.tanee-body {
  flex: 1;
  min-width: 0;
  height: 834px;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

/* 2.1 Header (76px) */
.tanee-header {
  height: 76px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;

  .header-title {
    margin: 0;
    font-size: 28px;
    font-weight: 700;
    letter-spacing: -0.02em;
    color: #333333;
  }

  .header-right-tools {
    display: flex;
    align-items: center;
    gap: 16px;
  }
}

/* Alerts Button (auto width for CJK text, gradient #666 to #1a1a1a) */
.alerts-pill-btn {
  width: auto;
  min-width: 112px;
  height: 32px;
  border-radius: 8px;
  border: none;
  background: linear-gradient(135deg, #666666 0%, #1a1a1a 100%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 0 10px 0 0;
  cursor: pointer;
  color: #ffffff;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.15);
  transition: transform 0.15s ease;

  &:hover {
    transform: translateY(-1px);
  }

  .notif-box {
    width: 32px;
    height: 32px;
    border-radius: 8px 0 0 8px;
    background: rgba(255, 255, 255, 0.16);
    display: flex;
    align-items: center;
    justify-content: center;

    .bell-svg {
      width: 14px;
      height: 14px;
      filter: brightness(0) invert(1);
    }
  }

  .alerts-txt {
    font-size: 13px;
    font-weight: 600;
  }

  .arrow-up-right-svg {
    width: 14px;
    height: 14px;
  }
}

/* Sector Selector (text + pill) */
.sector-selector-wrap {
  display: flex;
  align-items: center;
  gap: 8px;

  .sector-label-txt {
    font-size: 14px;
    font-weight: 500;
    color: #333333;
  }

  .sector-dropdown-btn {
    height: 31px;
    border-radius: 8px;
    border: none;
    background: #eaeaea;
    display: flex;
    align-items: center;
    gap: 6px;
    padding: 0 10px;
    cursor: pointer;
    font-size: 13px;
    font-weight: 500;
    color: #333333;

    &:hover {
      background: #e2e2e2;
    }

    .caret-down-svg {
      width: 12px;
      height: 12px;
    }
  }
}

/* 2.2 Main Content Layout (16px Padding, 2 Columns) */
.main-content-layout {
  flex: 1;
  min-height: 0;
  padding: 0 16px 16px 16px;
  display: flex;
  gap: 8px;
  box-sizing: border-box;
}

.content-column {
  flex: 1;
  min-width: 0;
  height: 726px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  box-sizing: border-box;

  &.right-col-reordered {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
}

/* ──────────────── LEFT COLUMN: 核心功能 · 图片导入与智能检测 ──────────────── */

/* Card 1: 视觉感知与图像导入交互工作台 (525.5px × 446px) */
.ai-detection-workbench {
  width: 100%;
  height: 446px;
  background: #ffffff;
  border-radius: 8px;
  padding: 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  position: relative;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
}

.wb-header-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;

  .wb-title-group {
    display: flex;
    align-items: center;
    gap: 8px;

    .wb-title-icon-box {
      width: 28px;
      height: 28px;
      border-radius: 6px;
      background: #ecfdf3;
      display: flex;
      align-items: center;
      justify-content: center;

      svg {
        width: 16px;
        height: 16px;
      }
    }

    .wb-title-text-wrap {
      display: flex;
      align-items: center;
      gap: 8px;

      .wb-main-title {
        margin: 0;
        font-size: 15px;
        font-weight: 700;
        color: #1d2939;
      }

      .wb-model-tag {
        font-size: 12px;
        font-weight: 700;
        background: #ecfdf3;
        color: #027a48;
        padding: 2px 7px;
        border-radius: 9999px;
        border: 1px solid #a6f4c5;
        letter-spacing: 0.02em;
      }
    }
  }

  .wb-header-actions {
    display: flex;
    align-items: center;
    gap: 8px;

    .wb-status-badge {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 13px;
      font-weight: 500;
      color: #475467;
      background: #f8f9fa;
      border: 1px solid #eaecf0;
      padding: 4px 10px;
      border-radius: 6px;

      .status-pulse-dot {
        width: 7px;
        height: 7px;
        border-radius: 9999px;
        background: #17b26a;
        box-shadow: 0 0 0 3px rgba(23, 178, 106, 0.2);
      }

      &.detecting {
        .status-pulse-dot {
          background: #f79009;
          box-shadow: 0 0 0 3px rgba(247, 144, 9, 0.25);
          animation: pulse 1s infinite alternate;
        }
      }

      &.waiting {
        .status-pulse-dot {
          background: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.25);
          animation: pulse 1.5s infinite alternate;
        }
      }
    }

    .hidden-file-input {
      display: none;
    }

    .wb-upload-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #1d2939;
      color: #ffffff;
      border: none;
      padding: 5px 14px;
      border-radius: 6px;
      font-size: 13.5px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;

      svg {
        width: 15px;
        height: 15px;
      }

      &:hover {
        background: #101828;
        transform: translateY(-0.5px);
      }
    }
  }
}

/* Central Visual Inspection Canvas */
.detection-canvas-container {
  flex: 1;
  width: 100%;
  min-height: 275px;
  background: #15191c;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.08);

  /* 图像显示舞台：自适应包裹叶片，使标注框百分比基准严格对应叶片本身 */
  .canvas-image-stage {
    position: relative;
    display: inline-flex;
    align-items: center;
    justify-content: center;
    max-width: 100%;
    max-height: 275px;
    line-height: 0;

    .leaf-raw-image {
      max-width: 100%;
      max-height: 275px;
      object-fit: contain;
      display: block;
      transition: opacity 0.3s ease;

      &.dimmed {
        opacity: 0.65;
      }
    }

    .leaf-gradcam-layer {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      object-fit: fill;
      mix-blend-mode: screen;
      pointer-events: none;
      transition: opacity 0.3s ease;
    }

    .leaf-bbox-overlay {
      position: absolute;
      inset: 0;
      width: 100%;
      height: 100%;
      pointer-events: none;

      .leaf-single-box {
        position: absolute;
        border: 2px solid #f9ad19;
        background: rgba(249, 173, 25, 0.18);
        box-shadow: 0 0 8px rgba(249, 173, 25, 0.4);
        box-sizing: border-box;

        .bbox-label {
          position: absolute;
          top: -20px;
          left: -2px;
          background: #f9ad19;
          color: #1a1a1a;
          font-size: 11.5px;
          font-weight: 700;
          padding: 1px 5px;
          border-radius: 2px;
          white-space: nowrap;
        }
      }
    }

    .ai-scanline-laser {
      position: absolute;
      inset: 0;
      pointer-events: none;
      overflow: hidden;

      .laser-beam {
        width: 100%;
        height: 3px;
        background: linear-gradient(90deg, transparent, #17b26a, #52e597, #17b26a, transparent);
        box-shadow: 0 0 14px #17b26a;
        position: absolute;
        animation: scanLaser 2s linear infinite;
      }
    }
  }

  .canvas-top-overlay {
    position: absolute;
    top: 8px;
    left: 8px;
    right: 8px;
    display: flex;
    justify-content: space-between;
    pointer-events: none;
    z-index: 5;

    .canvas-filename-chip {
      display: flex;
      align-items: center;
      gap: 5px;
      background: rgba(0, 0, 0, 0.65);
      backdrop-filter: blur(6px);
      color: #ffffff;
      font-size: 12.5px;
      font-weight: 500;
      padding: 3px 10px;
      border-radius: 4px;

      svg {
        width: 13px;
        height: 13px;
        color: #17b26a;
      }
    }

    .canvas-conf-chip {
      background: rgba(23, 178, 106, 0.9);
      backdrop-filter: blur(6px);
      color: #ffffff;
      font-size: 13px;
      font-weight: 700;
      padding: 3px 10px;
      border-radius: 4px;
    }
  }

  .canvas-floating-toolbar {
    position: absolute;
    bottom: 8px;
    left: 8px;
    right: 8px;
    background: rgba(18, 22, 25, 0.8);
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    border-radius: 6px;
    padding: 4px 8px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 5;

    .view-layers-group {
      display: flex;
      gap: 5px;

      .layer-toggle-btn {
        background: transparent;
        border: 1px solid rgba(255, 255, 255, 0.2);
        color: #d0d5dd;
        font-size: 12.5px;
        padding: 4px 10px;
        border-radius: 4px;
        cursor: pointer;
        transition: all 0.2s ease;

        &:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #ffffff;
        }

        &.active {
          background: #ffffff;
          color: #101828;
          border-color: #ffffff;
          font-weight: 600;
        }
      }
    }

    .canvas-action-btn {
      display: flex;
      align-items: center;
      gap: 6px;
      background: linear-gradient(135deg, #17b26a 0%, #0f9755 100%);
      color: #ffffff;
      border: none;
      padding: 6px 16px;
      border-radius: 4px;
      font-size: 13px;
      font-weight: 700;
      cursor: pointer;
      transition: all 0.2s ease;

      svg {
        width: 14px;
        height: 14px;
      }

      &:hover {
        filter: brightness(1.1);
        transform: translateY(-0.5px);
      }

      &.pulse-highlight {
        animation: pulseBtn 1.8s infinite;
      }

      &:disabled {
        opacity: 0.65;
        cursor: not-allowed;
      }

      .btn-spinner {
        width: 10px;
        height: 10px;
        border: 2px solid rgba(255, 255, 255, 0.4);
        border-top-color: #ffffff;
        border-radius: 9999px;
        animation: spin 0.8s linear infinite;
      }
    }
  }
}

/* Preset Samples Footer */
.wb-samples-footer {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 8px;

  .preset-label-txt {
    font-size: 13px;
    font-weight: 600;
    color: #667085;
    flex-shrink: 0;
  }

  .preset-samples-scroll {
    display: flex;
    gap: 6px;
    flex: 1;
    overflow-x: auto;

    .preset-sample-pill {
      display: flex;
      align-items: center;
      gap: 6px;
      background: #f4f4f4;
      border: 1px solid #e5e7eb;
      border-radius: 5px;
      padding: 3px 10px;
      cursor: pointer;
      transition: all 0.2s ease;
      flex-shrink: 0;

      .pill-thumb-img {
        width: 20px;
        height: 20px;
        border-radius: 3px;
        object-fit: cover;
      }

      .pill-sample-name {
        font-size: 13px;
        font-weight: 500;
        color: #333333;
      }

      &.active {
        background: #ecfdf3;
        border-color: #17b26a;

        .pill-sample-name {
          color: #027a48;
          font-weight: 700;
        }
      }

      &:hover {
        border-color: #17b26a;
      }
    }
  }

  .quick-cam-btn {
    display: flex;
    align-items: center;
    gap: 5px;
    background: #f4f4f4;
    border: 1px solid #e5e7eb;
    padding: 3px 10px;
    border-radius: 5px;
    font-size: 13px;
    color: #333333;
    cursor: pointer;
    flex-shrink: 0;

    .quick-cam-icon {
      width: 14px;
      height: 14px;
    }

    &:hover {
      background: #eaeaea;
    }
  }
}

/* Card 2: 诊断评估与飞防决策结果面板 (525.5px × 272px) */
.diagnosis-decision-card {
  width: 100%;
  height: 272px;
  background: #ffffff;
  border-radius: 8px;
  padding: 10px 14px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);
  overflow: hidden;
}

.dd-header-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid #f0f0f0;
  padding-bottom: 6px;

  .dd-disease-info {
    display: flex;
    flex-direction: column;
    gap: 2px;

    .dd-disease-title {
      margin: 0;
      font-size: 17px;
      font-weight: 700;
      color: #101828;
      line-height: 1.2;
    }

    .dd-pathogen-txt {
      font-size: 12px;
      color: #667085;
      line-height: 1.2;
    }
  }

  .dd-severity-badge {
    color: #ffffff;
    font-size: 12.5px;
    font-weight: 700;
    padding: 3px 11px;
    border-radius: 9999px;
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
  }
}

.dd-content-grid {
  display: flex;
  gap: 10px;
  flex: 1;
  min-height: 0;
  padding-top: 6px;

  .dd-metrics-subcol {
    width: 38%;
    display: flex;
    flex-direction: column;
    gap: 5px;
    justify-content: space-between;

    .dd-stat-tile {
      background: #f8f9fa;
      border-radius: 6px;
      padding: 5px 8px;
      display: flex;
      flex-direction: column;
      gap: 2px;

      .stat-top-row {
        display: flex;
        justify-content: space-between;
        align-items: baseline;
      }

      .stat-lbl {
        font-size: 12px;
        color: #667085;
        font-weight: 500;
      }

      .stat-val {
        font-size: 16.5px;
        font-weight: 700;
        line-height: 1.1;

        &.text-green { color: #17b26a; }
        &.text-orange { color: #f79009; }
      }

      .stat-val-sm {
        font-size: 12.5px;
        font-weight: 600;
        color: #1d2939;
      }

      .stat-progress-line {
        width: 100%;
        height: 3.5px;
        background: #e5e7eb;
        border-radius: 2px;
        overflow: hidden;
        margin-top: 2px;

        .stat-progress-bar {
          height: 100%;
          background: #17b26a;
          border-radius: 2px;

          &.orange {
            background: #f79009;
          }
        }
      }
    }
  }

  .dd-flight-subcol {
    flex: 1;
    background: #fbfcfd;
    border: 1px solid #eaecf0;
    border-radius: 6px;
    padding: 8px 10px;
    display: flex;
    flex-direction: column;
    justify-content: space-between;

    .flight-head-row {
      display: flex;
      align-items: center;
      justify-content: space-between;

      .flight-tag-icon {
        font-size: 13.5px;
        font-weight: 700;
        color: #1d2939;
      }
    }

    .flight-prescription-txt {
      margin: 2px 0;
      font-size: 12.5px;
      color: #344054;
      line-height: 1.4;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;

      &.waiting-txt {
        color: #667085;
      }
    }

    .drone-params-row {
      display: flex;
      justify-content: space-between;
      background: #ffffff;
      border-radius: 6px;
      padding: 4px 6px;
      border: 1px solid #f2f4f7;

      .d-param-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1px;

        .dp-k {
          font-size: 11px;
          color: #98a2b3;
        }

        .dp-v {
          font-size: 12.5px;
          font-weight: 700;
          color: #101828;
        }
      }
    }

    .flight-weather-notice {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 11.5px;
      color: #027a48;
      background: #ecfdf3;
      padding: 3px 6px;
      border-radius: 4px;

      .check-icon {
        font-weight: 700;
      }

      &.notice-waiting {
        color: #475467;
        background: #f2f4f7;
      }
    }
  }
}

/* ──────────────── RIGHT COLUMN: 原左侧组件 (天气/地块 + 6大指标) + 轮播图 ──────────────── */

.weather-carousel-row {
  width: 100%;
  height: 248px;
  display: flex;
  gap: 8px;
  flex-shrink: 0;
  box-sizing: border-box;
}

.weather-plot-card {
  width: calc(50% - 4px);
  height: 248px;
  background: #ffffff;
  border-radius: 8px;
  padding: 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  &:hover {
    transform: translateY(-1px);
  }

  .wp-top-bar {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .wp-loc-tag {
      display: flex;
      align-items: center;
      gap: 6px;

      .pin-svg {
        width: 15px;
        height: 15px;
      }

      .loc-text {
        font-size: 16px;
        font-weight: 600;
        color: #333333;
      }
    }
  }

  .wp-datetime-str {
    font-size: 12.5px;
    color: #888888;
  }

  .wp-temp-center {
    margin: 4px 0;

    .temperature-big {
      font-size: 42px;
      font-weight: 700;
      color: #333333;
      line-height: 1;
      letter-spacing: -0.02em;
    }

    .weather-inline-row {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-top: 4px;

      .sun-icon-box {
        width: 22px;
        height: 22px;

        svg {
          width: 100%;
          height: 100%;
        }
      }

      .weather-status-txt {
        font-size: 15px;
        font-weight: 700;
        color: #333333;
      }

      .hl-range-txt {
        font-size: 12.5px;
        color: #888888;
      }
    }
  }

  .wp-plot-pill {
    background: #f4f4f4;
    border-radius: 6px;
    padding: 7px 10px;
    display: flex;
    flex-direction: column;
    gap: 3px;

    .wp-plot-head {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .plot-name {
        font-size: 14px;
        font-weight: 600;
        color: #333333;
      }

      .plot-status-dot {
        font-size: 12px;
        font-weight: 600;
        color: #17b26a;
      }
    }

    .wp-plot-meta {
      display: flex;
      justify-content: space-between;
      font-size: 12.5px;
      color: #555555;

      strong {
        color: #333333;
      }
    }
  }
}

/* Camera Card (fills right half of top row) */
.camera-live-box {
  width: calc(50% - 4px);
  height: 248px;
  border-radius: 8px;
  overflow: hidden;
  position: relative;
  flex-shrink: 0;

  .cam-carousel-stage {
    position: absolute;
    inset: 0;
    overflow: hidden;

    .cam-slide-track {
      display: flex;
      width: 100%;
      height: 100%;
      transition: transform 0.6s cubic-bezier(0.33, 0, 0.2, 1);

      &.no-anim {
        transition: none;
      }

      .camera-bg-image {
        flex-shrink: 0;
        width: 100%;
        height: 100%;
        object-fit: cover;
        display: block;
      }
    }
  }

  .camera-shade {
    position: absolute;
    left: 0;
    right: 0;
    height: 70px;
    pointer-events: none;

    &.top-shade {
      top: 0;
      background: linear-gradient(180deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%);
    }

    &.bottom-shade {
      bottom: 0;
      background: linear-gradient(0deg, rgba(0, 0, 0, 0.6) 0%, transparent 100%);
    }
  }

  .cam-overlay-row {
    position: absolute;
    left: 12px;
    right: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    z-index: 2;

    &.top-row {
      top: 12px;

      .cam-title-badge {
        display: flex;
        align-items: center;
        gap: 6px;
        color: #ffffff;

        .cam-signal-icon {
          width: 14px;
          height: 14px;
          color: #ffffff;
        }

        .cam-label-txt {
          font-size: 15px;
          font-weight: 600;
        }
      }

      .cam-frosted-btn {
        width: 32px;
        height: 32px;
        border-radius: 8px;
        border: none;
        background: rgba(255, 255, 255, 0.25);
        backdrop-filter: blur(8px);
        color: #ffffff;
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;

        svg { width: 14px; height: 14px; }
      }
    }

    &.bottom-row {
      bottom: 12px;

      .cam-counter-txt {
        font-size: 13.5px;
        font-weight: 700;
        color: #ffffff;
      }

      .cam-dots {
        display: flex;
        align-items: center;
        gap: 5px;

        .cam-dot {
          width: 6px;
          height: 6px;
          border-radius: 9999px;
          background: rgba(255, 255, 255, 0.45);
          cursor: pointer;
          transition: all 0.25s ease;

          &.active {
            width: 14px;
            background: #ffffff;
          }
        }
      }

      .cam-controls-group {
        display: flex;
        gap: 4px;

        .cam-square-btn {
          width: 32px;
          height: 32px;
          border-radius: 8px;
          border: none;
          background: rgba(255, 255, 255, 0.25);
          backdrop-filter: blur(8px);
          color: #ffffff;
          display: flex;
          align-items: center;
          justify-content: center;
          cursor: pointer;

          svg { width: 14px; height: 14px; }
          .cam-btn-svg {
            width: 14px;
            height: 14px;
            filter: brightness(0) invert(1);
          }

          &:hover {
            background: rgba(255, 255, 255, 0.4);
          }
        }
      }
    }
  }
}

/* Metrics Cards Matrix (525.5px × 470px, 2 Rows × 3 Columns) */
.metrics-cards-grid {
  width: 100%;
  height: 470px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: repeat(2, 1fr);
  gap: 8px;
  box-sizing: border-box;
}

.metric-card {
  border-radius: 8px;
  padding: 14px 16px;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  cursor: pointer;
  transition: transform 0.15s ease;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.04);

  &:hover {
    transform: translateY(-1px);
  }

  .m-card-top {
    display: flex;
    justify-content: space-between;
    align-items: center;

    .m-title-flex {
      display: flex;
      align-items: center;
      gap: 6px;

      .m-svg-icon {
        width: 18px;
        height: 18px;
      }

      .m-label {
        font-size: 16px;
        font-weight: 600;
      }
    }

    .m-corner-arrow-btn {
      width: 32px;
      height: 32px;
      border-radius: 8px;
      border: none;
      display: flex;
      align-items: center;
      justify-content: center;
      cursor: pointer;

      svg {
        width: 14px;
        height: 14px;
      }

      &.frosted-arrow {
        background: rgba(255, 255, 255, 0.2);
        color: #ffffff;
      }

      &.grey-arrow {
        background: #f4f4f4;
        color: #333333;
      }
    }
  }

  .m-value-flex {
    display: flex;
    align-items: baseline;
    gap: 8px;

    .val-num-unit {
      display: flex;
      align-items: baseline;
      gap: 2px;

      .val-num {
        font-size: 38px;
        font-weight: 700;
        letter-spacing: -0.02em;
        line-height: 1;
      }

      .val-unit {
        font-size: 17px;
        font-weight: 500;
      }
    }

    .status-pill-white {
      background: #ffffff;
      padding: 3px 8px;
      border-radius: 9999px;

      .status-pill-txt {
        font-size: 12.5px;
        font-weight: 700;
        color: #17b26a;
      }
    }
  }

  .m-bottom-desc {
    margin: 0;
    font-size: 13px;
    line-height: 1.35;
  }

  &.plant-health-card {
    background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);

    .white-txt { color: #ffffff; }
    .white-svg { filter: brightness(0) invert(1); }
  }

  &.default-metric-card {
    background: #ffffff;

    .dark-txt { color: #333333; }
    .muted-txt { color: #a4a4a4; }
  }
}

@keyframes scanLaser {
  0% { top: 0%; opacity: 0; }
  15% { opacity: 1; }
  85% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

@keyframes pulse {
  0% { transform: scale(0.95); opacity: 0.7; }
  100% { transform: scale(1.15); opacity: 1; }
}

@keyframes pulseBtn {
  0% {
    box-shadow: 0 0 0 0 rgba(23, 178, 106, 0.5);
  }
  70% {
    box-shadow: 0 0 0 6px rgba(23, 178, 106, 0);
  }
  100% {
    box-shadow: 0 0 0 0 rgba(23, 178, 106, 0);
  }
}

@keyframes spin {
  to { transform: rotate(360deg); }
}


/* ════════════════════ 3. MODALS & DRAWERS ════════════════════ */
.modal-backdrop-blur {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.45);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
}

.tanee-modal-card {
  width: 500px;
  max-width: 90vw;
  background: #ffffff;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 12px 36px rgba(0, 0, 0, 0.2);
  display: flex;
  flex-direction: column;

  &.large {
    width: 820px;
  }

  .t-modal-head {
    padding: 16px 20px;
    background: #f8f8f8;
    border-bottom: 1px solid #ebebeb;
    display: flex;
    justify-content: space-between;
    align-items: center;

    .head-title-flex {
      display: flex;
      align-items: center;
      gap: 10px;

      .modal-head-icon {
        width: 20px;
        height: 20px;
      }

      h4 { margin: 0; font-size: 16px; color: #333333; }
    }

    .modal-close-btn {
      background: none;
      border: none;
      font-size: 16px;
      cursor: pointer;
      color: #a4a4a4;
      &:hover { color: #333333; }
    }
  }

  .t-modal-body {
    padding: 20px;
    display: flex;
    flex-direction: column;
    gap: 12px;

    &.charts-grid-layout {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 16px;

      .chart-tile-box {
        h5 { margin: 0 0 10px 0; font-size: 13px; color: #333333; }
        .chart-canvas-div { width: 100%; height: 260px; }
      }
    }
  }
}

.alert-box-item {
  background: #f8f8f8;
  border-radius: 8px;
  padding: 12px 14px;
  border-left: 4px solid #a4a4a4;

  &.warning { border-left-color: #f9ad19; }
  &.urgent { border-left-color: #f04d28; }
  &.info { border-left-color: #17b26a; }

  .alert-item-head {
    display: flex;
    justify-content: space-between;
    font-size: 13px;
    margin-bottom: 4px;
    .alert-time { font-size: 11px; color: #a4a4a4; }
  }

  p { margin: 0; font-size: 12px; color: #666666; line-height: 1.4; }
}

/* ════════════════════ Dynamic Island · 灵动岛 AI 问答 ════════════════════ */
.dyn-island {
  position: absolute;
  top: 21px;
  left: 730px;
  width: 112px;
  height: 34px;
  border-radius: 17px;
  background: #0b0d10;
  box-shadow: 0 6px 22px rgba(0, 0, 0, 0.30), inset 0 0 0 1px rgba(255, 255, 255, 0.07);
  overflow: hidden;
  z-index: 800;

  /* 收起态：胶囊内容 */
  .dyn-island-pill {
    position: absolute;
    inset: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 7px;
    color: #ffffff;
    cursor: pointer;
    opacity: 1;

    .pill-live-dot {
      width: 7px;
      height: 7px;
      border-radius: 9999px;
      background: #17b26a;
      box-shadow: 0 0 8px rgba(23, 178, 106, 0.9);
      animation: pulse 1.6s infinite;
      flex-shrink: 0;
    }

    .pill-title-txt {
      font-size: 11.5px;
      font-weight: 600;
      letter-spacing: 0.3px;
      white-space: nowrap;
    }

    .pill-sparkle {
      width: 11px;
      height: 11px;
      color: #35c56e;
      flex-shrink: 0;
    }
  }

  /* 展开态：AI 问答面板（常驻挂载，初始透明 + 禁点击）
     固定 560×620：容器形变时仅裁剪不重排，保证滑动全程满帧 */
  .dyn-island-panel {
    position: absolute;
    top: 0;
    left: 0;
    width: 560px;
    height: 620px;
    display: flex;
    flex-direction: column;
    background: linear-gradient(180deg, #12151a 0%, #0b0d10 100%);
    color: #e8eaed;
    cursor: default;
    opacity: 0;
  }

  &.open .dyn-island-pill { pointer-events: none; }
  &:not(.open) .dyn-island-panel { pointer-events: none; }

  .di-head {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;

    .di-avatar-pill {
      background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
      color: #ffffff;
      font-size: 11px;
      font-weight: 700;
      padding: 5px 9px;
      border-radius: 8px;
      flex-shrink: 0;
    }

    .di-head-txt {
      flex: 1;
      min-width: 0;

      h4 {
        margin: 0;
        font-size: 13.5px;
        color: #f2f4f6;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      small { color: #17b26a; font-size: 10.5px; }
    }

    .di-collapse-btn {
      width: 28px;
      height: 28px;
      border: none;
      border-radius: 8px;
      background: rgba(255, 255, 255, 0.08);
      color: #cfd4da;
      cursor: pointer;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      svg { width: 14px; height: 14px; }
      &:hover { background: rgba(255, 255, 255, 0.16); color: #ffffff; }
    }
  }

  .di-messages {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    padding: 14px;
    display: flex;
    flex-direction: column;
    gap: 10px;

    &::-webkit-scrollbar { width: 5px; }
    &::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.16); border-radius: 3px; }

    .di-msg-row {
      display: flex;
      &.user { justify-content: flex-end; }
      &.ai { justify-content: flex-start; }

      .di-msg-bubble {
        max-width: 82%;
        padding: 9px 13px;
        border-radius: 12px;
        font-size: 12.5px;
        line-height: 1.55;

        .di-search-tag {
          font-size: 10px;
          color: #4ade80;
          margin-bottom: 4px;
          font-weight: 600;
        }

        /* 思考中气泡：三点弹跳 */
        &.thinking {
          display: inline-flex;
          align-items: center;
          gap: 5px;

          .think-dot {
            width: 6px;
            height: 6px;
            border-radius: 9999px;
            background: #4ade80;
            animation: think-bounce 1.1s ease-in-out infinite;

            &:nth-child(2) { animation-delay: 0.16s; }
            &:nth-child(3) { animation-delay: 0.32s; }
          }

          .think-label {
            margin-left: 3px;
            font-size: 11.5px;
            color: rgba(232, 234, 237, 0.72);
          }
        }

        /* 流式输出中：末尾跟随绿色光标 */
        &.streaming :deep(.msg-md > :last-child::after) {
          content: '';
          display: inline-block;
          width: 6px;
          height: 13px;
          margin-left: 3px;
          vertical-align: -2px;
          background: #35c56e;
          border-radius: 1px;
          animation: caret-blink 0.85s steps(1, end) infinite;
        }

        /* AI 回复 markdown 渲染样式（v-html 内容需 :deep 穿透） */
        :deep(.msg-md) {
          word-break: break-word;

          p {
            margin: 0 0 6px;
            &:last-child { margin-bottom: 0; }
          }

          h1, h2, h3, h4, h5 {
            margin: 8px 0 6px;
            font-size: 13px;
            font-weight: 700;
            color: #ffffff;
            &:first-child { margin-top: 0; }
          }

          ul, ol {
            margin: 4px 0;
            padding-left: 18px;

            li { margin: 2px 0; }
          }

          strong { color: #ffffff; font-weight: 700; }

          code {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 11.5px;
            background: rgba(255, 255, 255, 0.1);
            padding: 1px 5px;
            border-radius: 4px;
            color: #7ee2a8;
          }

          pre {
            background: rgba(0, 0, 0, 0.45);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 8px;
            padding: 10px 12px;
            margin: 6px 0;
            overflow-x: auto;

            code {
              background: none;
              padding: 0;
              color: #d7dce2;
              line-height: 1.6;
            }
          }

          blockquote {
            margin: 6px 0;
            padding: 4px 10px;
            border-left: 3px solid #35c56e;
            background: rgba(53, 197, 110, 0.08);
            border-radius: 0 6px 6px 0;
            color: rgba(232, 234, 237, 0.85);

            p { margin: 2px 0; }
          }

          table {
            border-collapse: collapse;
            margin: 6px 0;
            font-size: 11.5px;
            display: block;
            max-width: 100%;
            overflow-x: auto;

            th, td {
              border: 1px solid rgba(255, 255, 255, 0.14);
              padding: 5px 9px;
              text-align: left;
            }

            th {
              background: rgba(255, 255, 255, 0.08);
              color: #ffffff;
              font-weight: 600;
              white-space: nowrap;
            }

            tr:nth-child(even) td { background: rgba(255, 255, 255, 0.04); }
          }

          a { color: #6ee7b0; text-decoration: underline; }

          hr { border: none; border-top: 1px solid rgba(255, 255, 255, 0.14); margin: 8px 0; }
        }
      }

      &.user .di-msg-bubble {
        background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
        color: #ffffff;
        border-bottom-right-radius: 3px;
      }

      &.ai .di-msg-bubble {
        background: rgba(255, 255, 255, 0.07);
        color: #e8eaed;
        border-bottom-left-radius: 3px;
      }
    }

    .di-tool-status {
      display: flex;
      align-items: center;
      gap: 6px;
      font-size: 11px;
      color: #4ade80;
      padding: 6px 12px;
      background: rgba(23, 178, 106, 0.12);
      border-radius: 8px;
      align-self: flex-start;

      .spinner-dot {
        width: 8px;
        height: 8px;
        border-radius: 9999px;
        background: #17b26a;
        animation: pulse 1s infinite;
      }
    }
  }

  .di-quick-row {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;
    padding: 8px 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.06);
    flex-shrink: 0;

    .di-quick-pill {
      font-size: 10.5px;
      background: rgba(255, 255, 255, 0.06);
      border: 1px solid rgba(255, 255, 255, 0.12);
      padding: 4px 9px;
      border-radius: 9999px;
      cursor: pointer;
      color: #cfd4da;

      &:hover { border-color: #17b26a; color: #4ade80; }
    }
  }

  .di-input-bar {
    display: flex;
    gap: 8px;
    padding: 12px 14px;
    border-top: 1px solid rgba(255, 255, 255, 0.08);
    flex-shrink: 0;

    .di-input {
      flex: 1;
      min-width: 0;
      background: rgba(255, 255, 255, 0.07);
      border: 1px solid rgba(255, 255, 255, 0.12);
      border-radius: 9px;
      padding: 8px 12px;
      font-size: 12.5px;
      color: #e8eaed;
      outline: none;

      &::placeholder { color: #8a919a; }
      &:focus { border-color: #17b26a; }
    }

    .di-send-btn {
      background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
      color: #ffffff;
      border: none;
      padding: 0 16px;
      border-radius: 9px;
      font-size: 12.5px;
      font-weight: 700;
      cursor: pointer;

      &:disabled { opacity: 0.55; cursor: default; }
    }
  }
}

/* ════════════════════ 界面配色（主题切换） ════════════════════ */
.theme-menu-wrap {
  position: relative;
  display: flex;
  justify-content: center;
}

.theme-popover-mask {
  position: fixed;
  inset: 0;
  z-index: 940;
}

.theme-popover {
  position: absolute;
  bottom: 72px;
  left: 44px;
  width: 168px;
  background: #ffffff;
  border-radius: 12px;
  box-shadow: 0 10px 32px rgba(0, 0, 0, 0.18);
  padding: 10px;
  z-index: 950;
  cursor: default;

  h6 {
    margin: 2px 6px 8px;
    font-size: 11px;
    color: #a4a4a4;
    font-weight: 600;
  }

  .theme-option-row {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 8px;
    border: none;
    background: none;
    padding: 7px 6px;
    border-radius: 8px;
    cursor: pointer;
    font-size: 12.5px;
    color: #333333;

    &:hover { background: #f5f5f5; }
    &.active { background: #f0fdf4; color: #178a56; font-weight: 600; }

    .theme-swatch {
      width: 16px;
      height: 16px;
      border-radius: 9999px;
      border: 1px solid rgba(0, 0, 0, 0.12);
      flex-shrink: 0;

      &.sw-light { background: #ffffff; }
      &.sw-dark { background: #14161a; }
      &.sw-green { background: #cfe3c0; }
    }

    .theme-name { flex: 1; text-align: left; }
    .theme-check { width: 14px; height: 14px; flex-shrink: 0; }
  }
}

.pop-fade-enter-active, .pop-fade-leave-active { transition: opacity 0.18s ease, transform 0.18s ease; }
.pop-fade-enter-from, .pop-fade-leave-to { opacity: 0; transform: translateY(6px); }

/* 主题滤镜：深色 = 反相+色相回旋；青绿 = 轻度棕绿调 */
.tanee-dashboard-artboard {
  transition: filter 0.45s ease;

  &.theme-dark {
    filter: invert(1) hue-rotate(180deg);

    /* 照片/实景图反相还原，保持自然色彩 */
    img, video { filter: invert(1) hue-rotate(180deg); }

    /* 灵动岛与主题弹层保持原配色 */
    .dyn-island, .theme-popover { filter: invert(1) hue-rotate(180deg); }
  }

  &.theme-green {
    filter: sepia(0.22) hue-rotate(28deg) saturate(1.35) brightness(0.99);
  }
}

/* ════════════════════ 个人中心 Modal ════════════════════ */
.profile-modal-card { width: 440px; }

.profile-body {
  .profile-id-card {
    display: flex;
    gap: 14px;
    align-items: center;

    .profile-avatar-circle {
      width: 56px;
      height: 56px;
      border-radius: 9999px;
      background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
      color: #ffffff;
      font-size: 22px;
      font-weight: 700;
      display: flex;
      align-items: center;
      justify-content: center;
      box-shadow: 0 4px 12px rgba(53, 197, 110, 0.3);
      flex-shrink: 0;
    }

    .profile-id-info {
      min-width: 0;

      h3 { margin: 0 0 6px; font-size: 17px; color: #1e2024; }

      .profile-role-tags {
        display: flex;
        gap: 6px;
        margin-bottom: 6px;

        .role-tag {
          font-size: 10.5px;
          padding: 2px 8px;
          border-radius: 9999px;
          font-weight: 600;

          &.green { background: #f0fdf4; color: #178a56; border: 1px solid #b7e4c9; }
          &.gray { background: #f5f5f5; color: #666666; border: 1px solid #e5e5e5; }
        }
      }

      p { margin: 0; font-size: 11px; color: #a4a4a4; line-height: 1.4; }
    }
  }

  .profile-stats-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 10px;

    .profile-stat-cell {
      background: #f8f8f8;
      border-radius: 10px;
      padding: 12px 8px;
      text-align: center;

      strong { display: block; font-size: 20px; color: #178a56; }
      span { font-size: 10.5px; color: #a4a4a4; }
    }
  }

  .profile-info-rows {
    background: #ffffff;
    border: 1px solid #f0f0f0;
    border-radius: 10px;
    overflow: hidden;

    .profile-info-row {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 14px;
      font-size: 12.5px;

      & + .profile-info-row { border-top: 1px solid #f5f5f5; }

      span { color: #a4a4a4; }
      strong { color: #333333; font-weight: 600; }
    }
  }

  .profile-action-bar {
    display: flex;
    gap: 10px;

    .profile-secondary-btn {
      flex: 1;
      border: 1px solid #dcdcdc;
      background: #ffffff;
      border-radius: 9px;
      padding: 9px 0;
      font-size: 13px;
      color: #333333;
      font-weight: 600;
      cursor: pointer;

      &:hover { border-color: #178a56; color: #178a56; }
    }

    .profile-primary-btn {
      flex: 1;
      border: none;
      background: linear-gradient(135deg, #35c56e 0%, #2e9055 100%);
      border-radius: 9px;
      padding: 9px 0;
      font-size: 13px;
      color: #ffffff;
      font-weight: 700;
      cursor: pointer;

      &:hover { filter: brightness(1.05); }
    }
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@keyframes think-bounce {
  0%, 70%, 100% { transform: translateY(0); opacity: 0.4; }
  35% { transform: translateY(-4px); opacity: 1; }
}

@keyframes caret-blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
}
</style>
