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

          <!-- Main Navigation -->
          <nav class="menu-container upper">
            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'home' }"
              @click="activeNav = 'home'; showDiagWorkstation = false"
              title="总览仪表盘"
            >
              <img src="/tanee/svg/dashboard/icon-16.svg" alt="Home" class="nav-svg-icon white-filter"/>
              <span class="nav-label">首页</span>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'knowledge' }"
              @click="activeNav = 'knowledge'; openKnowledge()"
              title="病害图鉴与防治知识库"
            >
              <!-- Book / Knowledge Base Icon -->
              <svg class="nav-svg-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
                <path d="M3 4.5C3 3.7 3.7 3 4.5 3H9v14H4.5C3.7 17 3 16.3 3 15.5V4.5Z"/>
                <path d="M17 4.5C17 3.7 16.3 3 15.5 3H11v14h4.5c.8 0 1.5-.7 1.5-1.5V4.5Z"/>
                <line x1="5.5" y1="6.5" x2="7" y2="6.5"/>
                <line x1="13" y1="6.5" x2="14.5" y2="6.5"/>
              </svg>
              <span class="nav-label">病害图鉴</span>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'decision' }"
              @click="activeNav = 'decision'; activeModal = 'djiShop'"
              title="无人机推荐 · DJI 商城"
            >
              <el-icon :size="20"><Aim /></el-icon>
              <span class="nav-label">无人机推荐</span>
            </button>

            <button
              class="nav-item-btn"
              :class="{ active: activeNav === 'settings' }"
              @click="activeNav = 'settings'"
              title="系统设置"
            >
              <el-icon :size="20"><Setting /></el-icon>
              <span class="nav-label">系统设置</span>
            </button>
          </nav>

          <!-- Lower Menu Navigation (Pinned to bottom: Theme, User) -->
          <div class="menu-container lower">
            <div class="theme-menu-wrap">
              <button
                class="nav-tile-btn"
                :class="{ active: themeMenuOpen }"
                @click.stop="themeMenuOpen = !themeMenuOpen"
                title="切换界面配色"
              >
                <!-- Sun / Brightness Icon -->
                <svg class="nav-svg-icon" viewBox="0 0 20 20" fill="none" stroke="currentColor" stroke-width="1.8">
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

            <button class="brand-tile" @click="activeModal = 'profile'" title="个人中心">
              <svg class="plant-icon" viewBox="0 0 24 24" fill="none" stroke="#7fa08d" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round">
                <path d="M12 21V11"/>
                <path d="M12 11C12 7.5 9.5 5 6 5C6 8.5 8.5 11 12 11Z" fill="#5f8a72" stroke="none"/>
                <path d="M12 13C12 10 14.2 8 17.5 8C17.5 11 15.3 13 12 13Z" fill="#4c7a5f" stroke="none"/>
              </svg>
              <span class="brand-tile-text">让农业更智能<br />让丰收更简单</span>
            </button>
          </div>
        </aside>

        <!-- ════════════════════ 2. BODY (1091px × 834px) ════════════════════ -->
        <main class="tanee-body">
          <!-- 2.1 Header (1091px × 76px) -->
          <header class="tanee-header">
            <h1 class="header-title">玉米叶部病斑多尺度自适应感知与飞防决策系统</h1>

            <div class="header-right-tools">
              <!-- 告警按钮：数量来自 /screen/alerts（诊断自动生成），不再是写死的 3 条
                   Magic UI · PulsatingButton — 有未读时才呼吸 -->
              <PulsatingButton
                class="alerts-pill-btn"
                :class="{ 'has-unread': alertStats.unread > 0 }"
                pulse-color="rgba(23, 178, 106, 0.55)"
                duration="1.8s"
                distance="10px"
                @click="openAlerts"
                title="农场告警"
              >
                <div class="notif-box">
                  <img src="/tanee/svg/dashboard/icon-7.svg" alt="告警" class="bell-svg"/>
                </div>
                <span class="alerts-txt">{{ alertStats.unread }} 条告警</span>
                <svg class="arrow-up-right-svg" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M4 12L12 4M12 4H6M12 4V10"/>
                </svg>
              </PulsatingButton>

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

                    <div class="canvas-right-group">
                      <button class="canvas-action-btn ghost" @click="openBatch" title="一次识别多张巡田照片">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">
                          <rect x="1.6" y="3.2" width="8.4" height="8.4" rx="1.4"/>
                          <rect x="6" y="6" width="8.4" height="8.4" rx="1.4"/>
                        </svg>
                        <span>批量识别</span>
                      </button>
                      <button class="canvas-action-btn ghost" @click="openHistory" title="回看历史诊断记录">
                        <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.6">
                          <circle cx="8" cy="8" r="6.2"/><path d="M8 4.8V8l2.4 1.6"/>
                        </svg>
                        <span>历史记录</span>
                      </button>
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
                    <h4 class="dd-disease-title">{{ rejectNotice ? '非目标图像（已拒识）' : (isDetected ? (currentSample?.diseaseName || '玉米大斑病 (Northern Corn Leaf Blight)') : (isDetecting ? 'AI 正在推理中...' : '待检测样本（等待诊断）')) }}</h4>
                    <span class="dd-pathogen-txt">{{ rejectNotice ? '未检测到玉米叶片，本张图片不参与病害统计与处方生成' : (isDetected ? (currentSample?.pathogen || '病原菌：真菌，大斑凸脐蠕孢 (Exserohilum turcicum)') : (isDetecting ? '深度卷积注意力网络正在提取叶片表征特征...' : '尚未执行 AI 推理，请点击上方【开始诊断】按钮')) }}</span>
                  </div>
                  <div class="dd-severity-badge" :style="{ backgroundColor: rejectNotice ? '#b42318' : (isDetected ? (currentSample?.color || '#e28557') : (isDetecting ? '#3b82f6' : '#667085')) }">
                    {{ rejectNotice ? '拒识' : (isDetected ? (currentSample?.severity || '中度 (II 级扩展期)') : (isDetecting ? '推理中...' : '待诊断')) }}
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

                    <div v-if="rejectNotice" class="rx-reject-notice">
                      ⚠️ {{ rejectNotice }}
                    </div>

                    <p class="flight-prescription-txt" :class="{ 'waiting-txt': !isDetected }">
                      {{
                        rejectNotice
                          ? '本次未生成处方：图像中未检测到玉米叶片。请对准叶片、避免逆光与强反光后重新拍摄。'
                          : (isDetected
                              ? (currentSample?.prescription || '')
                              : (isDetecting
                                  ? '正在结合病斑注意力多尺度特征评估施药剂量与无人机航行参数...'
                                  : '图片已成功载入。请点击上方【开始诊断】按钮，系统将调用 ResNet50-CBAM 模型进行病斑多尺度定位与无人机处方生成。'))
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
                        <span class="dp-v">{{ isDetected ? droneDroplet : '--' }}</span>
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
                      <span class="check-icon">{{ rejectNotice ? '!' : (isDetected ? '✓' : 'ℹ') }}</span>
                      <span>{{ rejectNotice ? '未通过叶片校验，本次不进入用药与飞防参数计算' : (isDetected ? '当前风速 2m/s、温度 19°C 满足低空飞防窗口，无漂移药害风险' : '待诊断完成后，系统将根据病斑受损率与气象窗口生成施药决策') }}</span>
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
                  <!-- Magic UI · ShineBorder — 卡片边缘流光 -->
                  <ShineBorder :border-width="3" :duration="7" :shine-color="['#8DF3B8', '#17B26A', '#0F9755']" />

                  <!-- Location & Time Bar -->
                  <div class="wp-top-bar">
                    <div class="wp-loc-tag">
                      <svg class="pin-svg" viewBox="0 0 16 16" fill="none" stroke="#333333" stroke-width="2">
                        <path d="M8 14C8 14 13 9.5 13 6C13 3.23858 10.7614 1 8 1C5.23858 1 3 3.23858 3 6C3 9.5 8 14 8 14Z"/>
                        <circle cx="8" cy="6" r="2" fill="#333333"/>
                      </svg>
                      <span class="loc-text">贵阳 · 乌当</span>
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
                  <!-- Magic UI · BorderBeam — 实时画面光带 -->
                  <BorderBeam :size="140" :duration="4" color-from="#B9FBD4" color-to="#17B26A" :border-width="3" />

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
                <MagicCard
                  class="metric-card plant-health-card"
                  background="linear-gradient(135deg, #35c56e 0%, #2e9055 100%)"
                  gradient-color="#ffffff"
                  :gradient-opacity="0.22"
                  gradient-from="#BFF3D5"
                  gradient-to="#8DF3B8"
                  border-color="rgba(255, 255, 255, 0.3)"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <!-- Magic UI · ShineBorder — 主卡流转高光 -->
                    <ShineBorder :border-width="3" :duration="9" :shine-color="['#ffffff', '#8DF3B8', '#ffffff']" />
                  </template>
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
                      <NumberTicker :value="plantHealthValue" class="val-num white-txt" />
                      <span class="val-unit white-txt">%</span>
                    </div>
                    <div class="status-pill-white">
                      <span class="status-pill-txt">良好</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc white-txt">作物长势旺盛，健康状态优异</p>
                </MagicCard>

                <!-- Card 2: Wind (Fills: #FFFFFF) -->
                <MagicCard
                  class="metric-card default-metric-card"
                  background="#ffffff"
                  gradient-color="#17B26A"
                  :gradient-opacity="0.1"
                  gradient-from="#CBEFDD"
                  gradient-to="#E6F7EE"
                  border-color="#F0F1F3"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <ShineBorder :border-width="2.5" :duration="6.5" :shine-color="['#CBEFDD', '#17B26A', '#E6F7EE']" />
                  </template>
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
                      <NumberTicker :value="2" class="val-num dark-txt" />
                      <span class="val-unit muted-txt">m/s</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">请保持温室内空气充分流通</p>
                </MagicCard>

                <!-- Card 3: Temperature (Fills: #FFFFFF) -->
                <MagicCard
                  class="metric-card default-metric-card"
                  background="#ffffff"
                  gradient-color="#17B26A"
                  :gradient-opacity="0.1"
                  gradient-from="#CBEFDD"
                  gradient-to="#E6F7EE"
                  border-color="#F0F1F3"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <ShineBorder :border-width="2.5" :duration="7.5" :shine-color="['#CBEFDD', '#17B26A', '#E6F7EE']" />
                  </template>
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
                      <NumberTicker :value="19" class="val-num dark-txt" />
                      <span class="val-unit muted-txt">°C</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">建议稳定维持在 15°C 至 20°C</p>
                </MagicCard>

                <!-- Card 4: pH Level (Fills: #FFFFFF) -->
                <MagicCard
                  class="metric-card default-metric-card"
                  background="#ffffff"
                  gradient-color="#17B26A"
                  :gradient-opacity="0.1"
                  gradient-from="#CBEFDD"
                  gradient-to="#E6F7EE"
                  border-color="#F0F1F3"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <ShineBorder :border-width="2.5" :duration="8.5" :shine-color="['#CBEFDD', '#17B26A', '#E6F7EE']" />
                  </template>
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
                      <NumberTicker :value="7.6" :decimal-places="1" class="val-num dark-txt" />
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">可施加酸性堆肥平衡 pH 值</p>
                </MagicCard>

                <!-- Card 5: Humidity (Fills: #FFFFFF) -->
                <MagicCard
                  class="metric-card default-metric-card"
                  background="#ffffff"
                  gradient-color="#17B26A"
                  :gradient-opacity="0.1"
                  gradient-from="#CBEFDD"
                  gradient-to="#E6F7EE"
                  border-color="#F0F1F3"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <ShineBorder :border-width="2.5" :duration="9.5" :shine-color="['#CBEFDD', '#17B26A', '#E6F7EE']" />
                  </template>
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
                      <NumberTicker :value="82" class="val-num dark-txt" />
                      <span class="val-unit muted-txt">%</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">湿度适宜，可有效抑制霉菌滋生</p>
                </MagicCard>

                <!-- Card 6: Soil Moisture (Fills: #FFFFFF) -->
                <MagicCard
                  class="metric-card default-metric-card"
                  background="#ffffff"
                  gradient-color="#17B26A"
                  :gradient-opacity="0.1"
                  gradient-from="#CBEFDD"
                  gradient-to="#E6F7EE"
                  border-color="#F0F1F3"
                  @click="activeModal = 'telemetry'"
                >
                  <template #overlay>
                    <ShineBorder :border-width="2.5" :duration="10.5" :shine-color="['#CBEFDD', '#17B26A', '#E6F7EE']" />
                  </template>
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
                      <NumberTicker :value="65" class="val-num dark-txt" />
                      <span class="val-unit muted-txt">%</span>
                    </div>
                  </div>
                  <p class="m-bottom-desc muted-txt">请持续监测，保持水分稳定</p>
                </MagicCard>
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
              <button class="di-head-btn" @click="toggleSessionHistory" :title="showHistory ? '返回对话' : '历史会话'">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                  <circle cx="8" cy="8" r="6"/>
                  <path d="M8 4.8V8l2.2 1.4" stroke-linecap="round"/>
                </svg>
              </button>
              <button class="di-head-btn" @click="startNewSession" title="新会话">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path d="M8 3.2v9.6M3.2 8h9.6" stroke-linecap="round"/>
                </svg>
              </button>
              <button class="di-collapse-btn" @click="closeIsland" title="收起灵动岛">
                <svg viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="2">
                  <path d="M3 10L8 5L13 10"/>
                </svg>
              </button>
            </div>
            <!-- 历史会话找回视图（对齐 claude --resume：列出落盘会话，点击即接着聊） -->
            <div v-if="showHistory" class="di-history">
              <div class="di-history-head">
                <span class="di-history-title">历史会话</span>
                <span class="di-history-sub">{{ sessionList.length ? '共 ' + sessionList.length + ' 段' : '' }}</span>
              </div>
              <div class="di-history-list">
                <template v-if="loadingSessions">
                  <div class="di-history-empty">正在加载历史会话...</div>
                </template>
                <template v-else-if="loadError">
                  <!-- 失败态必须与空态区分：404=后端未重启（旧版无此路由），其余=网络异常。
                       此前失败被静默吞掉显示成「暂无历史会话」，误导为没有历史数据 -->
                  <div class="di-history-empty di-history-failed">
                    <p>{{ loadError === 404 ? '后端服务版本较旧，请重启后端后重试' : '会话服务连接失败，请检查后端' }}</p>
                    <button class="di-history-retry" @click="fetchSessionList">重试</button>
                  </div>
                </template>
                <template v-else-if="!sessionList.length">
                  <div class="di-history-empty">暂无历史会话</div>
                </template>
                <template v-else>
                  <div
                    v-for="s in sessionList"
                    :key="s.session_id"
                    class="di-history-item"
                    :class="{ active: s.session_id === activeSessionId }"
                    @click="restoreSession(s)"
                  >
                    <div class="di-history-main">
                      <div class="di-history-name">{{ s.title }}</div>
                      <div class="di-history-meta">
                        <span>{{ s.modified }}</span>
                        <span v-if="s.interrupted" class="di-history-tag">中断 · 可继续</span>
                      </div>
                    </div>
                    <button
                      class="di-history-del"
                      :class="{ armed: pendingDeleteId === s.session_id }"
                      @click.stop="removeSession(s)"
                    >{{ pendingDeleteId === s.session_id ? '确认删除' : '✕' }}</button>
                  </div>
                </template>
              </div>
            </div>
            <div v-show="!showHistory" class="di-messages" ref="chatBodyRef">
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
                  <div v-if="msg.searchQuery" class="di-search-tag">🔍 已联网检索: {{ msg.searchQuery }}</div>
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
            <div v-show="!showHistory" class="di-quick-row">
              <span
                v-for="(q, qi) in fastQuestions"
                :key="qi"
                class="di-quick-pill"
                @click="askQuestion(q)"
              >
                {{ q }}
              </span>
            </div>
            <div v-show="!showHistory" class="di-input-bar">
              <input
                v-model="inputText"
                @keyup.enter="sendMessage"
                placeholder="询问对症药剂、气象抑制阈值或无人机施药参数..."
                class="di-input"
              />
              <button class="di-send-btn" @click="aiTyping ? stopChat() : sendMessage()">
                {{ aiTyping ? '停止' : '发送' }}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- ════════════════════ 3. INTERACTIVE DRAWERS & MODALS ════════════════════ -->

    <!-- Alerts Drawer（告警来自 /screen/alerts，由诊断结果自动生成） -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'alerts'" @click.self="activeModal = null">
      <div class="tanee-modal-card alerts-modal-card">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-7.svg" alt="Alert" class="modal-head-icon"/>
            <h4>{{ alertStats.unread }} 条未读告警</h4>
            <span class="alerts-total-chip">今日 {{ alertStats.today }} · 共 {{ alertStats.total }}</span>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body alerts-body">
          <div class="alerts-toolbar">
            <button class="alerts-tool-btn" :disabled="!alertStats.unread" @click="markAllAlertsRead">
              全部标为已读
            </button>
            <button class="alerts-tool-btn ghost" @click="loadAlerts">刷新</button>
            <label class="alerts-filter">
              <input type="checkbox" v-model="alertsUnreadOnly" @change="loadAlerts"/>
              只看未读
            </label>
          </div>

          <div v-if="alertsLoading" class="alerts-empty">正在加载告警...</div>
          <div v-else-if="alertsError" class="alerts-empty">{{ alertsError }}</div>
          <div v-else-if="!alerts.length" class="alerts-empty">
            暂无告警 —— 每次诊断会自动按规则生成（重病斑 / 低置信度 / 扩散风险）
          </div>

          <div v-else class="alerts-list">
            <div v-for="a in alerts" :key="a.id" class="alert-box-item" :class="alertLevelClass(a.level)" :style="{ opacity: a.isRead ? 0.62 : 1 }">
              <div class="alert-item-head">
                <strong>{{ alertIcon(a.level) }} {{ a.title }}</strong>
                <span class="alert-time">{{ fmtTime(a.created_at) }}</span>
              </div>
              <p>{{ a.detail }}</p>
              <div class="alert-actions">
                <button v-if="!a.isRead" class="alert-action-btn" @click="markAlertRead(a)">标为已读</button>
                <button class="alert-action-btn danger" @click="removeAlert(a)">删除</button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Diagnosis History Drawer（诊断历史 · SQLite 落盘） -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'history'" @click.self="activeModal = null">
      <div class="tanee-modal-card large history-modal-card">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-15.svg" alt="History" class="modal-head-icon"/>
            <h4>诊断历史记录</h4>
            <span v-if="historyStats" class="history-stat-chip">
              今日 {{ historyStats.today }} 次 · 共 {{ historyStats.total }} 条
            </span>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body history-body">
          <div v-if="historyLoading" class="history-empty">正在加载历史记录...</div>
          <div v-else-if="historyError" class="history-empty">
            {{ historyError }}
            <button class="history-retry-btn" @click="loadHistory">重试</button>
          </div>
          <div v-else-if="!historyDetail && !historyItems.length" class="history-empty">
            暂无诊断记录——去画布做一次「开始诊断」，记录会自动出现在这里
          </div>

          <!-- 详情视图 -->
          <div v-else-if="historyDetail" class="history-detail">
            <div class="history-detail-top">
              <button class="history-back-btn" @click="historyDetail = null">← 返回列表</button>
              <span class="history-detail-time">{{ fmtTime(historyDetail.created_at) }}</span>
            </div>
            <div class="history-detail-grid">
              <div class="history-img-box">
                <img v-if="historyDetail.thumb" :src="historyDetail.thumb" alt="原图"/>
                <div v-else class="history-img-empty">无图片</div>
                <span class="history-img-tag">原图</span>
              </div>
              <div class="history-img-box">
                <img v-if="historyDetail.heatmap" :src="historyDetail.heatmap" alt="Grad-CAM 热力图"/>
                <div v-else class="history-img-empty">本次未生成热力图</div>
                <span class="history-img-tag cam">Grad-CAM</span>
              </div>
            </div>
            <div class="history-detail-rows">
              <div class="hrow">
                <span>病害结论</span>
                <strong class="hi-name">{{ historyDetail.class_name }}
                  <em class="hi-en">{{ historyDetail.class_en }}</em>
                </strong>
              </div>
              <div class="hrow">
                <span>严重度 / 受损率</span>
                <strong>
                  <em class="hi-sev" :data-sev="historyDetail.severity">{{ historyDetail.severity }}</em>
                  · {{ historyDetail.damage_rate }}%
                </strong>
              </div>
              <div class="hrow">
                <span>置信度 / 模型 / 耗时</span>
                <strong>{{ historyDetail.confidence }}% · {{ historyDetail.model_used }} · {{ historyDetail.inference_ms }}ms</strong>
              </div>
              <div class="hrow">
                <span>推荐机型</span>
                <strong>{{ historyDetail.droneParams?.model || '—' }}</strong>
              </div>
              <div class="hrow rx">
                <span>飞防处方</span>
                <strong>{{ historyDetail.prescription || '—' }}</strong>
              </div>
            </div>
          </div>

          <!-- 列表视图 -->
          <div v-else class="history-list">
            <div v-for="it in historyItems" :key="it.id" class="history-item" @click="openHistoryDetail(it.id)">
              <img v-if="it.thumb_small" :src="it.thumb_small" class="history-thumb" alt=""/>
              <div v-else class="history-thumb history-thumb-empty">🍃</div>
              <div class="history-item-main">
                <div class="hi-row1">
                  <strong>{{ it.class_name }}</strong>
                  <em class="hi-sev" :data-sev="it.severity">{{ it.severity }}</em>
                </div>
                <div class="hi-row2">
                  置信度 {{ it.confidence }}% · 受损率 {{ it.damage_rate }}% · {{ it.model_used }}
                </div>
              </div>
              <span class="history-item-time">{{ fmtTime(it.created_at) }}</span>
              <button class="history-del-btn" @click.stop="removeHistory(it.id)" title="删除该记录">✕</button>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Batch Recognition Drawer（批量巡田识别） -->
    <div class="modal-backdrop-blur" v-if="activeModal === 'batch'" @click.self="activeModal = null">
      <div class="tanee-modal-card large batch-modal-card">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <img src="/tanee/svg/dashboard/icon-15.svg" alt="Batch" class="modal-head-icon"/>
            <h4>批量巡田识别</h4>
            <span v-if="batchSummary" class="history-stat-chip">
              成功 {{ batchSummary.success }}/{{ batchSummary.count }} · 平均受损 {{ batchSummary.avgDamageRate }}%
            </span>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body batch-body">
          <input ref="batchInput" type="file" accept="image/*" multiple class="batch-file-input" @change="onBatchFiles"/>

          <div class="batch-picker" @click="batchInput && batchInput.click()">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
              <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5"/><path d="M4 15v3a2 2 0 002 2h12a2 2 0 002-2v-3"/>
            </svg>
            <strong>点击选择图片</strong>
            <span>支持多选 · 单次最多 {{ BATCH_MAX }} 张 · 自动压缩后上传</span>
          </div>

          <div v-if="batchFiles.length" class="batch-thumbs">
            <div v-for="(f, i) in batchFiles" :key="i" class="batch-thumb">
              <img :src="f.dataUrl" :alt="f.name"/>
              <span class="batch-thumb-name">{{ f.name }}</span>
              <button class="batch-thumb-del" @click.stop="removeBatchFile(i)" title="移除">✕</button>
            </div>
          </div>

          <div class="batch-actions">
            <button class="batch-run-btn" :disabled="!batchFiles.length || batchRunning" @click="runBatch">
              <span class="btn-spinner" v-if="batchRunning"></span>
              {{ batchRunning ? `识别中… 已用 ${batchElapsed}s` : '开始批量识别' }}
            </button>
            <button v-if="batchFiles.length && !batchRunning" class="batch-clear-btn" @click="resetBatch">清空</button>
            <span v-if="batchFiles.length && !batchRunning" class="batch-hint">已选 {{ batchFiles.length }} 张</span>
          </div>

          <div v-if="batchError" class="batch-error">{{ batchError }}</div>

          <div v-if="batchSummary" class="batch-summary">
            <div class="bs-cell"><strong>{{ batchSummary.success }}</strong><span>识别张数</span></div>
            <div class="bs-cell"><strong>{{ (batchSummary.acreage * batchSummary.success).toFixed(1) }} 亩</strong><span>覆盖面积</span></div>
            <div class="bs-cell"><strong>{{ batchSummary.totalVolumeLiters }} L</strong><span>建议药液量</span></div>
            <div class="bs-cell"><strong>{{ batchSummary.avgDamageRate }}%</strong><span>平均受损率</span></div>
            <div class="bs-cell"><strong>{{ batchSummary.avgConfidence }}%</strong><span>平均置信度</span></div>
          </div>

          <div v-if="batchSummary?.byClass?.length" class="batch-dist">
            <span class="batch-dist-label">病害分布</span>
            <span v-for="c in batchSummary.byClass" :key="c.class_en" class="batch-dist-chip"
                  :style="{ color: c.color, background: c.color + '1a', borderColor: c.color + '40' }">
              {{ c.name }} × {{ c.count }}
            </span>
          </div>

          <div v-if="batchSummary?.worst" class="batch-worst">
            最严重：<strong>{{ batchSummary.worst.diseaseName }}</strong>
            · {{ batchSummary.worst.severity }} · 受损率 {{ batchSummary.worst.damageRate }}%
            <span class="batch-worst-file">{{ batchSummary.worst.filename }}</span>
          </div>

          <div v-if="batchItems.length" class="batch-list">
            <div v-for="it in batchItems" :key="it.index" class="batch-item">
              <img v-if="it._thumb" :src="it._thumb" class="batch-item-thumb" alt=""/>
              <div class="batch-item-main">
                <div class="bi-row1">
                  <strong>{{ it.class_name_cn }}</strong>
                  <em class="hi-sev" :data-sev="sevKey(it.severity)">{{ sevKey(it.severity) }}</em>
                  <span class="bi-file">{{ it.filename }}</span>
                </div>
                <div class="bi-row2">
                  置信度 {{ it.confidence }}% · 受损率 {{ it.damageRate }}% ·
                  {{ it.droneParams?.model || '—' }} · {{ it.droneParams?.volume || '—' }} · {{ it.inference_ms }}ms
                </div>
                <div class="bi-rx">{{ it.prescription }}</div>
              </div>
            </div>
          </div>

          <div v-if="batchRejected.length" class="batch-rejected">
            <div class="batch-rejected-head">以下 {{ batchRejected.length }} 张未检测到玉米叶片，已拒识（不计入统计）</div>
            <div v-for="r in batchRejected" :key="r.index" class="batch-reject-row">
              <span class="br-name" :title="r.filename">{{ r.filename }}</span>
              <span class="br-reason" :title="r.reason">已拒识</span>
            </div>
          </div>

          <div v-if="batchErrors.length" class="batch-errors">
            <div v-for="e in batchErrors" :key="e.index" class="batch-error-row">
              第 {{ e.index + 1 }} 张（{{ e.filename }}）失败：{{ e.error }}
            </div>
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

    <!-- 病害图鉴 · 识别与防治知识库 Modal
         弹窗特效：shadcn / Magic UI registry「hero-video-dialog」spring dialog 编排的 Vue 移植
         （背景毛玻璃淡入 + 卡片 from-center spring 缩放 damping:30 / stiffness:300，关闭时反向收拢） -->
    <Transition :css="false" @enter="onKbDialogEnter" @leave="onKbDialogLeave">
    <div class="modal-backdrop-blur" v-if="activeModal === 'knowledge'" @click.self="activeModal = null">
      <div class="tanee-modal-card large">
        <div class="t-modal-head">
          <div class="head-title-flex">
            <svg class="modal-head-icon" viewBox="0 0 20 20" fill="none" stroke="#333333" stroke-width="1.8">
              <path d="M3 4.5C3 3.7 3.7 3 4.5 3H9v14H4.5C3.7 17 3 16.3 3 15.5V4.5Z"/>
              <path d="M17 4.5C17 3.7 16.3 3 15.5 3H11v14h4.5c.8 0 1.5-.7 1.5-1.5V4.5Z"/>
              <line x1="5.5" y1="6.5" x2="7" y2="6.5"/>
              <line x1="13" y1="6.5" x2="14.5" y2="6.5"/>
            </svg>
            <h4>病害图鉴 · 识别与防治知识库</h4>
          </div>
          <button class="modal-close-btn" @click="activeModal = null">✕</button>
        </div>
        <div class="t-modal-body kb-layout">
          <div class="kb-side">
            <button
              v-for="k in knowledgeItems"
              :key="k.class_name_en"
              class="kb-side-item"
              :class="{ active: knowledgeActiveId === k.class_name_en }"
              @click="knowledgeActiveId = k.class_name_en"
            >
              <span class="kb-dot" :style="{ background: k.color }"></span>
              {{ k.name_cn }}
            </button>
          </div>
          <div class="kb-detail" v-if="currentKnowledge">
            <div class="kb-hero" :style="{ borderLeftColor: currentKnowledge.color }">
              <img v-if="kbSampleImg" :src="kbSampleImg" class="kb-hero-img" alt="病害样本图"/>
              <div class="kb-hero-info">
                <h3>{{ currentKnowledge.name_cn }}</h3>
                <p class="kb-en">{{ currentKnowledge.name_en }}</p>
                <p class="kb-pathogen">病原：{{ currentKnowledge.pathogen }}</p>
                <span class="kb-severity" v-if="currentKnowledge.severity">危害程度：{{ currentKnowledge.severity }}</span>
              </div>
            </div>
            <div class="kb-section" v-if="currentKnowledge.symptoms?.length">
              <h5>典型症状</h5>
              <ul><li v-for="(s, i) in currentKnowledge.symptoms" :key="'sy' + i">{{ s }}</li></ul>
            </div>
            <div class="kb-section" v-if="currentKnowledge.occurrence?.length">
              <h5>发生规律</h5>
              <ul><li v-for="(s, i) in currentKnowledge.occurrence" :key="'oc' + i">{{ s }}</li></ul>
            </div>
            <div class="kb-section" v-if="currentKnowledge.control?.chemical?.length">
              <h5>飞防处方</h5>
              <ul class="kb-rx"><li v-for="(s, i) in currentKnowledge.control.chemical" :key="'rx' + i">{{ s }}</li></ul>
            </div>
            <div class="kb-section" v-if="currentKnowledge.control?.agricultural?.length">
              <h5>农艺防治</h5>
              <ul><li v-for="(s, i) in currentKnowledge.control.agricultural" :key="'ag' + i">{{ s }}</li></ul>
            </div>
            <div class="kb-section" v-if="currentKnowledge.control?.field?.length">
              <h5>田间管理</h5>
              <ul><li v-for="(s, i) in currentKnowledge.control.field" :key="'fi' + i">{{ s }}</li></ul>
            </div>
          </div>
          <div class="kb-empty" v-else>
            <template v-if="knowledgeLoading">知识库加载中…</template>
            <template v-else-if="knowledgeError">
              <p class="kb-error-text">{{ knowledgeError }}</p>
              <button class="kb-retry-btn" @click="loadKnowledge()">重试</button>
            </template>
            <template v-else>暂无知识库数据</template>
          </div>
        </div>
      </div>
    </div>
    </Transition>

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
            <div class="profile-stat-cell"><strong>{{ historyStats ? historyStats.today : '—' }}</strong><span>今日诊断（次）</span></div>
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

    <!-- Drone Recommendation Modal（无人机推荐 · DJI 商城）
         完整复刻大疆商城风格的商品详情页：版本切换 / 价格同步 / 官方购买跳转 / 购物车 / 收藏
         弹窗特效：与病害图鉴同款 hero-video-dialog spring 编排（v-if 必须放在 Transition 内部才能触发进入/离开动画） -->
    <Transition :css="false" @enter="onKbDialogEnter" @leave="onKbDialogLeave">
      <DjiAir3Shop v-if="activeModal === 'djiShop'" @close="activeModal = null" />
    </Transition>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { Aim, Setting } from '@element-plus/icons-vue'
import axios from 'axios'
import { animate } from 'motion'
import gsap from 'gsap'
import { marked } from 'marked'
import * as echarts from 'echarts'

// ── Magic UI effects (shadcn registry · @magicui) ─────────────────────
import MagicCard from '@/components/effects/magicui/MagicCard.vue'
import NumberTicker from '@/components/effects/magicui/NumberTicker.vue'
import ShineBorder from '@/components/effects/magicui/ShineBorder.vue'
import BorderBeam from '@/components/effects/magicui/BorderBeam.vue'
import PulsatingButton from '@/components/effects/magicui/PulsatingButton.vue'
import DjiAir3Shop from './DjiAir3Shop.vue'

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
// 非目标图像（未检测到玉米叶片）的提示文案；正常识别时为空
const rejectNotice = ref('')

// 植株健康度（Magic UI NumberTicker 消费的数值源）
const plantHealthValue = computed(() =>
  currentSample.value && isDetected.value
    ? Math.max(10, Math.round(100 - currentSample.value.damageRate))
    : 94,
)

// 雾滴粒径：后端会带「120 μm (超细雾化)」这类备注，参数行只放数值以免换行撑高
const droneDroplet = computed(() => {
  const dp = currentSample.value?.droneParams || {}
  const raw = dp.dropletSize || dp.droplet_size || '135 μm'
  return String(raw).replace(/\s*[（(][^)）]*[)）]\s*$/, '')
})

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
    rejectNotice.value = ''
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

// ── 病害图鉴（知识库弹窗）：数据与 /predict 决策卡同源（后端 knowledge_base.py） ──
const knowledgeItems = ref([])
const knowledgeActiveId = ref('')
const knowledgeLoaded = ref(false)
const knowledgeLoading = ref(false)
const knowledgeError = ref('')
const currentKnowledge = computed(
  () => knowledgeItems.value.find(k => k.class_name_en === knowledgeActiveId.value) || null
)
const kbSampleImg = computed(() => {
  if (!currentKnowledge.value) return ''
  const s = presetSamples.value.find(p => p.class_name_en === currentKnowledge.value.class_name_en)
  return s?.imgData || ''
})

async function loadKnowledge() {
  knowledgeLoading.value = true
  knowledgeError.value = ''
  try {
    const res = await axios.get('/api/screen/knowledge')
    knowledgeItems.value = res.data?.data || []
    knowledgeLoaded.value = true
    if (!knowledgeActiveId.value && knowledgeItems.value.length) {
      knowledgeActiveId.value = knowledgeItems.value[0].class_name_en
    }
  } catch (e) {
    console.error('加载病害知识库失败:', e)
    knowledgeError.value = e?.response?.status === 404
      ? '知识库接口不存在（404）：后端可能未重启到包含 /screen/knowledge 的最新代码'
      : '知识库加载失败：无法连接后端服务，请确认 run_backend.bat 已启动'
  } finally {
    knowledgeLoading.value = false
  }
}

async function openKnowledge() {
  activeModal.value = 'knowledge'
  if (!knowledgeLoaded.value && !knowledgeLoading.value) {
    await loadKnowledge()
  }
}

// ── 知识库弹窗 spring 入退场 ───────────────────────────────────────────
// 编排移植自 shadcn / Magic UI registry「hero-video-dialog」from-center 变体：
// 背景毛玻璃淡入 + 卡片 spring 缩放（damping: 30 / stiffness: 300），关闭时反向收拢。
// React 版的 AnimatePresence + motion.div 对应 Vue 的 <Transition :css="false"> + motion 的
// animate()（与 NumberTicker.vue 同一依赖通道）。
async function onKbDialogEnter(el, done) {
  // 同时兼容病害图鉴卡片与无人机推荐弹窗卡片
  const card = el.querySelector('.tanee-modal-card, .dji-shop-card')
  if (!card || typeof animate !== 'function') { done(); return }
  // 起始态在本帧绘制前内联写死，避免弹窗闪现原始尺寸
  el.style.opacity = '0'
  card.style.opacity = '0'
  card.style.transform = 'scale(0.5)'
  try {
    await Promise.all([
      animate(el, { opacity: [0, 1] }, { duration: 0.25, ease: 'easeOut' }),
      animate(card, { opacity: [0, 1], scale: [0.5, 1] }, { type: 'spring', damping: 30, stiffness: 300 }),
    ])
  } finally {
    el.style.opacity = ''
    card.style.opacity = ''
    card.style.transform = ''
    done()
  }
}

async function onKbDialogLeave(el, done) {
  const card = el.querySelector('.tanee-modal-card, .dji-shop-card')
  if (!card || typeof animate !== 'function') { done(); return }
  try {
    await Promise.all([
      animate(el, { opacity: [1, 0] }, { duration: 0.2, ease: 'easeIn' }),
      animate(card, { opacity: [1, 0], scale: [1, 0.5] }, { duration: 0.2, ease: 'easeIn' }),
    ])
  } finally {
    done()
  }
}

// hero-video-dialog 交互惯例：Esc 关闭弹窗
function onKbKeydown(e) {
  if (e.key === 'Escape' && activeModal.value === 'knowledge') {
    activeModal.value = null
  }
}
onMounted(() => window.addEventListener('keydown', onKbKeydown))
onUnmounted(() => window.removeEventListener('keydown', onKbKeydown))

function selectPreset(s, autoDetect = true) {
  currentSampleId.value = s.id
  currentSample.value = { ...s }
  previewUrl.value = s.imgData
  isDetected.value = false
  rejectNotice.value = ''
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
  rejectNotice.value = ''
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

      // 非目标图像：直接拒识，不出严重度/处方，也不计入统计
      if (data.is_target === false) {
        rejectNotice.value = data.reject_reason || '未检测到玉米叶片，请对准叶片重新拍摄'
        isDetected.value = false
        currentSample.value = {
          ...currentSample.value,
          diseaseName: '非目标图像',
          class_name_en: '',
          class_name_cn: '非目标图像',
          severity: '—',
          damageRate: 0,
          confidence: data.confidence,
          prescription: '',
          droneParams: {},
          boxes: [],
          gradcam_base64: ''
        }
        inferenceSpeed.value = data.inference_ms + 'ms'
        return
      }

      rejectNotice.value = ''
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
        // 飞防参数也要跟着本次结果的严重度走，否则模板默认值（1.6 L/亩…）会和动态处方打架
        droneParams: data.droneParams,
        boxes: data.boxes || [],
        gradcam_base64: data.gradcam_base64
      }
      isDetected.value = true
      inferenceSpeed.value = data.inference_ms + 'ms'
      refreshHistoryStats()
      refreshAlertStats()
    }
  } catch (err) {
    console.error('推理检测失败:', err)
  } finally {
    isDetecting.value = false
  }
}

// ── Alerts（诊断自动生成 · /screen/alerts）────────────────────────────
const alerts = ref([])
const alertStats = ref({ unread: 0, total: 0, today: 0 })
const alertsLoading = ref(false)
const alertsError = ref('')
const alertsUnreadOnly = ref(false)

const alertLevelClass = (level) => (level === 'urgent' ? 'urgent' : level === 'warning' ? 'warning' : 'info')
const alertIcon = (level) => (level === 'urgent' ? '🚨' : level === 'warning' ? '⚠️' : 'ℹ️')

async function loadAlerts() {
  alertsLoading.value = true
  alertsError.value = ''
  try {
    const res = await axios.get('/api/screen/alerts', {
      params: { limit: 50, unread_only: alertsUnreadOnly.value },
    })
    const d = res.data?.data
    if (d) {
      alerts.value = d.items || []
      alertStats.value = d.stats || { unread: 0, total: 0, today: 0 }
    }
  } catch (err) {
    console.error('告警加载失败:', err)
    alertsError.value = '告警加载失败，请检查后端服务'
  } finally {
    alertsLoading.value = false
  }
}

// 只刷未读数（诊断结束后调用，避免每次拉全量列表）
// 后端刚重启时首个请求可能失败，重试一次；失败不打扰界面
async function refreshAlertStats(retry = 1) {
  try {
    const res = await axios.get('/api/screen/alerts', { params: { limit: 1 } })
    if (res.data?.data?.stats) alertStats.value = res.data.data.stats
  } catch {
    if (retry > 0) setTimeout(() => refreshAlertStats(retry - 1), 1500)
  }
}

function openAlerts() {
  activeModal.value = 'alerts'
  loadAlerts()
}

async function markAlertRead(a) {
  try {
    await axios.post(`/api/screen/alerts/${a.id}/read`)
    await loadAlerts()
  } catch (err) {
    console.error('标记告警失败:', err)
  }
}

async function markAllAlertsRead() {
  try {
    await axios.post('/api/screen/alerts/read-all')
    await loadAlerts()
  } catch (err) {
    console.error('全部已读失败:', err)
  }
}

async function removeAlert(a) {
  try {
    await axios.delete(`/api/screen/alerts/${a.id}`)
    await loadAlerts()
  } catch (err) {
    console.error('删除告警失败:', err)
  }
}

// ── Diagnosis History（诊断历史 · /screen/history）───────────────────
const historyItems = ref([])
const historyStats = ref(null)
const historyLoading = ref(false)
const historyError = ref('')
const historyDetail = ref(null)

function fmtTime(iso) {
  if (!iso) return ''
  const m = String(iso).match(/(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2})/)
  return m ? `${m[2]}-${m[3]} ${m[4]}:${m[5]}` : iso
}

async function loadHistory() {
  historyLoading.value = true
  historyError.value = ''
  try {
    const res = await axios.get('/api/screen/history', { params: { limit: 50 } })
    if (res.data?.data) {
      historyItems.value = res.data.data.items || []
      historyStats.value = res.data.data.stats || null
    }
  } catch (err) {
    console.error('历史记录加载失败:', err)
    historyError.value = '历史记录加载失败，请检查后端服务'
  } finally {
    historyLoading.value = false
  }
}

// 只刷统计（诊断成功后调用，不拉全量列表，避免无谓传输）
async function refreshHistoryStats() {
  try {
    const res = await axios.get('/api/screen/history', { params: { limit: 1 } })
    if (res.data?.data?.stats) historyStats.value = res.data.data.stats
  } catch { /* 静默失败，不打扰诊断主流程 */ }
}

function openHistory() {
  activeModal.value = 'history'
  historyDetail.value = null
  loadHistory()
}

async function openHistoryDetail(id) {
  try {
    const res = await axios.get(`/api/screen/history/${id}`)
    if (res.data?.data) historyDetail.value = res.data.data
  } catch (err) {
    console.error('历史详情加载失败:', err)
  }
}

async function removeHistory(id) {
  try {
    await axios.delete(`/api/screen/history/${id}`)
    if (historyDetail.value?.id === id) historyDetail.value = null
    await loadHistory()
  } catch (err) {
    console.error('删除历史记录失败:', err)
  }
}

// ── Batch Recognition（批量巡田识别 · /screen/predict/batch）────────────
const BATCH_MAX = 24
const batchInput = ref(null)
const batchFiles = ref([])
const batchItems = ref([])
const batchErrors = ref([])
const batchRejected = ref([])
const batchSummary = ref(null)
const batchRunning = ref(false)
const batchElapsed = ref(0)
const batchError = ref('')
let batchTimer = null
let alertPollTimer = null

// 严重度带描述（"危急 (IV 级暴发期)"），徽标只显示档位词
function sevKey(severity) {
  const s = String(severity || '')
  for (const kw of ['危急', '重度', '中度', '轻度']) if (s.includes(kw)) return kw
  return s.includes('健康') ? '健康' : s
}

// 浏览器端压缩：最长边 1024px / JPEG 0.86，避免 24 张原图把请求体撑到几十 MB
function fileToDataUrl(file, maxSide = 1024, quality = 0.86) {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onerror = () => reject(new Error('读取失败'))
    reader.onload = () => {
      const img = new Image()
      img.onerror = () => reject(new Error('图片解码失败'))
      img.onload = () => {
        let { width, height } = img
        const scale = Math.min(1, maxSide / Math.max(width, height))
        width = Math.round(width * scale)
        height = Math.round(height * scale)
        const canvas = document.createElement('canvas')
        canvas.width = width
        canvas.height = height
        canvas.getContext('2d').drawImage(img, 0, 0, width, height)
        resolve(canvas.toDataURL('image/jpeg', quality))
      }
      img.src = reader.result
    }
    reader.readAsDataURL(file)
  })
}

