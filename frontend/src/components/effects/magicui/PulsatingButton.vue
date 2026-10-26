<!--
  Magic UI · Pulsating Button
  https://magicui.design/docs/components/pulsating-button
  Source: shadcn registry item `@magicui/pulsating-button` (registry/magicui/pulsating-button.tsx)
  Keyframes `pulse` / `pulse-ripple` are registered globally in
  `@/assets/style/magicui-effects.css` (values taken from the item's `css` field).

  Vue 3 port — `variant="pulse"` expands a box-shadow ring around the button,
  `variant="ripple"` fades one out. When `pulseColor` is omitted the button's own
  background color is sampled (same as the original), falling back to a neutral
  tint for transparent / gradient backgrounds.
-->
<template>
  <button
    ref="rootEl"
    v-bind="$attrs"
    class="pulsating-button"
    :style="{
      '--pulse-color': pulseColor || sampledColor,
      '--duration': duration,
      '--distance': distance,
    }"
  >
    <span class="pulsating-button__label"><slot /></span>
    <span
      class="pulsating-button__pulse"
      :class="variant === 'ripple' ? 'is-ripple' : 'is-pulse'"
      aria-hidden="true"
    />
  </button>
</template>

<script setup>
import { onBeforeUnmount, onMounted, ref } from 'vue'

const props = defineProps({
  pulseColor: { type: String, default: '' },
  duration: { type: String, default: '1.5s' },
  distance: { type: String, default: '8px' },
  variant: { type: String, default: 'pulse' }, // 'pulse' | 'ripple'
})

const rootEl = ref(null)
const sampledColor = ref('rgba(0, 0, 0, 0.35)')
let observer = null

function sampleBackground() {
  if (!rootEl.value) return
  const bg = getComputedStyle(rootEl.value).backgroundColor
  if (bg && bg !== 'rgba(0, 0, 0, 0)' && bg !== 'transparent') sampledColor.value = bg
}

onMounted(() => {
  if (props.pulseColor) return
  sampleBackground()
  observer = new MutationObserver(sampleBackground)
  observer.observe(rootEl.value, { attributes: true, attributeFilter: ['class', 'style'] })
})

onBeforeUnmount(() => observer?.disconnect())
</script>

<style scoped>
.pulsating-button {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
}

.pulsating-button__label {
  position: relative;
  z-index: 10;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: inherit;
  width: 100%;
}

.pulsating-button__pulse {
  pointer-events: none;
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: inherit;

  &.is-pulse {
    animation: pulse var(--duration) ease-out infinite;
  }

  &.is-ripple {
    animation: pulse-ripple var(--duration) cubic-bezier(0.16, 1, 0.3, 1) infinite;
  }
}

@media (prefers-reduced-motion: reduce) {
  .pulsating-button__pulse {
    animation: none;
  }
}
</style>
