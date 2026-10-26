<!-- 
  React Bits - DecryptedText Component (adapted 1:1 from reactbits.dev)
  Hacker/Sci-Fi glyph shuffling animation until original text settles
-->
<template>
  <span
    class="decrypted-text-wrap"
    :class="parentClassName"
    @mouseenter="handleMouseEnter"
  >
    <span
      class="decrypted-text"
      :class="[className, { 'is-scrambling': !isRevealed, [encryptedClassName]: !isRevealed }]"
    >
      {{ displayText }}
    </span>
  </span>
</template>

<script setup>
import { ref, watch, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  text: {
    type: String,
    required: true
  },
  speed: {
    type: Number,
    default: 40
  },
  maxIterations: {
    type: Number,
    default: 12
  },
  revealDirection: {
    type: String,
    default: 'start' // 'start' | 'end' | 'center'
  },
  characters: {
    type: String,
    default: '01ABCDEFXYZ#@*&!%?'
  },
  animateOn: {
    type: String,
    default: 'hover' // 'view' | 'hover' | 'trigger'
  },
  className: {
    type: String,
    default: ''
  },
  parentClassName: {
    type: String,
    default: ''
  },
  encryptedClassName: {
    type: String,
    default: ''
  }
})

const displayText = ref(props.text)
const isRevealed = ref(true)
let interval = null

const startScramble = () => {
  if (interval) clearInterval(interval)
  isRevealed.value = false
  let currentIteration = 0
  const totalLength = props.text.length

  interval = setInterval(() => {
    currentIteration++
    const progress = currentIteration / props.maxIterations

    displayText.value = props.text
      .split('')
      .map((char, index) => {
        if (char === ' ') return ' '

        let revealCondition = false
        if (props.revealDirection === 'start') {
          revealCondition = index / totalLength < progress
        } else if (props.revealDirection === 'end') {
          revealCondition = index / totalLength > 1 - progress
        } else if (props.revealDirection === 'center') {
          const center = totalLength / 2
          revealCondition = Math.abs(index - center) / center > 1 - progress
        }

        if (revealCondition || currentIteration >= props.maxIterations) {
          return char
        }

        return props.characters[Math.floor(Math.random() * props.characters.length)]
      })
      .join('')

    if (currentIteration >= props.maxIterations) {
      clearInterval(interval)
      displayText.value = props.text
      isRevealed.value = true
    }
  }, props.speed)
}

const handleMouseEnter = () => {
  if (props.animateOn === 'hover') {
    startScramble()
  }
}

watch(() => props.text, () => {
  displayText.value = props.text
  startScramble()
})

onMounted(() => {
  if (props.animateOn === 'view') {
    startScramble()
  }
})

onUnmounted(() => {
  if (interval) clearInterval(interval)
})

defineExpose({
  trigger: startScramble
})
</script>

<style scoped>
.decrypted-text-wrap {
  display: inline-block;
  white-space: pre-wrap;
  cursor: default;
}

.decrypted-text {
  font-family: inherit;
  transition: color 0.15s ease;
}

.is-scrambling {
  font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace;
}
</style>
