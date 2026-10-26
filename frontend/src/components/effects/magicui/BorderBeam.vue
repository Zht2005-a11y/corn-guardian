<!--
  Magic UI · Border Beam
  https://magicui.design/docs/components/border-beam
  Source: shadcn registry item `@magicui/border-beam` (registry/magicui/border-beam.tsx)

  Vue 3 port — the beam rides the border via `offset-path: rect(...)` + `offset-distance`,
  exactly like the original. React used motion for the tween; here the same
  offsetDistance range is expressed with the `border-beam` keyframes
  (registered in `@/assets/style/magicui-effects.css`).
-->
<template>
  <div class="border-beam" :style="{ '--border-beam-width': `${borderWidth}px` }" aria-hidden="true">
    <div
      class="border-beam__beam"
      :style="{
        '--beam-size': `${size}px`,
        '--color-from': colorFrom,
        '--color-to': colorTo,
        '--duration': `${duration}s`,
        '--delay': `${delay}`,
        '--beam-from': `${reverse ? 100 - initialOffset : initialOffset}%`,
        '--beam-to': `${reverse ? -initialOffset : 100 + initialOffset}%`,
        width: `${size}px`,
        offsetPath: `rect(0 auto auto 0 round ${size}px)`,
      }"
    />
  </div>
</template>

<script setup>
defineProps({
  /** Size of the border beam */
  size: { type: Number, default: 50 },
  /** Duration of the border beam */
  duration: { type: Number, default: 6 },
  /** Delay of the border beam */
  delay: { type: Number, default: 0 },
  colorFrom: { type: String, default: '#ffaa40' },
  colorTo: { type: String, default: '#9c40ff' },
  reverse: { type: Boolean, default: false },
  /** Initial offset position (0-100) */
  initialOffset: { type: Number, default: 0 },
  borderWidth: { type: Number, default: 1 },
})
</script>

<style scoped>
.border-beam {
  pointer-events: none;
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: var(--border-beam-width, 1px) solid transparent;
  -webkit-mask:
    linear-gradient(transparent, transparent),
    linear-gradient(#000, #000);
  mask:
    linear-gradient(transparent, transparent),
    linear-gradient(#000, #000);
  -webkit-mask-clip: padding-box, border-box;
  mask-clip: padding-box, border-box;
  -webkit-mask-composite: source-in;
  mask-composite: intersect;
}

.border-beam__beam {
  position: absolute;
  aspect-ratio: 1;
  background-image: linear-gradient(to left, var(--color-from), var(--color-to), transparent);
  animation: border-beam var(--duration) linear infinite;
  animation-delay: calc(var(--delay) * -1s);
  will-change: offset-distance;
}

@media (prefers-reduced-motion: reduce) {
  .border-beam__beam {
    animation: none;
  }
}
</style>
