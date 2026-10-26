<!--
  Magic UI · Number Ticker
  https://magicui.design/docs/components/number-ticker
  Source: shadcn registry item `@magicui/number-ticker` (registry/magicui/number-ticker.tsx)

  Vue 3 port — same spring (stiffness 100 / damping 60), same in-view-once trigger,
  same `Intl.NumberFormat` formatting. React's `useSpring` + `useMotionValue` map to
  motion's framework-agnostic `animate()` with `onUpdate`.
-->
<template>
  <span ref="rootEl" class="number-ticker">{{ formatted }}</span>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { animate } from 'motion'

const props = defineProps({
  value: { type: Number, required: true },
  startValue: { type: Number, default: 0 },
  direction: { type: String, default: 'up' }, // 'up' | 'down'
  delay: { type: Number, default: 0 },
  decimalPlaces: { type: Number, default: 0 },
})

const rootEl = ref(null)
const target = computed(() => (props.direction === 'down' ? props.startValue : props.value))
const current = ref(props.direction === 'down' ? props.value : props.startValue)

const formatter = computed(
  () =>
    new Intl.NumberFormat('en-US', {
      minimumFractionDigits: props.decimalPlaces,
      maximumFractionDigits: props.decimalPlaces,
    }),
)

const formatted = computed(() => formatter.value.format(Number(current.value.toFixed(props.decimalPlaces))))

let controls = null
let timer = null
let observer = null
let started = false

function play(from) {
  controls?.stop()
  controls = animate(from, target.value, {
    type: 'spring',
    stiffness: 100,
    damping: 60,
    onUpdate: (latest) => {
      current.value = latest
    },
  })
}

onMounted(() => {
  observer = new IntersectionObserver(
    (entries) => {
      if (!entries[0]?.isIntersecting || started) return
      started = true
      observer.disconnect()
      if (props.delay) {
        timer = setTimeout(() => play(current.value), props.delay * 1000)
      } else {
        play(current.value)
      }
    },
    { rootMargin: '0px' },
  )
  if (rootEl.value) observer.observe(rootEl.value)
})

// keep live values (e.g. sensor readings) animating instead of jumping
watch(target, () => {
  if (started) play(current.value)
})

onBeforeUnmount(() => {
  controls?.stop()
  observer?.disconnect()
  if (timer) clearTimeout(timer)
})
</script>

<style scoped>
.number-ticker {
  display: inline-block;
  font-variant-numeric: tabular-nums;
}
</style>
