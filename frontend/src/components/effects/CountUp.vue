<!-- 
  React Bits - CountUp Component (adapted 1:1 from reactbits.dev)
  Animated rolling numbers on update/view
-->
<template>
  <span class="count-up-number" :class="className">
    {{ displayValue }}
  </span>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'

const props = defineProps({
  to: {
    type: Number,
    required: true
  },
  from: {
    type: Number,
    default: 0
  },
  duration: {
    type: Number,
    default: 1.2 // in seconds
  },
  decimals: {
    type: Number,
    default: 1
  },
  className: {
    type: String,
    default: ''
  }
})

const displayValue = ref(props.from.toFixed(props.decimals))

const animateValue = (start, end, duration) => {
  let startTimestamp = null
  const step = (timestamp) => {
    if (!startTimestamp) startTimestamp = timestamp
    const progress = Math.min((timestamp - startTimestamp) / (duration * 1000), 1)
    // easeOutExpo
    const ease = progress === 1 ? 1 : 1 - Math.pow(2, -10 * progress)
    const current = start + (end - start) * ease
    displayValue.value = current.toFixed(props.decimals)

    if (progress < 1) {
      window.requestAnimationFrame(step)
    } else {
      displayValue.value = end.toFixed(props.decimals)
    }
  }
  window.requestAnimationFrame(step)
}

watch(() => props.to, (newVal, oldVal) => {
  animateValue(oldVal !== undefined ? oldVal : props.from, newVal, props.duration)
})

onMounted(() => {
  animateValue(props.from, props.to, props.duration)
})
</script>

<style scoped>
.count-up-number {
  font-variant-numeric: tabular-nums;
  display: inline-block;
}
</style>