function openBatch() {
  activeModal.value = 'batch'
}

async function onBatchFiles(e) {
  const picked = [...(e.target.files || [])]
  batchError.value = ''
  const room = BATCH_MAX - batchFiles.value.length
  if (room <= 0) {
    batchError.value = `单次最多 ${BATCH_MAX} 张，请先清空或分批提交`
    e.target.value = ''
    return
  }
  if (picked.length > room) batchError.value = `最多 ${BATCH_MAX} 张，已忽略多余的 ${picked.length - room} 张`

  for (const f of picked.slice(0, room)) {
    if (!f.type.startsWith('image/')) continue
    try {
      batchFiles.value.push({ name: f.name, dataUrl: await fileToDataUrl(f) })
    } catch {
      batchError.value = `图片处理失败：${f.name}`
    }
  }
  e.target.value = ''
  batchItems.value = []
  batchSummary.value = null
  batchErrors.value = []
}

function removeBatchFile(i) {
  batchFiles.value.splice(i, 1)
}

function resetBatch() {
  batchFiles.value = []
  batchItems.value = []
  batchErrors.value = []
  batchRejected.value = []
  batchSummary.value = null
  batchError.value = ''
}

async function runBatch() {
  if (!batchFiles.value.length || batchRunning.value) return
  batchRunning.value = true
  batchElapsed.value = 0
  batchError.value = ''
  batchItems.value = []
  batchErrors.value = []
  batchRejected.value = []
  batchSummary.value = null
  batchTimer = setInterval(() => { batchElapsed.value += 1 }, 1000)

  try {
    const res = await axios.post(
      '/api/screen/predict/batch',
      {
        images: batchFiles.value.map((f) => ({ image_base64: f.dataUrl, filename: f.name })),
        model: 'resnet50_cbam',
        acreage_per_image: 1.0,
      },
      { timeout: 600000 }
    )
    const d = res.data?.data
    if (d) {
      batchItems.value = (d.items || []).map((it) => ({
        ...it,
        _thumb: batchFiles.value[it.index]?.dataUrl || '',
      }))
      batchErrors.value = d.errors || []
      batchRejected.value = d.rejected || []
      batchSummary.value = d.summary || null
      refreshHistoryStats()
    }
  } catch (err) {
    console.error('批量识别失败:', err)
    batchError.value =
      '批量识别失败：' + (err?.response?.data?.detail || err?.message || '请检查后端服务')
  } finally {
    batchRunning.value = false
    if (batchTimer) {
      clearInterval(batchTimer)
      batchTimer = null
    }
  }
}

