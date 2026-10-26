<template>
  <button
    :class="['uiverse-btn', variant, { 'is-loading': loading }]"
    :disabled="disabled || loading"
    @click="$emit('click', $event)"
  >
    <span v-if="loading" class="spinner"></span>
    <span class="btn-text">
      <slot />
    </span>
  </button>
</template>

<script setup>
defineProps({
  variant: {
    type: String,
    default: 'primary' // 'primary' | 'secondary' | 'outline'
  },
  loading: {
    type: Boolean,
    default: false
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

defineEmits(['click'])
</script>

<style lang="scss" scoped>
/*
 * Uiverse.io Button adapted to IT-NuanxinPro/Vue3Echarts deep blue palette
 */
.uiverse-btn {
  position: relative;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 8px 22px;
  font-size: 13px;
  font-weight: bold;
  border-radius: 6px;
  cursor: pointer;
  outline: none;
  border: none;
  transition: all 0.25s ease-in-out;
  letter-spacing: 0.5px;
  user-select: none;
}

.uiverse-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

/* 主按钮: 原仓库高光蓝渐变 + 细腻微光 */
.uiverse-btn.primary {
  background: linear-gradient(180deg, #1f6fd9 0%, #004dcf 100%);
  color: #ffffff;
  border: 1px solid #539dff;
  box-shadow: 0 4px 12px rgba(0, 77, 207, 0.4), inset 0 1px 0 rgba(255, 255, 255, 0.3);

  &:hover:not(:disabled) {
    background: linear-gradient(180deg, #3283ec 0%, #0f5ee0 100%);
    box-shadow: 0 6px 16px rgba(0, 77, 207, 0.6), inset 0 1px 0 rgba(255, 255, 255, 0.5);
    transform: translateY(-1px);
  }

  &:active:not(:disabled) {
    transform: translateY(1px);
    box-shadow: 0 2px 6px rgba(0, 77, 207, 0.4);
  }
}

/* 次按钮: 优雅深蓝微光 */
.uiverse-btn.secondary {
  background: rgba(6, 72, 156, 0.35);
  color: #e0eeff;
  border: 1px solid rgba(83, 157, 255, 0.5);

  &:hover:not(:disabled) {
    background: rgba(6, 72, 156, 0.6);
    border-color: #539dff;
    color: #ffffff;
    transform: translateY(-1px);
  }
}

/* 轮廓按钮 */
.uiverse-btn.outline {
  background: transparent;
  color: #abcfff;
  border: 1px solid rgba(171, 207, 255, 0.35);

  &:hover:not(:disabled) {
    background: rgba(83, 157, 255, 0.15);
    border-color: #abcfff;
    color: #ffffff;
  }
}

/* 加载动画 */
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid transparent;
  border-top-color: currentColor;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}
</style>
