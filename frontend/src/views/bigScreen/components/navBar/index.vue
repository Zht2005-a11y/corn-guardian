<template>
  <div class="navBar">
    <!-- 原仓库经典大屏顶栏背景图 -->
    <img src="@/assets/img/bigScreen/title1.png" class="navBarImg" alt="大屏顶栏" />

    <!-- React Bits 液态玻璃微质感层 (融入原仓库深蓝宝石质感) -->
    <div class="liquid-glass-layer">
      <LiquidGlass
        :tint="[0.05, 0.22, 0.65]"
        :speed="0.45"
        :amplitude="0.25"
        :detail="3.5"
        :roughness="0.12"
        :interactive="true"
      />
    </div>

    <!-- 顶栏内容层 (左侧状态、中央大标题、右侧时间气象) -->
    <div class="navBar-content">
      <div class="nav-left">
        <span class="dot-indicator"></span>
        <span class="system-status">复杂大田感知节点: 4号试验区在线</span>
        <span class="status-tag">多尺度抗噪自适应</span>
      </div>

      <div class="nav-center">
        <div class="title-text">面向复杂大田环境的玉米病害智能诊断系统</div>
        <div class="subtitle-text">Intelligent Diagnosis & Management System for Maize Foliar Diseases</div>
      </div>

      <div class="nav-right">
        <div class="env-chip">
          <span class="icon">⛅</span>
          <span class="val">28.4°C / 84.2% RH</span>
        </div>
        <div class="clock-chip">
          <span class="time">{{ currentTime }}</span>
          <span class="date">{{ currentDate }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import LiquidGlass from '@/components/LiquidGlass.vue'

const currentTime = ref('')
const currentDate = ref('')
let timer = null

const updateClock = () => {
  const now = new Date()
  const hours = String(now.getHours()).padStart(2, '0')
  const minutes = String(now.getMinutes()).padStart(2, '0')
  const seconds = String(now.getSeconds()).padStart(2, '0')
  currentTime.value = `${hours}:${minutes}:${seconds}`

  const year = now.getFullYear()
  const month = String(now.getMonth() + 1).padStart(2, '0')
  const date = String(now.getDate()).padStart(2, '0')
  const days = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  currentDate.value = `${year}.${month}.${date} ${days[now.getDay()]}`
}

onMounted(() => {
  updateClock()
  timer = setInterval(updateClock, 1000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style lang="scss" scoped>
.navBar {
  position: relative;
  width: 100%;
  height: 7.2vh;
  min-height: 56px;
  overflow: hidden;
  user-select: none;

  .navBarImg {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    z-index: 1;
    pointer-events: none;
  }

  .liquid-glass-layer {
    position: absolute;
    top: 0;
    left: 15%;
    width: 70%;
    height: 100%;
    opacity: 0.35;
    z-index: 2;
    mix-blend-mode: screen;
    pointer-events: none;
  }

  .navBar-content {
    position: relative;
    z-index: 3;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 100%;
    padding: 0 1.8%;
    box-sizing: border-box;
  }

  .nav-left {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 8px;
    padding-bottom: 0.8vh;

    .dot-indicator {
      width: 7px;
      height: 7px;
      border-radius: 50%;
      background: #539dff;
      box-shadow: 0 0 6px #539dff;
    }

    .system-status {
      font-size: 13px;
      color: #e0eeff;
      letter-spacing: 0.5px;
    }

    .status-tag {
      font-size: 11px;
      color: #abcfff;
      background: rgba(0, 77, 207, 0.35);
      border: 1px solid rgba(83, 157, 255, 0.4);
      padding: 1px 7px;
      border-radius: 4px;
    }
  }

  .nav-center {
    flex: 2;
    text-align: center;
    padding-bottom: 0.6vh;

    .title-text {
      font-size: 25px;
      font-weight: bold;
      letter-spacing: 2.5px;
      background-image: linear-gradient(to bottom, #ffffff 15%, #e0eeff 50%, #abcfff 75%, #539dff 100%);
      -webkit-background-clip: text;
      color: transparent;
      text-shadow: 0 2px 10px rgba(0, 77, 207, 0.5);
    }

    .subtitle-text {
      font-size: 10px;
      color: #93bde8;
      letter-spacing: 0.8px;
      margin-top: 1px;
      opacity: 0.85;
    }
  }

  .nav-right {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: flex-end;
    gap: 14px;
    padding-bottom: 0.8vh;

    .env-chip {
      display: inline-flex;
      align-items: center;
      gap: 5px;
      font-size: 12px;
      color: #e0eeff;
      background: rgba(6, 72, 156, 0.3);
      border: 1px solid rgba(83, 157, 255, 0.3);
      padding: 3px 9px;
      border-radius: 4px;

      .icon {
        font-size: 13px;
      }

      .val {
        font-family: monospace;
      }
    }

    .clock-chip {
      display: flex;
      flex-direction: column;
      align-items: flex-end;

      .time {
        font-size: 15px;
        font-weight: bold;
        color: #ffffff;
        font-family: monospace;
        letter-spacing: 0.5px;
      }

      .date {
        font-size: 10px;
        color: #abcfff;
      }
    }
  }
}
</style>
