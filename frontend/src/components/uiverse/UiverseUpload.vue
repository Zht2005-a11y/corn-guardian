<template>
  <div class="uiverse-upload-container">
    <!-- Uiverse.io Component: "custum-file-upload" by Yaya12085 (Adapted to Vue3Echarts Navy Style) -->
    <div
      class="custum-file-upload"
      :class="{ 'is-dragover': isDragging, 'has-file': !!previewUrl }"
      @dragover.prevent="handleDragOver"
      @dragleave.prevent="handleDragLeave"
      @drop.prevent="handleDrop"
      @click="triggerFileInput"
    >
      <div v-if="!previewUrl" class="upload-inner">
        <div class="icon">
          <!-- Uiverse.io SVG Icon in repository Ice-Blue -->
          <svg viewBox="0 0 24 24" fill="" xmlns="http://www.w3.org/2000/svg">
            <g id="SVGRepo_bgCarrier" stroke-width="0"></g>
            <g id="SVGRepo_tracerCarrier" stroke-linecap="round" stroke-linejoin="round"></g>
            <g id="SVGRepo_iconCarrier">
              <path
                fill-rule="evenodd"
                clip-rule="evenodd"
                d="M10 1C9.73478 1 9.48043 1.10536 9.29289 1.29289L3.29289 7.29289C3.10536 7.48043 3 7.73478 3 8V20C3 21.6569 4.34315 23 6 23H7C7.55228 23 8 22.5523 8 22C8 21.4477 7.55228 21 7 21H6C5.44772 21 5 20.5523 5 20V9H10C10.5523 9 11 8.55228 11 8V3H18C18.5523 3 19 3.44772 19 4V9C19 9.55228 19.4477 10 20 10C20.5523 10 21 9.55228 21 9V4C21 2.34315 19.6569 1 18 1H10ZM9 7H6.41421L9 4.41421V7ZM14 14C14 13.4477 14.4477 13 15 13C15.5523 13 16 13.4477 16 14V20.5858L17.2928 19.2929C17.6834 18.9024 18.3166 18.9024 18.7071 19.2929C19.0976 19.6834 19.0976 20.3166 18.7071 20.7071L15.7071 23.7071C15.3166 24.0976 14.6834 24.0976 14.2928 23.7071L11.2929 20.7071C10.9024 20.3166 10.9024 19.6834 11.2929 19.2929C11.6834 18.9024 12.3166 18.9024 12.7071 19.2929L14 20.5858V14Z"
                fill="currentColor"
              ></path>
            </g>
          </svg>
        </div>
        <div class="text">
          <span class="main-prompt">点击或拖拽上传大田玉米叶片图片</span>
          <span class="sub-prompt">支持复杂大田光照、水珠、微小病斑实测图像 (JPG/PNG)</span>
        </div>
      </div>

      <div v-else class="preview-box">
        <img :src="previewUrl" alt="玉米叶片" class="preview-img" />
        <div class="preview-mask">
          <span>点击更换图片</span>
        </div>
      </div>

      <input
        ref="fileInputRef"
        type="file"
        accept="image/*"
        class="hidden-file-input"
        @change="handleFileChange"
      />
    </div>

    <!-- 典型大田样本点选栏 -->
    <div class="sample-nav">
      <span class="sample-title">大田代表性样本：</span>
      <div class="sample-pills">
        <button
          v-for="sample in presetSamples"
          :key="sample.id"
          class="sample-pill-btn"
          :class="{ active: currentSampleId === sample.id }"
          @click.stop="selectPresetSample(sample)"
        >
          <span class="dot" :style="{ backgroundColor: sample.color }"></span>
          {{ sample.name }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const emit = defineEmits(['image-selected', 'image-cleared'])

const fileInputRef = ref(null)
const isDragging = ref(false)
const previewUrl = ref('')
const currentSampleId = ref('')

const presetSamples = [
  {
    id: 'blight',
    name: '大斑病 (强光直射)',
    diseaseName: '玉米大斑病 (Northern Leaf Blight)',
    pathogen: '大斑凸脐蠕孢 (Exserohilum turcicum)',
    severity: '重度 (III级扩散期)',
    confidence: 97.4,
    color: '#e28557',
    desc: '叶面呈长梭形灰褐色枯斑，伴强光日照反光干扰',
    boxes: [
      { x: 18, y: 22, w: 42, h: 28, label: '大斑侵染灶 #1', conf: '97.4%' },
      { x: 55, y: 46, w: 32, h: 36, label: '扩散性枯斑 #2', conf: '94.8%' }
    ],
    prescription: '选用 25% 嘧菌酯悬浮剂 1500倍液 或 10% 苯醚甲环唑 1000倍液，建议傍晚利用植保无人机实施精准变量喷雾。',
    imgData: generateSampleSvg('corn-blight')
  },
  {
    id: 'rust',
    name: '南方锈病 (高湿凝露)',
    diseaseName: '玉米南方锈病 (Southern Corn Rust)',
    pathogen: '多堆柄锈菌 (Puccinia polysora)',
    severity: '危急 (IV级暴发)',
    confidence: 98.8,
    color: '#f59e0b',
    desc: '叶面密生圆形橘黄色夏孢子堆，散生铁锈色粉末',
    boxes: [
      { x: 26, y: 16, w: 28, h: 32, label: '锈孢密集区 #1', conf: '98.8%' },
      { x: 48, y: 38, w: 38, h: 42, label: '夏孢子堆群 #2', conf: '96.2%' }
    ],
    prescription: '选用 430g/L 戊唑醇悬浮剂 3000倍液 或 30% 肟菌·戊唑醇 2000倍液，立即启动连片整田统防统治。',
    imgData: generateSampleSvg('corn-rust')
  },
  {
    id: 'gray_spot',
    name: '灰斑病 (叶脉受限)',
    diseaseName: '玉米灰斑病 (Gray Leaf Spot)',
    pathogen: '玉米尾孢菌 (Cercospora zeae-maydis)',
    severity: '中度 (II级发病)',
    confidence: 95.6,
    color: '#38bdf8',
    desc: '长方形窄条状灰褐色病斑，边缘平直，受叶脉严格限制',
    boxes: [
      { x: 22, y: 35, w: 54, h: 22, label: '条状灰斑', conf: '95.6%' }
    ],
    prescription: '选用 40% 氟硅唑乳油 8000倍液 + 磷酸二氢钾营养复配喷雾，有效抑制病斑沿叶脉向上下扩展。',
    imgData: generateSampleSvg('corn-gray-spot')
  },
  {
    id: 'brown_spot',
    name: '褐斑病 (叶鞘浸渍)',
    diseaseName: '玉米褐斑病 (Brown Spot)',
    pathogen: '玉蜀黍节壶菌 (Physoderma maydis)',
    severity: '轻度 (I级初期)',
    confidence: 93.2,
    color: '#c084fc',
    desc: '叶片及叶鞘基部紫褐色圆形小脓疱，伴泥渍溅污',
    boxes: [
      { x: 30, y: 28, w: 35, h: 35, label: '微型褐脓斑', conf: '93.2%' }
    ],
    prescription: '选用 12.5% 烯唑醇可湿性粉剂 1000倍液喷雾防治，重点喷施玉米植株茎秆及叶鞘紧密结合部。',
    imgData: generateSampleSvg('corn-brown-spot')
  },
  {
    id: 'healthy',
    name: '健康植株 (长势优良)',
    diseaseName: '健康玉米叶片 (Healthy Corn Canopy)',
    pathogen: '无致病菌检出 (Negative)',
    severity: '正常 (健康态)',
    confidence: 99.2,
    color: '#22c55e',
    desc: '叶色翠绿舒展，叶脉清晰匀称，无坏死斑及褪绿条纹',
    boxes: [],
    prescription: '植株健康长势良好，维持大田水肥一体化管理，按常规物候期适量补充叶面微肥。',
    imgData: generateSampleSvg('corn-healthy')
  }
]

function generateSampleSvg(type) {
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

function triggerFileInput() {
  fileInputRef.value && fileInputRef.value.click()
}

function handleFileChange(e) {
  const file = e.target.files && e.target.files[0]
  if (file) {
    processImageFile(file)
  }
}

function handleDragOver() {
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function handleDrop(e) {
  isDragging.value = false
  const file = e.dataTransfer.files && e.dataTransfer.files[0]
  if (file && file.type.startsWith('image/')) {
    processImageFile(file)
  }
}

function processImageFile(file) {
  currentSampleId.value = 'custom'
  const reader = new FileReader()
  reader.onload = (e) => {
    previewUrl.value = e.target.result
    const customMeta = {
      id: 'custom',
      name: file.name,
      diseaseName: '玉米大斑病 (疑似大田侵染)',
      pathogen: '大斑凸脐蠕孢 (Exserohilum turcicum)',
      severity: '重度 (III级扩散期)',
      confidence: 96.5,
      color: '#e28557',
      desc: '叶面检测到典型长条形干枯病斑，边缘浸润加深',
      boxes: [
        { x: 25, y: 30, w: 38, h: 32, label: '大斑病灶 #1', conf: '96.5%' },
        { x: 50, y: 45, w: 28, h: 30, label: '初侵染病斑 #2', conf: '92.1%' }
      ],
      prescription: '建议立即实施连片整田喷药，选用25%苯醚甲环唑或嘧菌酯悬浮剂1500倍液。',
      imgData: previewUrl.value
    }
    emit('image-selected', customMeta)
  }
  reader.readAsDataURL(file)
}

function selectPresetSample(sample) {
  currentSampleId.value = sample.id
  previewUrl.value = sample.imgData
  emit('image-selected', sample)
}

// 默认直接选中大斑病样本
selectPresetSample(presetSamples[0])
</script>

<style lang="scss" scoped>
.uiverse-upload-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 100%;
}

.custum-file-upload {
  height: 200px;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  border: 1.5px dashed #cbd5e1;
  background: #f8fafc;
  border-radius: 8px;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
  box-sizing: border-box;

  &:hover,
  &.is-dragover {
    border-color: #059669;
    background: #f0fdf4;
  }
}

.upload-inner {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;

  .icon svg {
    width: 40px;
    height: 40px;
    fill: #059669;
    transition: transform 0.25s ease;
  }

  .text {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;

    .main-prompt {
      font-size: 13px;
      font-weight: 600;
      color: #0f172a;
      letter-spacing: 0.2px;
    }

    .sub-prompt {
      font-size: 11px;
      color: #64748b;
    }
  }
}

.custum-file-upload:hover .upload-inner .icon svg {
  transform: translateY(-2px);
}

.preview-box {
  width: 100%;
  height: 100%;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;

  .preview-img {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .preview-mask {
    position: absolute;
    inset: 0;
    background: rgba(15, 23, 42, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    opacity: 0;
    transition: opacity 0.2s ease;

    span {
      color: #ffffff;
      font-size: 12px;
      background: #059669;
      padding: 5px 14px;
      border-radius: 6px;
      font-weight: 500;
      box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
    }
  }

  &:hover .preview-mask {
    opacity: 1;
  }
}

.hidden-file-input {
  display: none;
}

/* 样本选择药丸栏 */
.sample-nav {
  display: flex;
  align-items: center;
  width: 100%;
  margin-top: 8px;
  padding: 4px 6px;
  box-sizing: border-box;

  .sample-title {
    font-size: 12px;
    font-weight: 600;
    color: #475569;
    white-space: nowrap;
    margin-right: 8px;
  }

  .sample-pills {
    display: flex;
    flex-wrap: wrap;
    gap: 6px;

    .sample-pill-btn {
      display: inline-flex;
      align-items: center;
      gap: 6px;
      padding: 4px 10px;
      border-radius: 6px;
      font-size: 11px;
      color: #475569;
      background: #ffffff;
      border: 1px solid #e2e8f0;
      cursor: pointer;
      transition: all 0.2s;

      .dot {
        width: 6px;
        height: 6px;
        border-radius: 50%;
      }

      &:hover {
        border-color: #059669;
        background: #f0fdf4;
        color: #059669;
      }

      &.active {
        background: #ecfdf5;
        border-color: #059669;
        color: #059669;
        font-weight: 600;
        box-shadow: 0 1px 3px rgba(5, 150, 105, 0.12);
      }
    }
  }
}
</style>