// ── Agnes-3.0 AI Chat ─────────────────────────────────────────────────
const WELCOME_MSG = {
  role: 'ai',
  text: '您好！我是 <strong>AI 植保问答助手</strong>，已连接示范田 24h 微气候传感器与田间监测数据。请问有什么可以协助您？',
  searchQuery: ''
}
const messages = ref([WELCOME_MSG])
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

// 会话标识：一次页面会话默认一个新 id，用于后端恢复上下文（内存快照 / 磁盘会话找回）。
// 声明为 let——「会话找回」时需切换为历史会话 id；activeSessionId 是它的响应式镜像，
// 供历史列表高亮当前会话用（普通 let 重新赋值不会触发视图更新）
let chatSessionId = `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
const activeSessionId = ref(chatSessionId)

function newSessionId() {
  return `s_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`
}

// ── 会话找回（复用 claude --resume 机制：列出落盘会话 + 一键接着聊）────────
const showHistory = ref(false)
const sessionList = ref([])
const loadingSessions = ref(false)
const loadError = ref(false)  // 列表加载失败（404=后端旧版无该路由 / 其他=网络异常），与空态区分
const pendingDeleteId = ref(null)

function toggleSessionHistory() {
  showHistory.value = !showHistory.value
  if (showHistory.value) fetchSessionList()
}

async function fetchSessionList() {
  loadingSessions.value = true
  loadError.value = false
  try {
    const res = await axios.get('/api/screen/sessions')
    sessionList.value = res.data?.data?.sessions || []
  } catch (err) {
    console.error('获取历史会话失败:', err)
    loadError.value = err?.response?.status || true
    sessionList.value = []
  } finally {
    loadingSessions.value = false
  }
}

// 选定一段历史会话：拉取气泡数据回填 + 切换 chatSessionId。
// 之后正常提问即可——后端自动以磁盘 transcript 为基底接着聊（含此前检索结果）
async function restoreSession(s) {
  if (!s || loadingSessions.value) return
  try {
    const res = await axios.get(`/api/screen/sessions/${encodeURIComponent(s.session_id)}`)
    const d = res.data?.data
    if (!d) return
    chatSessionId = s.session_id
    activeSessionId.value = s.session_id
    const restored = (d.messages || [])
      .filter(m => m.text)
      .map(m => ({ role: m.role, text: m.text, searchQuery: m.searchQuery || '' }))
    if (d.interrupted) {
      // 末轮被打断（检索完成未答完等）：加一条提示气泡（hint 标记，不进上下文）
      restored.push({
        role: 'ai',
        hint: true,
        text: '⏸ 已找回上次会话，回答在此处中断。直接说「继续」即可接着完成。'
      })
    }
    messages.value = restored.length ? restored : [WELCOME_MSG]
    showHistory.value = false
    await nextTick()
    if (chatBodyRef.value) chatBodyRef.value.scrollTop = chatBodyRef.value.scrollHeight
  } catch (err) {
    console.error('找回会话失败:', err)
  }
}

// 两步删除（首点击进入待确认态，3 秒内再点才真删），避免误删会话数据
function removeSession(s) {
  if (pendingDeleteId.value !== s.session_id) {
    pendingDeleteId.value = s.session_id
    setTimeout(() => {
      if (pendingDeleteId.value === s.session_id) pendingDeleteId.value = null
    }, 3000)
    return
  }
  pendingDeleteId.value = null
  axios.delete(`/api/screen/sessions/${encodeURIComponent(s.session_id)}`)
    .then(() => {
      if (chatSessionId === s.session_id) startNewSession()
      fetchSessionList()
    })
    .catch(err => console.error('删除会话失败:', err))
}

// 新会话（等价 /clear）：换新会话 id，气泡回到欢迎语
function startNewSession() {
  chatSessionId = newSessionId()
  activeSessionId.value = chatSessionId
  messages.value = [WELCOME_MSG]
  inputText.value = ''
  toolStatus.value = ''
  pendingDeleteId.value = null
  showHistory.value = false
}

// 当前请求的中断控制器。必须放模块级——stopChat() 需要访问它
// （此前声明在 sendMessage 内部，导致点「停止」时抛 ReferenceError）
let chatAbort = null

// ── Typewriter 匀速缓冲（ChatGPT 手感的核心）────────────────────────────
// LLM 吐 token 忽快忽慢（网络抖动 / 网关合批），直接来一个上屏一个会"哗蹦一段又停半秒"。
// 这里把接收与显示拆开：delta 先进缓冲区，rAF 以固定帧率匀速取字上屏，
// 用户看到的始终是稳定节奏的打字效果。生产者-消费者模式。
function createTyper(onUpdate) {
  let pending = ''   // 已收到、待上屏
  let displayed = '' // 已上屏
  let rafId = null

  function tick() {
    if (pending.length) {
      // 自适应取字量：底速 2 字/帧，积压越多吐得越快（封顶 10），保证既匀速又追得上高速流
      const take = Math.min(Math.max(2, Math.ceil(pending.length / 40)), 10, pending.length)
      displayed += pending.slice(0, take)
      pending = pending.slice(take)
      onUpdate(displayed)
    }
    rafId = pending.length ? requestAnimationFrame(tick) : null
  }

  return {
    push(chunk) {
      pending += chunk
      if (rafId === null) rafId = requestAnimationFrame(tick)
    },
    // 流结束/中断时调用：把余量一次性上屏，避免「网络已结束、UI 还在逐字蹦」
    flush() {
      if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null }
      if (pending.length) {
        displayed += pending
        pending = ''
        onUpdate(displayed)
      }
    },
    dispose() {
      if (rafId !== null) { cancelAnimationFrame(rafId); rafId = null }
      pending = ''
    }
  }
}

async function sendMessage() {
  const query = inputText.value.trim()
  if (!query || aiTyping.value) return

  // 多轮上下文：携带之前的对话（跳过固定欢迎语、提示气泡与本轮问题），后端按标准 messages 结构包装
  const history = messages.value
    .slice(1)
    .filter(m => m.text && !m.hint)
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
  let aiMsg = null // 本轮 AI 气泡的引用（首个 delta 时创建）
  chatAbort = null

  // 打字机缓冲：delta 不直接上屏，经 rAF 匀速释放（onUpdate 只在真正吐字时触发）
  const typer = createTyper((text) => {
    if (aiMsg) aiMsg.text = text
    const body = chatBodyRef.value
    if (body && body.scrollHeight - body.scrollTop - body.clientHeight < 80) {
      body.scrollTop = body.scrollHeight
    }
  })

  try {
    // AbortController：用户点「停止」时可中断生成，后端检测到断连即终止上游请求
    chatAbort = new AbortController()
    const response = await fetch('/api/screen/chat/stream', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      signal: chatAbort.signal,
      body: JSON.stringify({
        message: query,
        history,
        // 会话标识：后端据此缓存被打断那一轮的完整上下文（含检索结果）
        session_id: chatSessionId,
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
          } else if (evt.type === 'truncated') {
            // 回答被 max_tokens 截断：resume=后端正在续写，incomplete=续写额度用尽
            toolStatus.value = evt.action === 'resume'
              ? '回答较长，正在继续生成...'
              : ''
          } else if (evt.type === 'resume') {
            // 后端恢复会话上下文：source=disk 为从磁盘找回历史会话，
            // 否则是命中缓存接着被打断的任务（含此前已检索到的结果）
            toolStatus.value = evt.source === 'disk'
              ? '已找回历史会话，正在接着上次继续...'
              : '已恢复上次中断的任务，正在继续处理...'
          } else if (evt.type === 'retry') {
            // 上游请求抖动，后端正在指数退避重试（避免整段回答降级成离线模板）
            toolStatus.value = `网络波动，正在重试（${evt.attempt}/${evt.max}）...`
          } else if (evt.type === 'stop_hook') {
            // Stop Hook（回合结束钩子）：block=回答被打回重答，allow=校验通过即将结束
            toolStatus.value = evt.action === 'block'
              ? '回答未通过停止校验，正在重新组织更完整的回答...'
              : ''
          } else if (evt.type === 'delta') {
            if (!hasAiMsg) {
              hasAiMsg = true
              aiMsg = reactive({
                role: 'ai',
                text: '',
                searchQuery: toolStatus.value ? toolStatus.value.replace(/.*「(.*)」.*/, '$1') : ''
              })
              messages.value.push(aiMsg)
            }
            toolStatus.value = ''
            // 进缓冲区由 rAF 匀速上屏，不再逐 chunk 直写
            typer.push(evt.content)
          }
        } catch (e) {
          console.warn('解析流式消息异常:', e)
        }
      }
    }

    // 流正常结束：把缓冲区余量一次性上屏
    typer.flush()
  } catch (err) {
    if (err?.name === 'AbortError') {
      // 用户主动停止：先冲掉缓冲区已生成的内容，再追加标记，避免误以为是异常
      typer.flush()
      if (hasAiMsg && aiMsg) {
        aiMsg.text += '\n\n⏹ 已停止生成'
      } else {
        messages.value.push({ role: 'ai', text: '⏹ 已停止生成。' })
      }
    } else {
      console.error('流式问答失败:', err)
      if (!hasAiMsg) {
        messages.value.push({
          role: 'ai',
          text: '⚠️ 问答服务响应超时，建议参考嘧菌酯对路药剂并严控田间湿度。'
        })
      }
    }
  } finally {
    // 兜底：任何路径退出都停掉 rAF 循环，防止计时器泄漏
    typer.dispose()
    aiTyping.value = false
    chatAbort = null
  }
}

// 手动停止当前生成（发送按钮在 aiTyping 时变为「停止」）
function stopChat() {
  if (chatAbort) {
    chatAbort.abort()
    toolStatus.value = ''
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
  refreshHistoryStats() // 个人中心「今日诊断」用真实计数
  refreshAlertStats() // 顶部告警胶囊的未读数
  alertPollTimer = setInterval(refreshAlertStats, 60000)
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
  clearInterval(alertPollTimer)
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

/* ════════════════════ 1. SIDEBAR (103px · 深墨绿) ════════════════════ */
.tanee-sidebar {
  width: 103px;
  height: 834px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: space-between;
  box-sizing: border-box;
  flex-shrink: 0;
  background: linear-gradient(180deg, #16302a 0%, #10231d 55%, #0d1d18 100%);
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
  gap: 6px;
  width: 100%;

  &.upper {
    margin-top: 14px;
  }

  &.lower {
    margin-top: auto;
    margin-bottom: 16px;
    gap: 10px;
  }
}

/* 主导航项：图标 + 文字，选中态为亮绿渐变圆角块 */
.nav-item-btn {
  width: 68px;
  height: 58px;
  border-radius: 12px;
  border: none;
  background: transparent;
  color: #93a79c;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 5px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-family: inherit;

  .nav-svg-icon {
    width: 20px;
    height: 20px;
  }

  .nav-label {
    font-size: 11px;
    line-height: 1;
    letter-spacing: 0.02em;
    white-space: nowrap;
  }

  /* 白色原始填充的 SVG（icon-16 房子 fill="white"）：非选中时转为浅灰绿，
     选中态反白 */
  .white-filter {
    filter: brightness(0) invert(0.72);
    transition: filter 0.15s ease;
  }

  &.active {
    background: linear-gradient(155deg, #2fae6f 0%, #1d8a52 100%);
    color: #ffffff;
    box-shadow: 0 6px 14px rgba(53, 197, 110, 0.38);

    .white-filter {
      filter: brightness(0) invert(1);
    }
  }

  &:hover:not(.active) {
    background: rgba(255, 255, 255, 0.06);
    color: #d8e6de;

    .white-filter {
      filter: brightness(0) invert(0.9);
    }
  }
}

/* 底部功能区：主题切换小方块 */
.nav-tile-btn {
  width: 44px;
  height: 44px;
  border-radius: 12px;
  border: none;
  background: rgba(255, 255, 255, 0.07);
  color: #aebfb5;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.15s ease;

  .nav-svg-icon {
    width: 20px;
    height: 20px;
  }

  &.active,
  &:hover {
    background: rgba(255, 255, 255, 0.14);
    color: #ffffff;
  }
}

/* 底部品牌块：植物 + slogan（点击进入个人中心） */
.brand-tile {
  width: 84px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.04);
  padding: 14px 6px 12px;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 9px;
  cursor: pointer;
  transition: background 0.15s ease;

  .plant-icon {
    width: 26px;
    height: 26px;
  }

  .brand-tile-text {
    font-size: 10px;
    line-height: 1.7;
    color: #7d938a;
    text-align: center;
    white-space: nowrap;
  }

  &:hover {
    background: rgba(255, 255, 255, 0.08);

    .brand-tile-text {
      color: #a7bcb1;
    }
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
  background: #f4f4f4;
  border-radius: 6px;
  position: relative;
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: inset 0 0 0 1px #dcdcdc;

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
      font-size: 12.5px;
      color: #475467;
      line-height: 1.2;
    }
  }

  .dd-severity-badge {
    color: #ffffff;
    font-size: 13px;
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
    /* 34%：处方区的机型字段会返回两个型号（“大疆 T60 / 极飞 P100 Pro”），
       36% 时五列参数的间隙会被压到 10px，看起来粘连；34% 回到 13.8px 且左右均无溢出 */
    width: 34%;
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
        font-size: 13px;
        color: #475467;
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
        font-size: 13px;
        font-weight: 600;
        color: #101828;
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
      flex: 0 0 auto; /* 不让 flex 压缩，否则第 4 行会被裁掉 */
      margin: 2px 0;
      font-size: 12.5px;
      color: #344054;
      line-height: 1.4;
      display: -webkit-box;
      /* 处方改为按严重度动态生成，最长（危急 + 低置信度）约 145 字，4 行放得下且卡片无溢出 */
      -webkit-line-clamp: 4;
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
      padding: 4px 3px;
      border: 1px solid #f2f4f7;

      .d-param-item {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1px;

        .dp-k {
          font-size: 12px;
          color: #667085;
          font-weight: 500;
          white-space: nowrap;
        }

        .dp-v {
          font-size: 11.5px;
          font-weight: 700;
          color: #101828;
          white-space: nowrap; /* 长机型名不换行，否则整行高度翻倍挤压处方 */
        }
      }
    }

    .flight-weather-notice {
      display: flex;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      color: #05603a;
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
  position: relative;
  overflow: hidden;
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

    &.kb-layout {
      display: grid;
      grid-template-columns: 168px 1fr;
      gap: 0;
      padding: 0;
      height: 480px;

      .kb-side {
        border-right: 1px solid #ebebeb;
        background: #f8f8f8;
        padding: 12px;
        display: flex;
        flex-direction: column;
        gap: 6px;

        .kb-side-item {
          display: flex;
          align-items: center;
          gap: 8px;
          border: none;
          background: none;
          padding: 10px 12px;
          border-radius: 8px;
          font-size: 13px;
          color: #525866;
          cursor: pointer;
          text-align: left;
          transition: background 0.15s ease, color 0.15s ease;

          &:hover { background: #ececec; }

          &.active {
            background: #ffffff;
            color: #333333;
            font-weight: 600;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
          }

          .kb-dot {
            width: 8px;
            height: 8px;
            border-radius: 99999px;
            flex-shrink: 0;
          }
        }
      }

      .kb-detail {
        padding: 16px 20px 20px;
        overflow-y: auto;
        display: flex;
        flex-direction: column;
        gap: 14px;

        .kb-hero {
          display: flex;
          gap: 14px;
          padding: 12px;
          border: 1px solid #ebebeb;
          border-left: 4px solid #17b26a;
          border-radius: 8px;
          background: #ffffff;

          .kb-hero-img {
            width: 132px;
            height: 100px;
            object-fit: cover;
            border-radius: 8px;
            flex-shrink: 0;
            background: #f4f4f4;
          }

          .kb-hero-info {
            min-width: 0;

            h3 { margin: 0 0 4px; font-size: 16px; color: #333333; }
            .kb-en { margin: 0 0 6px; font-size: 11px; color: #a4a4a4; letter-spacing: 0.3px; }
            .kb-pathogen { margin: 0 0 8px; font-size: 12px; color: #525866; line-height: 1.6; }
            .kb-severity {
              display: inline-block;
              font-size: 11px;
              color: #8a6116;
              background: rgba(249, 173, 25, 0.12);
              border: 1px solid rgba(249, 173, 25, 0.45);
              padding: 2px 8px;
              border-radius: 99999px;
            }
          }
        }

        .kb-section {
          h5 {
            margin: 0 0 6px;
            font-size: 13px;
            color: #333333;
            display: flex;
            align-items: center;
            gap: 6px;

            &::before {
              content: '';
              width: 4px;
              height: 12px;
              border-radius: 2px;
              background: linear-gradient(180deg, #35c56e, #2e9055);
            }
          }

          ul { margin: 0; padding: 0; list-style: none; }

          li {
            position: relative;
            padding-left: 14px;
            font-size: 12px;
            color: #525866;
            line-height: 1.7;
            margin-bottom: 4px;

            &::before {
              content: '';
              position: absolute;
              left: 2px;
              top: 8px;
              width: 5px;
              height: 5px;
              border-radius: 50%;
              background: #dcdcdc;
            }
          }

          &.kb-rx li::before { background: #f9ad19; }
        }
      }

      .kb-empty {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        gap: 10px;
        font-size: 13px;
        color: #a4a4a4;
        text-align: center;
        padding: 0 24px;

        .kb-error-text { margin: 0; line-height: 1.6; }

        .kb-retry-btn {
          border: none;
          cursor: pointer;
          color: #ffffff;
          font-size: 13px;
          padding: 7px 22px;
          border-radius: 8px;
          background: linear-gradient(135deg, #35c56e, #2e9055);

          &:hover { filter: brightness(1.05); }
        }
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

    .di-collapse-btn,
    .di-head-btn {
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

  /* 历史会话找回视图（灵动岛内切换：对话 ⇄ 会话列表，对齐 claude --resume 选择器） */
  .di-history {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;

    .di-history-head {
      display: flex;
      align-items: baseline;
      gap: 8px;
      padding: 10px 14px 8px;
      flex-shrink: 0;

      .di-history-title {
        font-size: 12px;
        font-weight: 600;
        color: #f2f4f6;
      }
      .di-history-sub {
        font-size: 10.5px;
        color: #8d93a1;
      }
    }

    .di-history-list {
      flex: 1;
      min-height: 0;
      overflow-y: auto;
      padding: 0 14px 10px;
      display: flex;
      flex-direction: column;
      gap: 8px;

      &::-webkit-scrollbar { width: 5px; }
      &::-webkit-scrollbar-thumb { background: rgba(255, 255, 255, 0.16); border-radius: 3px; }
    }

    .di-history-empty {
      font-size: 11.5px;
      color: #8d93a1;
      text-align: center;
      padding: 28px 0;
    }

    /* 失败态：与「暂无数据」区分开，明确提示原因并可重试 */
    .di-history-failed {
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 10px;

      p {
        margin: 0;
        color: #eb4335;
        line-height: 1.5;
      }

      .di-history-retry {
        border: 1px solid rgba(235, 67, 53, 0.5);
        background: rgba(235, 67, 53, 0.12);
        color: #eb4335;
        font-size: 11px;
        padding: 4px 14px;
        border-radius: 9999px;
        cursor: pointer;

        &:hover {
          background: rgba(235, 67, 53, 0.22);
        }
      }
    }

    .di-history-item {
      display: flex;
      align-items: center;
      gap: 8px;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.08);
      border-radius: 8px;
      cursor: pointer;
      transition: background 0.15s, border-color 0.15s;

      &:hover {
        background: rgba(255, 255, 255, 0.09);
        border-color: rgba(53, 197, 110, 0.45);
      }
      &.active {
        border-color: rgba(53, 197, 110, 0.8);
        background: rgba(53, 197, 110, 0.08);
      }

      .di-history-main { flex: 1; min-width: 0; }

      .di-history-name {
        font-size: 12.5px;
        color: #e8eaed;
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }

      .di-history-meta {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-top: 3px;
        font-size: 10px;
        color: #8d93a1;

        .di-history-tag {
          color: #f9ad19;
          background: rgba(249, 173, 25, 0.14);
          padding: 1px 6px;
          border-radius: 4px;
          font-weight: 600;
        }
      }

      .di-history-del {
        flex-shrink: 0;
        width: 22px;
        height: 22px;
        border: none;
        border-radius: 6px;
        background: rgba(255, 255, 255, 0.06);
        color: #8d93a1;
        font-size: 10px;
        cursor: pointer;
        display: flex;
        align-items: center;
        justify-content: center;
        padding: 0;

        &:hover {
          background: rgba(235, 67, 53, 0.18);
          color: #eb4335;
        }
        &.armed {
          width: auto;
          padding: 0 8px;
          color: #eb4335;
          background: rgba(235, 67, 53, 0.14);
        }
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

/* 让 Magic UI 的流光/光带「亮」起来：
   1) 层级：MagicCard 内部 backdrop/z=1、content/z=3，ShineBorder 默认 auto 会被压在背景下面；
      摄像头卡里 BorderBeam 是最前面的兄弟节点，会被后面的画面层盖住 —— 必须抬高
   2) 辉光：2~3px 的渐变环在浅色卡面上太弱，补一层绿色 drop-shadow */
.shine-border {
  z-index: 4 !important;
  filter: drop-shadow(0 0 4px rgba(23, 178, 106, 0.6));
}

.border-beam {
  z-index: 3 !important;
  filter: drop-shadow(0 0 6px rgba(23, 178, 106, 0.85));
}

/* ── Diagnosis History（诊断历史）────────────────────────────────── */.canvas-floating-toolbar {
  .canvas-action-btn.ghost {
    background: rgba(255, 255, 255, 0.92);
    color: #1d2939;
    border: 1px solid rgba(255, 255, 255, 0.4);

    svg { width: 13px; height: 13px; }
    &:hover { background: #ffffff; }
  }
}

.canvas-right-group {
  display: flex;
  align-items: center;
  gap: 6px;
}

.history-modal-card {
  .history-stat-chip {
    margin-left: 10px;
    font-size: 12px;
    color: #05603a;
    background: #e7f6ef;
    border: 1px solid #bfe8d2;
    border-radius: 999px;
    padding: 2px 10px;
    font-weight: 600;
    white-space: nowrap;
  }

  .history-body {
    min-height: 220px;
    max-height: 62vh;
    overflow-y: auto;
    padding: 12px 16px 16px;
  }

  .history-empty {
    padding: 48px 0;
    text-align: center;
    color: #98a2b3;
    font-size: 13px;
  }

  .history-retry-btn {
    display: block;
    margin: 10px auto 0;
    padding: 4px 18px;
    font-size: 12.5px;
    border: 1px solid #d0d5dd;
    background: #ffffff;
    border-radius: 6px;
    cursor: pointer;
    color: #344054;
    &:hover { border-color: #17b26a; color: #0f9755; }
  }

  /* 列表 */
  .history-list { display: flex; flex-direction: column; gap: 8px; }

  .history-item {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    border: 1px solid #eceef1;
    border-radius: 8px;
    cursor: pointer;
    background: #ffffff;
    transition: border-color 0.15s ease, box-shadow 0.15s ease;

    &:hover {
      border-color: #9fe0bd;
      box-shadow: 0 2px 8px rgba(23, 178, 106, 0.12);
    }

    .history-thumb {
      width: 56px;
      height: 44px;
      object-fit: cover;
      border-radius: 5px;
      flex-shrink: 0;
      background: #f2f4f7;
    }

    .history-thumb-empty {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 18px;
    }

    .history-item-main { flex: 1; min-width: 0; }

    .hi-row1 {
      display: flex;
      align-items: center;
      gap: 8px;
      strong { font-size: 13px; color: #101828; }
    }

    .hi-row2 {
      margin-top: 2px;
      font-size: 11.5px;
      color: #667085;
    }

    .history-item-time {
      font-size: 11.5px;
      color: #98a2b3;
      white-space: nowrap;
    }

    .history-del-btn {
      width: 22px;
      height: 22px;
      line-height: 20px;
      text-align: center;
      border: none;
      border-radius: 50%;
      background: transparent;
      color: #c2c7cf;
      cursor: pointer;
      font-size: 12px;
      flex-shrink: 0;
      &:hover { background: #fee4e2; color: #b42318; }
    }
  }

  /* 严重度徽标 */
  .hi-sev {
    font-style: normal;
    font-size: 11px;
    font-weight: 700;
    border-radius: 999px;
    padding: 1px 8px;

    &[data-sev='健康'] { color: #067647; background: #e7f6ef; }
    &[data-sev='轻度'] { color: #b54708; background: #fef0c7; }
    &[data-sev='中度'] { color: #b93815; background: #ffead5; }
    &[data-sev='重度'] { color: #b42318; background: #fee4e2; }
  }

  /* 详情 */
  .history-detail-top {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .history-back-btn {
    border: 1px solid #d0d5dd;
    background: #ffffff;
    border-radius: 6px;
    padding: 3px 12px;
    font-size: 12.5px;
    color: #344054;
    cursor: pointer;
    &:hover { border-color: #17b26a; color: #0f9755; }
  }

  .history-detail-time { font-size: 12px; color: #98a2b3; }

  .history-detail-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 10px;
  }

  .history-img-box {
    position: relative;
    border-radius: 8px;
    overflow: hidden;
    background: #101418;
    min-height: 150px;

    img { width: 100%; display: block; }

    .history-img-empty {
      display: flex;
      align-items: center;
      justify-content: center;
      height: 150px;
      color: #667085;
      font-size: 12px;
    }

    .history-img-tag {
      position: absolute;
      left: 8px;
      bottom: 8px;
      font-size: 11px;
      font-weight: 700;
      color: #ffffff;
      background: rgba(16, 24, 40, 0.72);
      border-radius: 4px;
      padding: 2px 8px;

      &.cam { background: rgba(23, 178, 106, 0.85); }
    }
  }

  .history-detail-rows {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 6px;

    .hrow {
      display: flex;
      gap: 12px;
      font-size: 12.5px;
      padding: 6px 10px;
      background: #f9fafb;
      border-radius: 6px;

      span { width: 118px; flex-shrink: 0; color: #667085; }
      strong { color: #101828; font-weight: 600; line-height: 1.5; }

      &.rx strong { font-weight: 400; color: #344054; }

      .hi-en { font-style: normal; color: #98a2b3; font-weight: 400; font-size: 11.5px; }
      .hi-name strong, strong.hi-name { font-weight: 700; }
    }
  }
}
/* ── Batch Recognition（批量巡田识别）────────────────────────────── */
.batch-modal-card {
  .batch-body {
    max-height: 64vh;
    overflow-y: auto;
    padding: 14px 16px 16px;
  }

  .batch-file-input { display: none; }

  .batch-picker {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
    padding: 22px 16px;
    border: 1.5px dashed #cfd8d3;
    border-radius: 10px;
    background: #f8fbf9;
    cursor: pointer;
    transition: border-color 0.15s ease, background 0.15s ease;

    &:hover { border-color: #17b26a; background: #f1faf5; }

    svg { width: 26px; height: 26px; color: #17b26a; }
    strong { font-size: 13.5px; color: #101828; }
    span { font-size: 11.5px; color: #98a2b3; }
  }

  .batch-thumbs {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(86px, 1fr));
    gap: 8px;
    margin-top: 10px;
  }

  .batch-thumb {
    position: relative;
    border-radius: 6px;
    overflow: hidden;
    background: #f2f4f7;

    img { width: 100%; height: 64px; object-fit: cover; display: block; }

    .batch-thumb-name {
      display: block;
      padding: 2px 4px;
      font-size: 10px;
      color: #667085;
      white-space: nowrap;
      overflow: hidden;
      text-overflow: ellipsis;
    }

    .batch-thumb-del {
      position: absolute;
      top: 3px;
      right: 3px;
      width: 18px;
      height: 18px;
      line-height: 16px;
      border: none;
      border-radius: 50%;
      background: rgba(16, 24, 40, 0.6);
      color: #ffffff;
      font-size: 10px;
      cursor: pointer;
      &:hover { background: #b42318; }
    }
  }

  .batch-actions {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 12px;
  }

  .batch-run-btn {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 7px 18px;
    border: none;
    border-radius: 6px;
    background: linear-gradient(135deg, #17b26a 0%, #0f9755 100%);
    color: #ffffff;
    font-size: 13px;
    font-weight: 700;
    cursor: pointer;

    &:hover:not(:disabled) { filter: brightness(1.08); }
    &:disabled { opacity: 0.55; cursor: not-allowed; }

    .btn-spinner {
      width: 11px;
      height: 11px;
      border: 2px solid rgba(255, 255, 255, 0.4);
      border-top-color: #ffffff;
      border-radius: 9999px;
      animation: spin 0.8s linear infinite;
    }
  }

  .batch-clear-btn {
    padding: 6px 14px;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    background: #ffffff;
    color: #344054;
    font-size: 12.5px;
    cursor: pointer;
    &:hover { border-color: #98a2b3; }
  }

  .batch-hint { font-size: 11.5px; color: #98a2b3; }

  .batch-error {
    margin-top: 10px;
    padding: 7px 10px;
    border-radius: 6px;
    background: #fef3f2;
    color: #b42318;
    font-size: 12px;
  }

  .batch-summary {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 8px;
    margin-top: 12px;
  }

  .bs-cell {
    padding: 8px 6px;
    border-radius: 8px;
    background: #f9fafb;
    border: 1px solid #eef0f2;
    text-align: center;

    strong { display: block; font-size: 15px; color: #101828; line-height: 1.2; }
    span { font-size: 10.5px; color: #667085; }
  }

  .batch-dist {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 6px;
    margin-top: 10px;

    .batch-dist-label { font-size: 11.5px; color: #667085; }

    .batch-dist-chip {
      font-size: 11.5px;
      font-weight: 600;
      padding: 2px 9px;
      border-radius: 999px;
      border: 1px solid transparent;
    }
  }

  .batch-worst {
    margin-top: 8px;
    font-size: 12px;
    color: #475467;

    strong { color: #b42318; }
    .batch-worst-file { color: #98a2b3; margin-left: 4px; }
  }

  .batch-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    margin-top: 12px;
  }

  .batch-item {
    display: flex;
    gap: 10px;
    padding: 8px 10px;
    border: 1px solid #eceef1;
    border-radius: 8px;
    background: #ffffff;

    .batch-item-thumb {
      width: 62px;
      height: 62px;
      object-fit: cover;
      border-radius: 6px;
      flex-shrink: 0;
      background: #f2f4f7;
    }

    .batch-item-main { flex: 1; min-width: 0; }

    .bi-row1 {
      display: flex;
      align-items: center;
      gap: 8px;
      strong { font-size: 13px; color: #101828; }
      .bi-file { font-size: 11px; color: #98a2b3; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
    }

    .bi-row2 { margin-top: 2px; font-size: 11.5px; color: #667085; }

    .bi-rx {
      margin-top: 4px;
      font-size: 11.5px;
      line-height: 1.5;
      color: #475467;
      display: -webkit-box;
      -webkit-line-clamp: 2;
      -webkit-box-orient: vertical;
      overflow: hidden;
    }
  }

  /* 与历史弹窗同一套严重度徽标 */
  .hi-sev {
    font-style: normal;
    font-size: 11px;
    font-weight: 700;
    border-radius: 999px;
    padding: 1px 8px;
    flex-shrink: 0;

    &[data-sev='健康'] { color: #067647; background: #e7f6ef; }
    &[data-sev='轻度'] { color: #b54708; background: #fef0c7; }
    &[data-sev='中度'] { color: #b93815; background: #ffead5; }
    &[data-sev='重度'] { color: #b42318; background: #fee4e2; }
    &[data-sev='危急'] { color: #ffffff; background: #b42318; }
  }

  .batch-errors {
    margin-top: 12px;
    display: flex;
    flex-direction: column;
    gap: 4px;

    .batch-error-row {
      font-size: 11.5px;
      color: #b42318;
      background: #fef3f2;
      border-radius: 6px;
      padding: 5px 9px;
    }
  }
}
/* ── Alerts（真实告警）───────────────────────────────────────────── */
/* 没有未读告警时不再呼吸，避免"一直闪但没内容" */
.alerts-pill-btn:not(.has-unread) :deep(.pulsating-button__pulse) {
  animation: none;
  opacity: 0;
}

.alerts-modal-card {
  .alerts-total-chip {
    margin-left: 10px;
    font-size: 11.5px;
    color: #475467;
    background: #f2f4f7;
    border-radius: 999px;
    padding: 2px 10px;
    white-space: nowrap;
  }

  .alerts-body {
    max-height: 62vh;
    overflow-y: auto;
    padding: 12px 16px 16px;
  }

  .alerts-toolbar {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 10px;
  }

  .alerts-tool-btn {
    padding: 4px 12px;
    font-size: 12px;
    border: 1px solid #d0d5dd;
    border-radius: 6px;
    background: #ffffff;
    color: #344054;
    cursor: pointer;

    &:hover:not(:disabled) { border-color: #17b26a; color: #0f9755; }
    &:disabled { opacity: 0.5; cursor: not-allowed; }
    &.ghost { background: #f9fafb; }
  }

  .alerts-filter {
    margin-left: auto;
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #475467;
    cursor: pointer;

    input { accent-color: #17b26a; }
  }

  .alerts-empty {
    padding: 46px 0;
    text-align: center;
    font-size: 12.5px;
    color: #98a2b3;
  }

  .alerts-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .alert-box-item {
    .alert-actions {
      display: flex;
      gap: 6px;
      margin-top: 6px;
    }

    .alert-action-btn {
      padding: 2px 10px;
      font-size: 11.5px;
      border-radius: 5px;
      border: 1px solid #d0d5dd;
      background: #ffffff;
      color: #475467;
      cursor: pointer;

      &:hover { border-color: #98a2b3; }
      &.danger { color: #b42318; border-color: #fda29b; }
      &.danger:hover { background: #fef3f2; }
    }
  }
}
/* 非目标图像拒识提示（决策卡内） */
.rx-reject-notice {
  margin: 4px 0 2px;
  padding: 5px 9px;
  border-radius: 6px;
  background: #fef3f2;
  border: 1px solid #fda29b;
  color: #b42318;
  font-size: 12px;
  line-height: 1.45;
  flex: 0 0 auto;
}

/* 批量里被拒识的图片 */
.batch-rejected {
  margin-top: 12px;
  padding: 8px 10px;
  border-radius: 8px;
  background: #fffaeb;
  border: 1px solid #fedf89;

  .batch-rejected-head {
    font-size: 12px;
    font-weight: 600;
    color: #b54708;
    margin-bottom: 4px;
  }

  .batch-reject-row {
    display: flex;
    align-items: baseline;
    justify-content: space-between;
    gap: 12px;
    font-size: 11.5px;
    color: #93370d;
    line-height: 1.7;

    .br-name {
      flex: 1 1 auto;
      min-width: 0;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
    .br-reason {
      flex: 0 0 auto;
      color: #b54708;
      white-space: nowrap;
    }
  }
}
</style>
