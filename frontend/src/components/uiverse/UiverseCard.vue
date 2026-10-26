<template>
  <!-- Uiverse.io Component: Glassmorphism Cyber Card -->
  <div class="uiverse-card" :class="[variant, { hoverable: isHoverable }]">
    <div v-if="title || $slots.header" class="card-header">
      <div class="header-left">
        <span class="header-indicator"></span>
        <span class="header-title">{{ title }}</span>
      </div>
      <div class="header-right">
        <slot name="header-extra" />
      </div>
    </div>
    <div class="card-body">
      <slot />
    </div>
  </div>
</template>

<script setup>
defineProps({
  title: {
    type: String,
    default: ''
  },
  variant: {
    type: String,
    default: 'default' // 'default' | 'glow-border' | 'accent'
  },
  isHoverable: {
    type: Boolean,
    default: true
  }
})
</script>

<style scoped>
/*
 * Uiverse.io Glassmorphism Card
 * Features cyber-styled frosted glass, border lighting, and corner indicators
 */
.uiverse-card {
  position: relative;
  background: rgba(10, 26, 47, 0.65);
  backdrop-filter: blur(12px);
  -webkit-backdrop-filter: blur(12px);
  border: 1px solid rgba(0, 180, 255, 0.25);
  border-radius: 10px;
  padding: 12px;
  box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.37);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.uiverse-card.hoverable:hover {
  border-color: rgba(0, 255, 170, 0.45);
  box-shadow: 0 12px 36px 0 rgba(0, 255, 170, 0.12), inset 0 0 16px rgba(0, 255, 170, 0.05);
  transform: translateY(-2px);
}

.card-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-bottom: 8px;
  margin-bottom: 8px;
  border-bottom: 1px solid rgba(0, 180, 255, 0.15);
}

.header-left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.header-indicator {
  width: 4px;
  height: 14px;
  background: linear-gradient(180deg, #00ffaa, #00b4d8);
  border-radius: 2px;
  box-shadow: 0 0 8px #00ffaa;
}

.header-title {
  font-size: 14px;
  font-weight: 600;
  color: #e2f1ff;
  letter-spacing: 0.5px;
  text-shadow: 0 0 6px rgba(0, 180, 255, 0.4);
}

.card-body {
  flex: 1;
  width: 100%;
  height: 100%;
  position: relative;
  overflow: hidden;
}

/* Variant: glow-border */
.uiverse-card.glow-border {
  border-color: rgba(0, 255, 170, 0.35);
  box-shadow: 0 0 18px rgba(0, 255, 170, 0.15);
}
</style>
