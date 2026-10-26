<!--
  Magic UI · Shine Border
  https://magicui.design/docs/components/shine-border
  Source: shadcn registry item `@magicui/shine-border` (registry/magicui/shine-border.tsx)
  Keyframes `shine` are registered globally in `@/assets/style/magicui-effects.css`.

  Vue 3 port — the border ring is produced with the same padding-box / border-box
  mask pair, so it composes with whatever radius the parent already has.
-->
<template>
  <div
    class="shine-border"
    :style="{
      '--border-width': `${borderWidth}px`,
      '--duration': `${duration}s`,
      backgroundImage: `radial-gradient(transparent,transparent, ${colors},transparent,transparent)`,
    }"
    aria-hidden="true"
  />
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  /** Width of the border in pixels */
  borderWidth: { type: Number, default: 1 },
  /** Duration of one animation cycle, in seconds */
  duration: { type: Number, default: 14 },
  /** A single color or a list of colors */
  shineColor: { type: [String, Array], default: '#000000' },
})

const colors = computed(() => (Array.isArray(props.shineColor) ? props.shineColor.join(',') : props.shineColor))
</script>

<style scoped>
.shine-border {
  pointer-events: none;
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  border-radius: inherit;
  background-size: 300% 300%;
  padding: var(--border-width);
  -webkit-mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  mask:
    linear-gradient(#fff 0 0) content-box,
    linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  will-change: background-position;
  animation: shine var(--duration) infinite linear;
}

@media (prefers-reduced-motion: reduce) {
  .shine-border {
    animation: none;
  }
}
</style>
