<!-- 
  React Bits - Particles Background (adapted from reactbits.dev)
  Vanilla JS Canvas: floating particles with connecting lines + mouse interaction
-->
<template>
  <div class="particles-wrap">
    <canvas ref="canvasRef"></canvas>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const props = defineProps({
  count: { type: Number, default: 55 },
  color: { type: String, default: '#059669' },
  speed: { type: Number, default: 0.5 },
  maxDist: { type: Number, default: 120 }
})

const canvasRef = ref(null)
let raf = null
let particles = []
const mouse = { x: null, y: null }

class P {
  constructor(w, h) {
    this.x = Math.random() * w
    this.y = Math.random() * h
    this.vx = (Math.random() - 0.5) * props.speed
    this.vy = (Math.random() - 0.5) * props.speed
    this.r = Math.random() * 1.8 + 0.8
    this.alpha = Math.random() * 0.5 + 0.3
  }
  update(w, h) {
    this.x += this.vx
    this.y += this.vy
    if (this.x < 0 || this.x > w) this.vx *= -1
    if (this.y < 0 || this.y > h) this.vy *= -1
  }
  draw(ctx, color) {
    ctx.save()
    ctx.globalAlpha = this.alpha
    ctx.fillStyle = color
    ctx.beginPath()
    ctx.arc(this.x, this.y, this.r, 0, Math.PI * 2)
    ctx.fill()
    ctx.restore()
  }
}

onMounted(() => {
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  let W, H

  const resize = () => {
    W = canvas.width = canvas.parentElement.offsetWidth
    H = canvas.height = canvas.parentElement.offsetHeight
    particles = Array.from({ length: props.count }, () => new P(W, H))
  }

  const onMove = (e) => {
    const r = canvas.getBoundingClientRect()
    mouse.x = e.clientX - r.left
    mouse.y = e.clientY - r.top
  }
  const onLeave = () => { mouse.x = null; mouse.y = null }

  resize()
  window.addEventListener('resize', resize)
  window.addEventListener('mousemove', onMove)

  const hexToRgb = (hex) => {
    const r = parseInt(hex.slice(1, 3), 16)
    const g = parseInt(hex.slice(3, 5), 16)
    const b = parseInt(hex.slice(5, 7), 16)
    return `${r},${g},${b}`
  }
  const rgb = hexToRgb(props.color)

  const draw = () => {
    ctx.clearRect(0, 0, W, H)
    particles.forEach((p, i) => {
      p.update(W, H)
      p.draw(ctx, props.color)
      for (let j = i + 1; j < particles.length; j++) {
        const q = particles[j]
        const d = Math.hypot(p.x - q.x, p.y - q.y)
        if (d < props.maxDist) {
          const a = (1 - d / props.maxDist) * 0.25
          ctx.save()
          ctx.globalAlpha = a
          ctx.strokeStyle = `rgba(${rgb},1)`
          ctx.lineWidth = 0.8
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(q.x, q.y)
          ctx.stroke()
          ctx.restore()
        }
      }
      if (mouse.x !== null) {
        const d = Math.hypot(p.x - mouse.x, p.y - mouse.y)
        if (d < 100) {
          ctx.save()
          ctx.globalAlpha = 0.35
          ctx.strokeStyle = `rgba(${rgb},1)`
          ctx.lineWidth = 0.6
          ctx.beginPath()
          ctx.moveTo(p.x, p.y)
          ctx.lineTo(mouse.x, mouse.y)
          ctx.stroke()
          ctx.restore()
        }
      }
    })
    raf = requestAnimationFrame(draw)
  }
  draw()

  onUnmounted(() => {
    window.removeEventListener('resize', resize)
    window.removeEventListener('mousemove', onMove)
    cancelAnimationFrame(raf)
  })
})
</script>

<style scoped>
.particles-wrap {
  position: absolute;
  inset: 0;
  pointer-events: none;
  overflow: hidden;
}
canvas {
  display: block;
  width: 100%;
  height: 100%;
}
</style>
