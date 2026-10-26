<!-- 
  React Bits - ShinyText Component (adapted 1:1 from reactbits.dev)
  Text with metallic/crystal light shimmer sweep
-->
<template>
  <span
    class="shiny-text"
    :class="{ 'animate-shine': !disabled, [className]: !!className }"
    :style="{
      '--shine-speed': `${speed}s`,
      '--shine-color': shimmerColor,
      '--base-color': baseColor
    }"
  >
    <slot>{{ text }}</slot>
  </span>
</template>

<script setup>
defineProps({
  text: {
    type: String,
    default: ''
  },
  disabled: {
    type: Boolean,
    default: false
  },
  speed: {
    type: Number,
    default: 3
  },
  baseColor: {
    type: String,
    default: '#0f172a'
  },
  shimmerColor: {
    type: String,
    default: '#10b981'
  },
  className: {
    type: String,
    default: ''
  }
})
</script>

<style scoped>
.shiny-text {
  display: inline-block;
  background-image: linear-gradient(
    120deg,
    var(--base-color) 35%,
    var(--shine-color) 50%,
    var(--base-color) 65%
  );
  background-size: 200% 100%;
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  color: transparent;
}

.animate-shine {
  animation: shine var(--shine-speed) linear infinite;
}

@keyframes shine {
  0% {
    background-position: 120% 0;
  }
  100% {
    background-position: -120% 0;
  }
}
</style>
