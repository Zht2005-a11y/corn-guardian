<!--
  Magic UI · Magic Card
  https://magicui.design/docs/components/magic-card
  Source: shadcn registry item `@magicui/magic-card` (registry/magicui/magic-card.tsx)

  Vue 3 port — props, markup and CSS are kept 1:1 with the original:
    · border ring   -> linear-gradient(bg) padding-box + radial-gradient(from,to,border) border-box
    · spotlight     -> radial-gradient(gradientColor, transparent) following the pointer
    · content       -> stacked above both layers
  The React `motion` motion-values are replaced by a reactive pointer position
  (gradient mode in the original is not spring-smoothed either, so behaviour matches).
-->
<template>
  <div
    class="magic-card"
    :style="rootStyle"
    @pointermove="handlePointerMove"
    @pointerenter="hovering = true"
    @pointerleave="hovering = false"
  >
    <div class="magic-card__backdrop" :style="{ background }" aria-hidden="true" />

    <div
      class="magic-card__spotlight"
      aria-hidden="true"
      :style="{
        background: `radial-gradient(${gradientSize}px circle at ${pos.x}px ${pos.y}px, ${gradientColor}, transparent 100%)`,
        opacity: hovering ? gradientOpacity : 0,
      }"
    />

    <div class="magic-card__content">
      <slot />
    </div>

    <!-- Vue-only extension: layer another Magic UI effect (ShineBorder / BorderBeam)
         on top of the card without nesting wrappers. -->
    <slot name="overlay" />
  </div>
</template>

<script setup>
import { computed, reactive, ref } from 'vue'

const props = defineProps({
  /** Size of the spotlight in px */
  gradientSize: { type: Number, default: 200 },
  /** Fill of the spotlight (alpha handled by gradientOpacity) */
  gradientColor: { type: String, default: '#262626' },
  /** Max opacity of the spotlight while hovering */
  gradientOpacity: { type: Number, default: 0.8 },
  /** Border gradient, start / end color */
  gradientFrom: { type: String, default: '#9E7AFF' },
  gradientTo: { type: String, default: '#FE8BBB' },
  /** Border color the gradient fades into */
  borderColor: { type: String, default: '#e5e7eb' },
  /** Card surface (any CSS background shorthand is accepted) */
  background: { type: String, default: '#ffffff' },
})

const hovering = ref(false)
const pos = reactive({ x: -props.gradientSize, y: -props.gradientSize })

const rootStyle = computed(() => ({
  background: `linear-gradient(${props.background} 0 0) padding-box, radial-gradient(${props.gradientSize}px circle at ${pos.x}px ${pos.y}px, ${props.gradientFrom}, ${props.gradientTo}, ${props.borderColor} 100%) border-box`,
}))

function handlePointerMove(event) {
  const rect = event.currentTarget.getBoundingClientRect()
  pos.x = event.clientX - rect.left
  pos.y = event.clientY - rect.top
}
</script>

<style scoped>
.magic-card {
  position: relative;
  isolation: isolate;
  overflow: hidden;
  border: 1px solid transparent;
  box-sizing: border-box;
}

.magic-card__backdrop {
  position: absolute;
  inset: 1px;
  z-index: 1;
  border-radius: inherit;
  pointer-events: none;
}

.magic-card__spotlight {
  position: absolute;
  inset: 1px;
  z-index: 2;
  border-radius: inherit;
  pointer-events: none;
  transition: opacity 0.3s ease;
}

.magic-card__content {
  position: relative;
  z-index: 3;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}
</style>
