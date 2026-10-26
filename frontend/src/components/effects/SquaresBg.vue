<!-- 
  React Bits - Squares Background Component (adapted 1:1 from reactbits.dev)
  Interactive drifting grid with hoverFillColor physics
-->
<template>
  <div class="squares-container">
    <canvas
      ref="canvasRef"
      @mousemove="handleMouseMove"
      @mouseleave="handleMouseLeave"
    ></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  direction: { type: String, default: 'diagonal' }, // 'right' | 'left' | 'up' | 'down' | 'diagonal'
  speed: { type: Number, default: 0.35 },
  squareSize: { type: Number, default: 36 },
  borderColor: { type: String, default: 'rgba(226, 232, 240, 0.7)' },
  hoverFillColor: { type: String, default: 'rgba(16, 185, 129, 0.08)' }
})

const canvasRef = ref(null)
const cursor = { x: -1000, y: -1000 }
let animationFrameId = null

onMounted(() => {
  const canvas = canvasRef.value
  if (!canvas) return
  const ctx = canvas.getContext('2d')

  let width = (canvas.width = canvas.parentElement.offsetWidth)
  let height = (canvas.height = canvas.parentElement.offsetHeight)

  const handleResize = () => {
    if (!canvas.parentElement) return
    width = canvas.width = canvas.parentElement.offsetWidth
    height = canvas.height = canvas.parentElement.offsetHeight
  }

  window.addEventListener('resize', handleResize)

  let offsetX = 0
  let offsetY = 0

  const render = () => {
    ctx.clearRect(0, 0, width, height)

    if (props.direction === 'right') offsetX = (offsetX + props.speed) % props.squareSize
    if (props.direction === 'left') offsetX = (offsetX - props.speed + props.squareSize) % props.squareSize
    if (props.direction === 'down') offsetY = (offsetY + props.speed) % props.squareSize
    if (props.direction === 'up') offsetY = (offsetY - props.speed + props.squareSize) % props.squareSize
    if (props.direction === 'diagonal') {
      offsetX = (offsetX + props.speed) % props.squareSize
      offsetY = (offsetY + props.speed) % props.squareSize
    }

    const cols = Math.ceil(width / props.squareSize) + 2
    const rows = Math.ceil(height / props.squareSize) + 2

    const startX = -props.squareSize + (offsetX % props.squareSize)
    const startY = -props.squareSize + (offsetY % props.squareSize)

    for (let i = 0; i < cols; i++) {
      for (let j = 0; j < rows; j++) {
        const x = startX + i * props.squareSize
        const y = startY + j * props.squareSize

        const isHovered =
          cursor.x >= x &&
          cursor.x < x + props.squareSize &&
          cursor.y >= y &&
          cursor.y < y + props.squareSize

        ctx.strokeStyle = props.borderColor
        ctx.lineWidth = 1
        ctx.strokeRect(x, y, props.squareSize, props.squareSize)

        if (isHovered) {
          ctx.fillStyle = props.hoverFillColor
          ctx.fillRect(x, y, props.squareSize, props.squareSize)
        }
      }
    }

    animationFrameId = requestAnimationFrame(render)
  }

  render()

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    cancelAnimationFrame(animationFrameId)
  })
})

const handleMouseMove = (e) => {
  if (!canvasRef.value) return
  const rect = canvasRef.value.getBoundingClientRect()
  cursor.x = e.clientX - rect.left
  cursor.y = e.clientY - rect.top
}

const handleMouseLeave = () => {
  cursor.x = -1000
  cursor.y = -1000
}
</script>

<style scoped>
.squares-container {
  position: absolute;
  inset: 0;
  pointer-events: auto;
  overflow: hidden;
}

canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
