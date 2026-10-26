<!--
  Magic UI · Dot Pattern
  https://magicui.design/docs/components/dot-pattern
  Source: shadcn registry item `@magicui/dot-pattern` (registry/magicui/dot-pattern.tsx)
  Glow keyframes are registered globally in `@/assets/style/magicui-effects.css`.

  Vue 3 port — same dot grid maths and the same optional per-dot glow
  (opacity .4 -> 1 -> .4, scale 1 -> 1.5 -> 1). Container size is tracked with
  a ResizeObserver instead of a window resize listener.
-->
<template>
  <svg ref="rootEl" class="dot-pattern" aria-hidden="true">
    <defs v-if="glow">
      <radialGradient :id="gradientId">
        <stop offset="0%" stop-color="currentColor" stop-opacity="1" />
        <stop offset="100%" stop-color="currentColor" stop-opacity="0" />
      </radialGradient>
    </defs>
    <circle
      v-for="dot in dots"
      :key="`${dot.x}-${dot.y}`"
      :cx="dot.x"
      :cy="dot.y"
      :r="cr"
      :fill="glow ? `url(#${gradientId})` : 'currentColor'"
      :class="{ 'dot-pattern__dot--glow': glow }"
      :style="
        glow
          ? {
              animationDuration: `${dot.duration}s`,
              animationDelay: `${dot.delay}s`,
            }
          : null
      "
    />
  </svg>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, ref, shallowRef } from 'vue'

const props = defineProps({
  /** Horizontal spacing between dots */
  width: { type: Number, default: 16 },
  /** Vertical spacing between dots */
  height: { type: Number, default: 16 },
  /** X offset of the whole pattern */
  x: { type: Number, default: 0 },
  /** Y offset of the whole pattern */
  y: { type: Number, default: 0 },
  /** X offset of each dot */
  cx: { type: Number, default: 1 },
  /** Y offset of each dot */
  cy: { type: Number, default: 1 },
  /** Radius of each dot */
  cr: { type: Number, default: 1 },
  /** Animate the dots */
  glow: { type: Boolean, default: false },
})

const rootEl = ref(null)
const size = ref({ width: 0, height: 0 })
const gradientId = `dot-pattern-${Math.random().toString(36).slice(2, 9)}`
let observer = null

const dots = shallowRef([])

const cols = computed(() => Math.ceil(size.value.width / props.width))
const rows = computed(() => Math.ceil(size.value.height / props.height))

function buildDots() {
  const total = cols.value * rows.value
  if (!Number.isFinite(total) || total <= 0) {
    dots.value = []
    return
  }
  dots.value = Array.from({ length: total }, (_, i) => {
    const col = i % cols.value
    const row = Math.floor(i / cols.value)
    return {
      x: col * props.width + props.cx + props.x,
      y: row * props.height + props.cy + props.y,
      delay: Math.random() * 5,
      duration: Math.random() * 3 + 2,
    }
  })
}

function measure() {
  if (!rootEl.value) return
  const rect = rootEl.value.getBoundingClientRect()
  size.value = { width: rect.width, height: rect.height }
  buildDots()
}

onMounted(() => {
  measure()
  observer = new ResizeObserver(measure)
  if (rootEl.value) observer.observe(rootEl.value)
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<style scoped>
.dot-pattern {
  pointer-events: none;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.dot-pattern__dot--glow {
  animation-name: dot-pattern-glow;
  animation-timing-function: ease-in-out;
  animation-iteration-count: infinite;
  transform-box: fill-box;
  transform-origin: center;
}
</style>
