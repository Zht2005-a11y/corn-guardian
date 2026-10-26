<!-- 
  React Bits - TiltedCard Component (adapted 1:1 from reactbits.dev)
  3D perspective tilting card with cursor tracking and glare overlay
-->
<template>
  <div
    ref="cardRef"
    class="tilted-card-figure"
    @mousemove="handleMouse"
    @mouseenter="handleMouseEnter"
    @mouseleave="handleMouseLeave"
  >
    <div
      class="tilted-card-inner"
      :style="{
        transform: `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale3d(${scale}, ${scale}, ${scale})`
      }"
    >
      <slot />

      <!-- Dynamic Light Glare Overlay -->
      <div
        class="tilted-card-glare"
        :style="{
          opacity: glareOpacity,
          background: `radial-gradient(circle at ${glareX}% ${glareY}%, rgba(255, 255, 255, 0.45) 0%, rgba(255, 255, 255, 0) 70%)`
        }"
      ></div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  maxTilt: {
    type: Number,
    default: 12 // max rotation degrees
  },
  scaleOnHover: {
    type: Number,
    default: 1.015
  }
})

const cardRef = ref(null)
const rotateX = ref(0)
const rotateY = ref(0)
const scale = ref(1)
const glareOpacity = ref(0)
const glareX = ref(50)
const glareY = ref(50)

const handleMouse = (e) => {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  const offsetX = e.clientX - rect.left
  const offsetY = e.clientY - rect.top

  const width = rect.width
  const height = rect.height

  const centerX = offsetX / width - 0.5
  const centerY = offsetY / height - 0.5

  rotateX.value = centerY * -props.maxTilt
  rotateY.value = centerX * props.maxTilt

  glareX.value = (offsetX / width) * 100
  glareY.value = (offsetY / height) * 100
}

const handleMouseEnter = () => {
  scale.value = props.scaleOnHover
  glareOpacity.value = 1
}

const handleMouseLeave = () => {
  scale.value = 1
  glareOpacity.value = 0
  rotateX.value = 0
  rotateY.value = 0
  glareX.value = 50
  glareY.value = 50
}
</script>

<style scoped>
.tilted-card-figure {
  position: relative;
  perspective: 1000px;
  width: 100%;
  display: block;
}

.tilted-card-inner {
  position: relative;
  width: 100%;
  height: 100%;
  transform-style: preserve-3d;
  will-change: transform;
  border-radius: inherit;
  transition: transform 0.12s ease-out;
}

.tilted-card-glare {
  position: absolute;
  inset: 0;
  border-radius: inherit;
  pointer-events: none;
  mix-blend-mode: overlay;
  transition: opacity 0.3s ease;
  z-index: 10;
}
</style>
