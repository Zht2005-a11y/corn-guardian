<!-- 
  React Bits - Aurora Soft Glow (adapted from reactbits.dev)
  Soft ambient animated mesh gradient banner
-->
<template>
  <div class="aurora-container" :style="containerStyle">
    <div class="aurora-wave wave-1"></div>
    <div class="aurora-wave wave-2"></div>
    <div class="aurora-wave wave-3"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  colorStops: {
    type: Array,
    default: () => ['#ecfdf5', '#10b981', '#064e3b']
  },
  speed: {
    type: Number,
    default: 1.2
  },
  opacity: {
    type: Number,
    default: 0.18
  }
})

const containerStyle = computed(() => ({
  '--c1': props.colorStops[0],
  '--c2': props.colorStops[1],
  '--c3': props.colorStops[2],
  '--anim-speed': `${12 / props.speed}s`,
  '--aurora-opacity': props.opacity
}))
</script>

<style scoped>
.aurora-container {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
  opacity: var(--aurora-opacity);
  border-radius: inherit;
  z-index: 0;
}

.aurora-wave {
  position: absolute;
  width: 180%;
  height: 180%;
  top: -40%;
  left: -40%;
  filter: blur(40px);
  animation: aurora-move var(--anim-speed) ease-in-out infinite alternate;
}

.wave-1 {
  background: radial-gradient(circle at 20% 30%, var(--c2) 0%, transparent 60%);
  animation-duration: var(--anim-speed);
}

.wave-2 {
  background: radial-gradient(circle at 75% 65%, var(--c3) 0%, transparent 55%);
  animation-duration: calc(var(--anim-speed) * 1.35);
  animation-direction: alternate-reverse;
}

.wave-3 {
  background: radial-gradient(circle at 50% 50%, var(--c1) 0%, transparent 50%);
  animation-duration: calc(var(--anim-speed) * 0.85);
}

@keyframes aurora-move {
  0% {
    transform: rotate(0deg) scale(1) translate(0px, 0px);
  }
  50% {
    transform: rotate(90deg) scale(1.15) translate(30px, 15px);
  }
  100% {
    transform: rotate(180deg) scale(1.05) translate(-20px, 20px);
  }
}
</style>
