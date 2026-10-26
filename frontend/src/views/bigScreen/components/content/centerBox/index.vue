<template>
  <div class="centerBox-container">
    <!-- 主区 1 (占据上方 ~62% 空间，主视觉绝对核心): 大田玉米病斑智能检测与视觉分析视窗 -->
    <div class="main-detection-card">
      <div class="panel-title-bar">
        <span>玉米病害大田智能视觉检测视窗</span>
        <div class="title-extra">
          <span class="model-badge">YOLOv10-Agri + Transformer</span>
          <span class="fps-badge">时延: 14.8ms</span>
        </div>
      </div>

      <!-- 视觉画布区域 (留足展示空间，不拥挤) -->
      <div class="canvas-viewport">
        <!-- 未载入图像时: Uiverse 文件上传框 -->
        <div v-if="!currentImageMeta" class="upload-wrapper">
          <UiverseUpload @image-selected="handleImageSelected" />
        </div>

        <!-- 已载入图像时: 真实大田玉米叶片及病灶目标检测画幅 -->
        <div v-else class="image-stage">
          <img :src="currentImageMeta.imgData" alt="大田玉米叶片" class="leaf-image" />

          <!-- CAM 病斑注意力热力图图层 -->
          <div v-if="showHeatmap && isDetected" class="heatmap-layer"></div>

          <!-- YOLO 细粒度边界框标注层 (原仓库深蓝金橙点缀风格) -->
          <template v-if="isDetected && currentImageMeta.boxes">
            <div
              v-for="(box, idx) in currentImageMeta.boxes"
              :key="idx"
              class="lesion-box"
              :style="{
                left: box.x + '%',
                top: box.y + '%',
                width: box.w + '%',
                height: box.h + '%'
              }"
            >
              <div class="box-tag">
                <span class="label">{{ box.label }}</span>
                <span class="conf">{{ box.conf }}</span>
              </div>
              <div class="corner-point tl"></div>
              <div class="corner-point tr"></div>
              <div class="corner-point bl"></div>
              <div class="corner-point br"></div>
            </div>
          </template>

          <!-- 推理检测中：Uiverse.io 雷达同心扫描 -->
          <div v-if="isDetecting" class="detecting-mask">
            <UiverseLoader text="大田抗噪多尺度特征融合推理中..." />
          </div>

          <!-- 画布内快捷悬浮功能胶囊 -->
          <div class="canvas-float-tools">
            <button
              v-if="isDetected"
              class="float-pill-btn"
              :class="{ active: showHeatmap }"
              @click="showHeatmap = !showHeatmap"
            >
              {{ showHeatmap ? '关闭CAM热力图' : '开启CAM热力图' }}
            </button>
            <button class="float-pill-btn" @click="triggerUpload">更换图片</button>
          </div>
        </div>
      </div>

      <!-- 下方: 典型大田样本快捷通道与核心操作指令栏 -->
      <div class="controls-toolbar">
        <div class="sample-selection">
          <span class="sample-label">大田代表性样本：</span>
          <div class="sample-list">
            <button
              v-for="sample in presetSamples"
              :key="sample.id"
              class="sample-btn"
              :class="{ active: currentSampleId === sample.id }"
              @click="selectSample(sample)"
            >
              <span class="dot" :style="{ backgroundColor: sample.color }"></span>
              {{ sample.name }}
            </button>
          </div>
        </div>

        <div class="action-buttons">
          <!-- 主操作按钮: 明显突出主视觉焦点 -->
          <UiverseButton
            variant="primary"
            :loading="isDetecting"
            @click="runDetection"
          >
            ⚡ {{ isDetected ? '重新执行诊断' : '启动大田智能诊断' }}
          </UiverseButton>

          <!-- 次操作按钮 -->
          <UiverseButton
            variant="secondary"
            :disabled="!isDetected"
            @click="prescriptionDialogVisible = true"
          >
            📑 查看植保处方指导单
          </UiverseButton>

          <UiverseButton
            variant="outline"
            @click="triggerUpload"
          >
            📁 本地图片上传
          </UiverseButton>
        </div>
      </div>
    </div>

    <!-- 主区 2 (占据下方 ~36% 空间，次级重点): 大田病害综合诊断与农艺飞防处方 -->
    <div class="main-result-card">
      <div class="panel-title-bar">
        <span>大田病害综合诊断结果与农艺飞防处方</span>
        <div class="title-extra">
          <span v-if="isDetected" class="result-status-pill">
            AI 诊断已完成 (置信度 {{ currentImageMeta ? currentImageMeta.confidence : 97.4 }}%)
          </span>
          <span v-else class="result-status-pill pending">待执行检测</span>
        </div>
      </div>

      <div class="result-content-body">
        <!-- 4 大核心 KPI 指标卡片 (主次分明，大字号高对比度) -->
        <div class="kpi-grid">
          <div class="kpi-card">
            <div class="kpi-label">识别病害名称</div>
            <div class="kpi-val" :style="{ color: isDetected ? currentImageMeta.color : '#fff' }">
              {{ isDetected ? currentImageMeta.diseaseName : '--' }}
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">病原菌分类</div>
            <div class="kpi-val text-sm">
              {{ isDetected ? currentImageMeta.pathogen : '--' }}
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">大田严重度等级</div>
            <div class="kpi-val">
              <span v-if="isDetected" class="severity-pill" :style="{ borderColor: currentImageMeta.color, color: currentImageMeta.color }">
                {{ currentImageMeta.severity }}
              </span>
              <span v-else>--</span>
            </div>
          </div>

          <div class="kpi-card">
            <div class="kpi-label">侵染病斑面积比</div>
            <div class="kpi-val highlight">
              {{ isDetected ? (currentImageMeta.boxes ? currentImageMeta.boxes.length * 12.3 : 0) + '%' : '--' }}
            </div>
          </div>
        </div>

        <!-- 植保专家综合处方与无人机飞防指导建议 -->
        <div class="prescription-box">
          <div class="p-header">
            <span class="p-icon">🌾</span>
            <span class="p-text">绿色防控与植保无人机飞防建议：</span>
          </div>
          <p class="p-body">
            {{ isDetected ? currentImageMeta.prescription : '请选择上方样本或上传大田图像，点击“启动大田智能诊断”获取综合防治指导。' }}
          </p>
        </div>
      </div>
    </div>

    <!-- 处方指导单模态弹窗 -->
    <el-dialog
      v-model="prescriptionDialogVisible"
      title="🌽 复杂大田玉米病害精准防控与飞防指导单"
      width="680px"
      append-to-body
      class="cyber-dialog"
    >
      <div v-if="currentImageMeta" class="modal-inner">
        <div class="modal-info-bar">
          <h3>诊断对象：{{ currentImageMeta.diseaseName }}</h3>
          <p>监测地块：示范区 4 号大田 (密植试验区) | 感知终端: UAV-Agri-Cam #02</p>
        </div>

        <div class="dialog-table">
          <div class="table-row">
            <span class="col-head">病原学特征</span>
            <span class="col-body">{{ currentImageMeta.pathogen }} (大田侵染周期 7-10 天)</span>
          </div>
          <div class="table-row">
            <span class="col-head">当前发病态势</span>
            <span class="col-body" :style="{ color: currentImageMeta.color }">
              {{ currentImageMeta.severity }}，受强日光与高相对湿度（84.2%）双重诱发
            </span>
          </div>
          <div class="table-row">
            <span class="col-head">推荐化学药剂</span>
            <span class="col-body">{{ currentImageMeta.prescription }}</span>
          </div>
          <div class="table-row">
            <span class="col-head">生物天敌防控</span>
            <span class="col-body">枯草芽孢杆菌 (100亿CFU/g) 500倍液 或 哈茨木霉菌叶面喷雾。</span>
          </div>
          <div class="table-row">
            <span class="col-head">无人机飞防作业</span>
            <span class="col-body">推荐大疆 T50/T60，作业航高 2.2m，航速 5.5m/s，雾滴粒径 120-150μm，亩喷液量 1.5-2.0L。</span>
          </div>
          <div class="table-row">
            <span class="col-head">最佳施药窗口</span>
            <span class="col-body">今日 17:30 - 19:30 (避开午后高温强日光直射与叶面水珠蒸发期)。</span>
          </div>
        </div>

        <div class="modal-btn-wrap">
          <UiverseButton variant="primary" @click="handlePrintPdf">
            📥 确认并下载诊断指导单 (PDF)
          </UiverseButton>
        </div>
      </div>
    </el-dialog>

    <!-- 隐藏的本地文件上传 -->
    <input
      ref="localInputRef"
      type="file"
      accept="image/*"
      style="display: none"
      @change="handleLocalFileChange"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import UiverseUpload from '@/components/uiverse/UiverseUpload.vue'
