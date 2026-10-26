<template>
  <div class="uiverse-loader-container">
    <!-- Uiverse.io Radar Pulse Scanner adapted to repository deep blue palette -->
    <div class="loader">
      <div class="radar">
        <div class="sweep"></div>
      </div>
      <div class="ring ring-1"></div>
      <div class="ring ring-2"></div>
      <div class="core-dot"></div>
    </div>
    <div v-if="text" class="loading-text">{{ text }}</div>
  </div>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: '模型大田特征融合推理中...'
  }
})
</script>

<style lang="scss" scoped>
.uiverse-loader-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px;
}

.loader {
  position: relative;
  width: 72px;
  height: 72px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.radar {
  position: absolute;
  width: 100%;
  height: 100%;
  border-radius: 50%;
  border: 1.5px solid rgba(83, 157, 255, 0.4);
  box-shadow: 0 0 15px rgba(0, 77, 207, 0.3);
  overflow: hidden;
}

.sweep {
  position: absolute;
  top: 50%;
  left: 50%;
  width: 100%;
  height: 100%;
  transform-origin: 0 0;
  background: conic-gradient(from 0deg, rgba(83, 157, 255, 0.6) 0deg, rgba(83, 157, 255, 0) 60deg);
  animation: sweep-spin 2s linear infinite;
}

.ring {
  position: absolute;
  border-radius: 50%;
  border: 1px dashed rgba(171, 207, 255, 0.35);
  box-sizing: border-box;
}

.ring-1 {
  width: 52px;
  height: 52px;
  animation: ring-pulse 2s ease-in-out infinite;
}

.ring-2 {
  width: 32px;
  height: 32px;
  border: 1px solid rgba(83, 157, 255, 0.4);
}

.core-dot {
  position: absolute;
  width: 8px;
  height: 8px;
  background: #539dff;
  border-radius: 50%;
  box-shadow: 0 0 8px #539dff;
}

.loading-text {
  font-size: 12px;
  color: #abcfff;
  letter-spacing: 0.8px;
}

@keyframes sweep-spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

@keyframes ring-pulse {
  0%, 100% { transform: scale(0.95); opacity: 0.6; }
  50% { transform: scale(1.05); opacity: 1; }
}
</style>
