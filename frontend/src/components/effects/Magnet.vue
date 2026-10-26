<!-- 
  React Bits - Magnet Component (adapted 1:1 from reactbits.dev)
  Attracts and pulls element towards mouse within magnetic radius
-->
<template>
  <div
    ref="refEl"
    class="magnet-wrapper"
    :class="className"
    @mousemove="handleMouseMove"
    @mouseleave="handleMouseLeave"
    :style="{
      transform: `translate3d(${position.x}px, ${position.y}px, 0)`,
      transition: isActive ? activeTransition : inactiveTransition
    }"
  >
    <slot />
  </div>
</template>

<script setup>
import { ref } from 'vue'

const props = defineProps({
  padding: {
    type: Number,
    default: 80
  },
  disabled: {
    type: Boolean,
    default: false
  },
  magnetStrength: {
    type: Number,
    default: 2.5
  },
  activeTransition: {
    type: String,
    default: 'transform 0.15s cubic-bezier(0.25, 1, 0.5, 1)'
  },
  inactiveTransition: {
    type: String,
    default: 'transform 0.5s cubic-bezier(0.25, 1, 0.5, 1)'
  },
  className: {
    type: String,
    default: ''
  }
})

const position = ref({ x: 0, y: 0 })
const isActive = ref(false)
const refEl = ref(null)

const handleMouseMove = (e) => {
  if (props.disabled || !refEl.value) return

  const { clientX, clientY } = e
  const { left, top, width, height } = refEl.value.getBoundingClientRect()

  const centerX = left + width / 2
  const centerY = top + height / 2

  const distanceX = clientX - centerX
  const distanceY = clientY - centerY

  if (
    Math.abs(distanceX) < width / 2 + props.padding &&
    Math.abs(distanceY) < height / 2 + props.padding
  ) {
    isActive.value = true
    position.value = {
      x: distanceX / props.magnetStrength,
      y: distanceY / props.magnetStrength
    }
  } else {
    isActive.value = false
    position.value = { x: 0, y: 0 }
  }
}

const handleMouseLeave = () => {
  isActive.value = false
  position.value = { x: 0, y: 0 }
}
</script>

<style scoped>
.magnet-wrapper {
  display: inline-flex;
  will-change: transform;
}
</style>