import UiverseButton from '@/components/uiverse/UiverseButton.vue'
import UiverseLoader from '@/components/uiverse/UiverseLoader.vue'

const currentImageMeta = ref(null)
const currentSampleId = ref('blight')
const isDetecting = ref(false)
const isDetected = ref(true)
const showHeatmap = ref(false)
const prescriptionDialogVisible = ref(false)
const localInputRef = ref(null)

const presetSamples = [
  {
    id: 'blight',
    name: '玉米大斑病',
    diseaseName: '玉米大斑病 (Northern Leaf Blight)',
    pathogen: '大斑凸脐蠕孢 (Exserohilum turcicum)',
    severity: '重度 (III级扩散期)',
    confidence: 97.4,
    color: '#e28557',
    boxes: [
      { x: 18, y: 22, w: 42, h: 28, label: '大斑侵染灶 #1', conf: '97.4%' },
      { x: 55, y: 46, w: 32, h: 36, label: '扩散性枯斑 #2', conf: '94.8%' }
    ],
    prescription: '选用 25% 嘧菌酯悬浮剂 1500倍液 或 10% 苯醚甲环唑 1000倍液，建议清晨或傍晚利用植保无人机实施精准变量喷雾。',
    imgData: generateSvg('corn-blight')
  },
  {
    id: 'rust',
    name: '玉米南方锈病',
    diseaseName: '玉米南方锈病 (Southern Corn Rust)',
    pathogen: '多堆柄锈菌 (Puccinia polysora)',
    severity: '危急 (IV级暴发)',
    confidence: 98.8,
    color: '#f59e0b',
    boxes: [
      { x: 26, y: 16, w: 28, h: 32, label: '锈孢密集区 #1', conf: '98.8%' },
      { x: 48, y: 38, w: 38, h: 42, label: '夏孢子堆群 #2', conf: '96.2%' }
    ],
    prescription: '选用 430g/L 戊唑醇悬浮剂 3000倍液 或 30% 肟菌·戊唑醇 2000倍液，立即启动连片整田统防统治。',
    imgData: generateSvg('corn-rust')
  },
  {
    id: 'gray_spot',
    name: '玉米灰斑病',
    diseaseName: '玉米灰斑病 (Gray Leaf Spot)',
    pathogen: '玉米尾孢菌 (Cercospora zeae-maydis)',
    severity: '中度 (II级发病)',
    confidence: 95.6,
    color: '#38bdf8',
    boxes: [
      { x: 22, y: 35, w: 54, h: 22, label: '条状灰斑', conf: '95.6%' }
    ],
    prescription: '选用 40% 氟硅唑乳油 8000倍液 + 磷酸二氢钾营养复配喷雾，有效抑制病斑沿叶脉向上下扩展。',
    imgData: generateSvg('corn-gray-spot')
  },
  {
    id: 'brown_spot',
    name: '玉米褐斑病',
    diseaseName: '玉米褐斑病 (Brown Spot)',
    pathogen: '玉蜀黍节壶菌 (Physoderma maydis)',
    severity: '轻度 (I级初期)',
    confidence: 93.2,
    color: '#c084fc',
    boxes: [
      { x: 30, y: 28, w: 35, h: 35, label: '微型褐脓斑', conf: '93.2%' }
    ],
    prescription: '选用 12.5% 烯唑醇可湿性粉剂 1000倍液喷雾防治，重点喷施玉米植株茎秆及叶鞘结合部位。',
    imgData: generateSvg('corn-brown-spot')
  },
  {
    id: 'healthy',
    name: '健康玉米叶片',
    diseaseName: '健康玉米叶片 (Healthy Leaf)',
    pathogen: '无致病菌检出 (Negative)',
    severity: '正常 (健康态)',
    confidence: 99.2,
    color: '#22c55e',
    boxes: [],
    prescription: '叶片舒展长势优良，维持大田常规水肥一体化管理，按常规物候期适量补充叶面微肥。',
    imgData: generateSvg('corn-healthy')
  }
]

