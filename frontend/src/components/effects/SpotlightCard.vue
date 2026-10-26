<!-- 
  React Bits - SpotlightCard Component (adapted 1:1 from reactbits.dev)
  Radial gradient spotlight follower on hover and focus
-->
<template>
  <div
    ref="divRef"
    class="spotlight-card"
    :class="className"
    @mousemove="handleMouseMove"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
    @focus="handleFocus"
    @blur="handleBlur"
  >
    <div
      class="spotlight-layer"
      :style="{
        opacity,
        background: `radial-gradient(${radius}px circle at ${position.x}px ${position.y}px, ${spotlightColor}, transparent 65%)`
      }"
    ></div>
    <div class="spotlight-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  spotlightColor: {
    type: String,
    default: 'rgba(5, 150, 105, 0.08)' // Clean emerald light tone
  },
  radius: {
    type: Number,
    default: 480
  },
  className: {
    type: String,
    default: ''
  }
})

const divRef = ref(null)
const isFocused = ref(false)
const position = ref({ x: 0, y: 0 })
const opacity = ref(0)

const handleMouseMove = (e) => {
  if (!divRef.value || isFocused.value) return
  const rect = divRef.value.getBoundingClientRect()
  position.value = {
    x: e.clientX - rect.left,
    y: e.clientY - rect.top
  }
}

const handleMouseEnter = () => {
  opacity.value = 1
}

const handleMouseLeave = () => {
  opacity.value = 0
}

const handleFocus = () => {
  isFocused.value = true
  opacity.value = 1
}

const handleBlur = () => {
  isFocused.value = false
  opacity.value = 0
}
</script>

<style scoped>
.spotlight-card {
  position: relative;
  border-radius: 16px;
  border: 1px solid var(--spotlight-border, rgba(52, 211, 153, 0.18));
  background: var(--spotlight-bg, rgba(13, 24, 19, 0.78));
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  overflow: hidden;
  box-shadow: var(--spotlight-shadow, 0 10px 30px -5px rgba(0, 0, 0, 0.5));
  transition: border-color 0.25s, box-shadow 0.25s, transform 0.2s;
}

.spotlight-card:hover {
  border-color: var(--spotlight-hover-border, rgba(52, 211, 153, 0.35));
  box-shadow: 0 12px 36px -4px rgba(0, 0, 0, 0.6), 0 0 20px rgba(16, 185, 129, 0.08);
}

.spotlight-layer {
  pointer-events: none;
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  transition: opacity 0.3s ease;
  z-index: 1;
}

.spotlight-content {
  position: relative;
  z-index: 2;
  height: 100%;
  display: flex;
  flex-direction: column;
}
</style>