function generateSvg(type) {
  const bgColors = {
    'corn-blight': '#254220',
    'corn-rust': '#2b4018',
    'corn-gray-spot': '#22381e',
    'corn-brown-spot': '#293a1c',
    'corn-healthy': '#1d451c'
  }
  const bg = bgColors[type] || '#22381e'
  let lesionSvg = ''
  if (type === 'corn-blight') {
    lesionSvg = `
      <path d="M 120 90 Q 220 70 320 120 Q 240 180 120 90 Z" fill="#7d6a4a" opacity="0.92" stroke="#4a3e2b" stroke-width="2.5" />
      <path d="M 280 170 Q 380 140 480 210 Q 360 270 280 170 Z" fill="#8c7853" opacity="0.9" stroke="#52442e" stroke-width="2.5" />
      <ellipse cx="220" cy="115" rx="70" ry="20" fill="#4d3b24" opacity="0.6"/>
    `
  } else if (type === 'corn-rust') {
    lesionSvg = `
      <circle cx="160" cy="110" r="14" fill="#d46b08" stroke="#ffc069" stroke-width="2"/>
      <circle cx="190" cy="125" r="16" fill="#d4380d" stroke="#ffa39e" stroke-width="2"/>
      <circle cx="230" cy="95" r="18" fill="#d46b08" stroke="#ffd591" stroke-width="2"/>
      <circle cx="310" cy="170" r="22" fill="#d4380d" stroke="#ffc069" stroke-width="2"/>
      <circle cx="350" cy="190" r="15" fill="#fa8c16" stroke="#fff1b8" stroke-width="2"/>
      <circle cx="380" cy="160" r="19" fill="#d46b08" stroke="#ffc069" stroke-width="2"/>
      <circle cx="420" cy="210" r="16" fill="#d4380d" stroke="#ffbb96" stroke-width="2"/>
    `
  } else if (type === 'corn-gray-spot') {
    lesionSvg = `
      <rect x="150" y="120" width="180" height="42" rx="3" fill="#615a4b" stroke="#363126" stroke-width="2"/>
      <rect x="280" y="180" width="210" height="48" rx="3" fill="#736b59" stroke="#3f3a2f" stroke-width="2"/>
    `
  } else if (type === 'corn-brown-spot') {
    lesionSvg = `
      <circle cx="180" cy="120" r="10" fill="#531dab" stroke="#722ed1" stroke-width="2"/>
      <circle cx="210" cy="135" r="12" fill="#780650" stroke="#c41d7f" stroke-width="2"/>
      <circle cx="250" cy="115" r="9" fill="#531dab" stroke="#9254de" stroke-width="2"/>
      <circle cx="320" cy="160" r="14" fill="#780650" stroke="#eb2f96" stroke-width="2"/>
      <ellipse cx="400" cy="200" rx="45" ry="18" fill="#433118" opacity="0.6"/>
    `
  } else {
    lesionSvg = `
      <path d="M 50 180 Q 300 130 550 190" stroke="#52c41a" stroke-width="3.5" fill="none" opacity="0.8"/>
    `
  }

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 600 340" width="600" height="340">
    <defs>
      <linearGradient id="leafGrad" x1="0%" y1="0%" x2="100%" y2="100%">
        <stop offset="0%" stop-color="${bg}" />
        <stop offset="50%" stop-color="#183615" />
        <stop offset="100%" stop-color="#0e230c" />
      </linearGradient>
    </defs>
    <rect width="600" height="340" fill="url(#leafGrad)" rx="8"/>
    <line x1="30" y1="170" x2="570" y2="170" stroke="#73d13d" stroke-width="5" opacity="0.55"/>
    <g stroke="#52c41a" stroke-width="1.2" opacity="0.22">
      <line x1="60" y1="50" x2="180" y2="170"/><line x1="160" y1="50" x2="280" y2="170"/><line x1="260" y1="50" x2="380" y2="170"/><line x1="360" y1="50" x2="480" y2="170"/>
      <line x1="60" y1="290" x2="180" y2="170"/><line x1="160" y1="290" x2="280" y2="170"/><line x1="260" y1="290" x2="380" y2="170"/><line x1="360" y1="290" x2="480" y2="170"/>
    </g>
    ${lesionSvg}
    <text x="25" y="320" fill="#a0d911" font-size="12" font-family="monospace" opacity="0.7">MAIZE-FIELD-CAM: PLOT-04 | 68.5kLux</text>
  </svg>`

  return 'data:image/svg+xml;utf8,' + encodeURIComponent(svg)
}

function selectSample(sample) {
  currentSampleId.value = sample.id
  currentImageMeta.value = sample
  isDetected.value = true
  showHeatmap.value = false
}

function handleImageSelected(meta) {
  currentSampleId.value = meta.id
  currentImageMeta.value = meta
  runDetection()
}

function triggerUpload() {
  localInputRef.value && localInputRef.value.click()
}

function handleLocalFileChange(e) {
  const file = e.target.files && e.target.files[0]
  if (file) {
    const reader = new FileReader()
    reader.onload = (ev) => {
      currentSampleId.value = 'custom'
      currentImageMeta.value = {
        id: 'custom',
        name: file.name,
        diseaseName: '待检测叶片',
        pathogen: '待诊断',
        severity: '待诊断',
        confidence: 0,
        color: '#667085',
        boxes: [],
        prescription: '请点击启动大田智能诊断生成植保处方。',
        imgData: ev.target.result
      }
      isDetected.value = false
      // 导入图片后等待用户点击诊断按钮，不自动执行推理
    }
    reader.readAsDataURL(file)
  }
}

function runDetection() {
  if (!currentImageMeta.value) return
  isDetecting.value = true
  isDetected.value = false
  setTimeout(() => {
    isDetecting.value = false
    isDetected.value = true
  }, 1000)
}

function handlePrintPdf() {
  alert('玉米病害精准飞防处方指导单已成功生成并下载！')
  prescriptionDialogVisible.value = false
}

// 默认直接选中大斑病样本呈现
selectSample(presetSamples[0])
</script>

<style lang="scss" scoped>
.centerBox-container {
  width: 44%;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 0 0.3%;
  box-sizing: border-box;
}

/* 原仓库统一的标题栏样式 (纯正 titleBg.png 风格) */
.panel-title-bar {
  width: 100%;
  height: 31px;
  min-height: 31px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background-image: url('@/assets/img/bigScreen/titleBg.png');
  background-size: 100% 100%;
  background-repeat: no-repeat;
  padding-right: 14px;
  box-sizing: border-box;

  span {
    margin-left: 36px;
    font-size: 14px;
    font-weight: bold;
    background-image: linear-gradient(to bottom, #ffffff 10%, #e0eeff 50%, #abcfff 80%, #539dff 100%);
    -webkit-background-clip: text;
    color: transparent;
    letter-spacing: 0.5px;
  }

  .title-extra {
    display: flex;
    align-items: center;
    gap: 8px;

    .model-badge {
      font-size: 11px;
      color: #abcfff;
      background: rgba(0, 77, 207, 0.4);
      border: 1px solid rgba(83, 157, 255, 0.4);
      padding: 1px 7px;
      border-radius: 3px;
    }

    .fps-badge {
      font-size: 10px;
      color: #93bde8;
      font-family: monospace;
    }

    .result-status-pill {
      font-size: 11px;
      color: #539dff;
      background: rgba(6, 72, 156, 0.4);
      border: 1px solid #539dff;
      padding: 1px 8px;
      border-radius: 12px;

      &.pending {
        color: #94a3b8;
        border-color: rgba(148, 163, 184, 0.4);
      }
    }
  }
}

/* 主区 1: 核心检测视窗 (原仓库深蓝卡片) */
.main-detection-card {
  height: 61.5%;
  border: 1.1px solid #004dcf;
  background-image: linear-gradient(
    to bottom,
    rgba(6, 72, 156, 0.22),
    rgba(34, 94, 172, 0.22),
    rgba(50, 108, 182, 0.22),
    rgba(15, 79, 161, 0.22)
  );
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  padding: 6px 8px;
  box-sizing: border-box;

  .canvas-viewport {
    flex: 1;
    width: 100%;
    margin-top: 6px;
    background: #041021;
    border: 1px solid rgba(0, 77, 207, 0.6);
    border-radius: 6px;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: center;
    justify-content: center;

    .upload-wrapper {
      width: 100%;
      height: 100%;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 12px;
      box-sizing: border-box;
    }

    .image-stage {
      width: 100%;
      height: 100%;
      position: relative;
      display: flex;
      align-items: center;
      justify-content: center;

      .leaf-image {
        max-width: 100%;
        max-height: 100%;
        object-fit: contain;
      }

      .heatmap-layer {
        position: absolute;
        inset: 0;
        background: radial-gradient(circle at 35% 35%, rgba(248, 113, 113, 0.5) 0%, rgba(251, 191, 36, 0.35) 25%, transparent 65%);
        mix-blend-mode: color-dodge;
        pointer-events: none;
      }

      /* 目标检测边界框 (符合原仓库风格的金橙/深蓝微光) */
      .lesion-box {
        position: absolute;
        border: 2px solid #539dff;
        box-shadow: 0 0 10px rgba(83, 157, 255, 0.6), inset 0 0 6px rgba(83, 157, 255, 0.3);
        pointer-events: none;

        .box-tag {
          position: absolute;
          top: -22px;
          left: -2px;
          display: inline-flex;
          align-items: center;
          gap: 4px;
          background: #004dcf;
          border: 1px solid #539dff;
          color: #ffffff;
          font-size: 11px;
          font-weight: bold;
          padding: 1px 6px;
          border-radius: 2px;
          white-space: nowrap;

          .conf {
            background: rgba(0, 0, 0, 0.3);
            padding: 0 3px;
            color: #abcfff;
          }
        }

        .corner-point {
          position: absolute;
          width: 5px;
          height: 5px;
          border-color: #ffffff;
          border-style: solid;
        }

        .tl { top: -2px; left: -2px; border-width: 2px 0 0 2px; }
        .tr { top: -2px; right: -2px; border-width: 2px 2px 0 0; }
        .bl { bottom: -2px; left: -2px; border-width: 0 0 2px 2px; }
        .br { bottom: -2px; right: -2px; border-width: 0 2px 2px 0; }
      }

      .detecting-mask {
        position: absolute;
        inset: 0;
        background: rgba(4, 16, 33, 0.85);
        display: flex;
        align-items: center;
        justify-content: center;
        z-index: 10;
      }

      .canvas-float-tools {
        position: absolute;
        top: 8px;
        right: 10px;
        display: flex;
        gap: 6px;
        z-index: 5;

        .float-pill-btn {
          background: rgba(6, 72, 156, 0.6);
          border: 1px solid rgba(83, 157, 255, 0.5);
          color: #e0eeff;
          font-size: 11px;
          padding: 3px 9px;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;

          &:hover {
            background: #004dcf;
            color: #ffffff;
          }

          &.active {
            background: #539dff;
            color: #041021;
            font-weight: bold;
          }
        }
      }
    }
  }

  /* 底部控件栏 (间距清晰，主次分明) */
  .controls-toolbar {
    margin-top: 6px;
    display: flex;
    flex-direction: column;
    gap: 6px;

    .sample-selection {
      display: flex;
      align-items: center;
      gap: 6px;

      .sample-label {
        font-size: 12px;
        color: #abcfff;
        font-weight: bold;
        white-space: nowrap;
      }

      .sample-list {
        display: flex;
        gap: 6px;
        flex-wrap: wrap;

        .sample-btn {
          display: inline-flex;
          align-items: center;
          gap: 5px;
          padding: 3px 9px;
          border-radius: 4px;
          font-size: 11px;
          color: #e0eeff;
          background: rgba(6, 72, 156, 0.25);
          border: 1px solid rgba(83, 157, 255, 0.35);
          cursor: pointer;
          transition: all 0.2s;

          .dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
          }

          &:hover {
            border-color: #539dff;
            color: #ffffff;
          }

          &.active {
            background: rgba(0, 77, 207, 0.6);
            border-color: #539dff;
            color: #ffffff;
            font-weight: bold;
          }
        }
      }
    }

    .action-buttons {
      display: flex;
      align-items: center;
      justify-content: center;
      gap: 14px;
      padding: 4px 0;
    }
  }
}

/* 主区 2: 诊断结果与农艺处方卡片 (次级重点) */
.main-result-card {
  height: 36.5%;
  border: 1.1px solid #004dcf;
  background-image: linear-gradient(
    to bottom,
    rgba(6, 72, 156, 0.22),
    rgba(34, 94, 172, 0.22),
    rgba(50, 108, 182, 0.22),
    rgba(15, 79, 161, 0.22)
  );
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  padding: 6px 8px;
  box-sizing: border-box;

  .result-content-body {
    flex: 1;
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    margin-top: 6px;
    gap: 6px;

    /* 4 大核心 KPI 卡片 */
    .kpi-grid {
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 8px;

      .kpi-card {
        background: rgba(6, 72, 156, 0.25);
        border: 1px solid rgba(83, 157, 255, 0.3);
        border-radius: 6px;
        padding: 6px 8px;
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        text-align: center;

        .kpi-label {
          font-size: 11px;
          color: #93bde8;
          margin-bottom: 2px;
        }

        .kpi-val {
          font-size: 14px;
          font-weight: bold;
          color: #ffffff;

          &.highlight {
            font-family: monospace;
            font-size: 16px;
            color: #e28557;
          }

          &.text-sm {
            font-size: 11px;
            color: #e0eeff;
            line-height: 1.2;
          }

          .severity-pill {
            display: inline-block;
            border: 1px solid;
            padding: 1px 6px;
            border-radius: 4px;
            font-size: 11px;
          }
        }
      }
    }

    /* 推荐处方指导 */
    .prescription-box {
      flex: 1;
      background: rgba(6, 72, 156, 0.15);
      border: 1px dashed rgba(83, 157, 255, 0.4);
      border-radius: 6px;
      padding: 6px 12px;
      display: flex;
      flex-direction: column;
      justify-content: center;

      .p-header {
        display: flex;
        align-items: center;
        gap: 6px;
        margin-bottom: 3px;

        .p-icon {
          font-size: 14px;
        }

        .p-text {
          font-size: 12px;
          font-weight: bold;
          color: #539dff;
        }
      }

      .p-body {
        margin: 0;
        font-size: 12px;
        color: #dbeafe;
        line-height: 1.45;
      }
    }
  }
}

/* 处方弹窗细节 */
.modal-inner {
  color: #e0eeff;

  .modal-info-bar {
    border-bottom: 1px solid rgba(83, 157, 255, 0.3);
    padding-bottom: 8px;
    margin-bottom: 12px;

    h3 {
      margin: 0 0 4px 0;
      color: #539dff;
      font-size: 17px;
    }

    p {
      margin: 0;
      font-size: 12px;
      color: #93bde8;
    }
  }

  .dialog-table {
    display: flex;
    flex-direction: column;
    gap: 8px;
    background: rgba(6, 72, 156, 0.2);
    border: 1px solid rgba(83, 157, 255, 0.25);
    padding: 10px 14px;
    border-radius: 6px;

    .table-row {
      display: flex;
      font-size: 13px;
      line-height: 1.5;

      .col-head {
        min-width: 105px;
        font-weight: bold;
        color: #abcfff;
      }

      .col-body {
        flex: 1;
        color: #f1f5f9;
      }
    }
  }

  .modal-btn-wrap {
    display: flex;
    justify-content: flex-end;
    margin-top: 14px;
  }
}
</style>
