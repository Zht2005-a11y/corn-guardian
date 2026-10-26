<template>
  <div ref="containerRef" class="liquid-glass-wrapper" :style="wrapperStyle">
    <canvas v-show="!useFallback" ref="canvasRef" class="liquid-glass-canvas" />
    <div v-if="useFallback" class="liquid-glass-fallback">
      <div class="glass-orb orb-1"></div>
      <div class="glass-orb orb-2"></div>
      <div class="glass-orb orb-3"></div>
    </div>
    <div class="liquid-glass-content">
      <slot />
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'

const props = defineProps({
  tint: {
    type: Array,
    default: () => [0.05, 0.18, 0.38]
  },
  speed: {
    type: Number,
    default: 0.4
  },
  amplitude: {
    type: Number,
    default: 0.22
  },
  detail: {
    type: Number,
    default: 3.5
  },
  roughness: {
    type: Number,
    default: 0.1
  },
  interactive: {
    type: Boolean,
    default: true
  },
  lightMode: {
    type: Boolean,
    default: false
  }
})

const containerRef = ref(null)
const canvasRef = ref(null)
const useFallback = ref(false)
let gl = null
let animationFrameId = null
let destroyed = false

const wrapperStyle = computed(() => ({
  position: 'relative',
  width: '100%',
  height: '100%',
  overflow: 'hidden'
}))

// Shaders adapted directly from React Bits (DavidHDev/react-bits) LiquidChrome component
const VERTEX = `#version 300 es
const vec2 corners[3] = vec2[3](vec2(-1.0, -1.0), vec2(3.0, -1.0), vec2(-1.0, 3.0));
void main() {
  gl_Position = vec4(corners[gl_VertexID], 0.0, 1.0);
}`

const SIM = `#version 300 es
precision highp float;
uniform sampler2D uState;
uniform vec2 uSize;
uniform vec4 uStroke;
uniform vec2 uImpulse;
out vec4 fragColor;

float segment(vec2 p, vec2 a, vec2 b) {
  vec2 ab = b - a;
  float t = clamp(dot(p - a, ab) / max(dot(ab, ab), 1e-4), 0.0, 1.0);
  return length(p - a - ab * t);
}

void main() {
  vec2 texel = 1.0 / uSize;
  vec2 uv = gl_FragCoord.xy * texel;
  vec2 state = texture(uState, uv).rg;
  vec2 around =
    texture(uState, uv - vec2(texel.x, 0.0)).rg +
    texture(uState, uv + vec2(texel.x, 0.0)).rg +
    texture(uState, uv - vec2(0.0, texel.y)).rg +
    texture(uState, uv + vec2(0.0, texel.y)).rg -
    4.0 * state;
  float next = state.r + (state.r - state.g) * 0.982 + 0.3 * around.r + 0.08 * (around.r - around.g);
  next *= 0.998;
  if (uImpulse.x != 0.0) {
    float d = segment(gl_FragCoord.xy, uStroke.xy, uStroke.zw) / uImpulse.y;
    next += uImpulse.x * exp(-d * d);
  }
  fragColor = vec4(next, state.r, 0.0, 1.0);
}`

const SLOPE = `#version 300 es
precision highp float;
uniform sampler2D uState;
uniform vec2 uSize;
out vec4 fragColor;

void main() {
  vec2 texel = 1.0 / uSize;
  vec2 uv = gl_FragCoord.xy * texel;
  float left = texture(uState, uv - vec2(texel.x, 0.0)).r;
  float right = texture(uState, uv + vec2(texel.x, 0.0)).r;
  float down = texture(uState, uv - vec2(0.0, texel.y)).r;
  float up = texture(uState, uv + vec2(0.0, texel.y)).r;
  fragColor = vec4((right - left) * 0.5, (up - down) * 0.5, 0.0, 1.0);
}`

const CHROME = `#version 300 es
precision highp float;
uniform vec2 uResolution;
uniform float uUnit;
uniform float uTime;
uniform float uAmplitude;
uniform vec2 uFrequency;
uniform float uDetail;
uniform float uSharpness;
uniform float uDepth;
uniform float uPresence;
uniform vec3 uTint;
uniform vec2 uShift;
uniform float uRoughness;
uniform float uExposure;
uniform float uLight;
uniform sampler2D uSlope;
uniform vec2 uSlopeSize;
uniform float uRipple;
out vec4 fragColor;

vec2 slopeAt(vec2 uv) {
  vec2 st = uv * uSlopeSize - 0.5;
  vec2 i = floor(st);
  vec2 f = st - i;
  vec2 f2 = f * f;
  vec2 f3 = f2 * f;
  vec2 w0 = (-f3 + 3.0 * f2 - 3.0 * f + 1.0) / 6.0;
  vec2 w1 = (3.0 * f3 - 6.0 * f2 + 4.0) / 6.0;
  vec2 w2 = (-3.0 * f3 + 3.0 * f2 + 3.0 * f + 1.0) / 6.0;
  vec2 w3 = f3 / 6.0;
  vec2 g0 = w0 + w1;
  vec2 g1 = w2 + w3;
  vec2 h0 = (i - 0.5 + w1 / g0) / uSlopeSize;
  vec2 h1 = (i + 1.5 + w3 / g1) / uSlopeSize;
  vec2 a = texture(uSlope, vec2(h0.x, h0.y)).rg;
  vec2 b = texture(uSlope, vec2(h1.x, h0.y)).rg;
  vec2 c = texture(uSlope, vec2(h0.x, h1.y)).rg;
  vec2 d = texture(uSlope, vec2(h1.x, h1.y)).rg;
  return g0.y * (g0.x * a + g1.x * b) + g1.y * (g0.x * c + g1.x * d);
}

float lamp(vec2 p, vec2 center, vec2 size, float soft) {
  vec2 grown = size + soft;
  vec2 q = (p - center) / grown;
  q *= q;
  float d = sqrt(sqrt(dot(q, q)));
  float edge = soft / min(grown.x, grown.y);
  float shape = (1.0 - smoothstep(1.0 - edge, 1.0 + edge, d)) * (1.0 - 0.45 * d * d);
  return shape * size.x * size.y / (grown.x * grown.y);
}

vec3 studio(vec3 r, float blur) {
  vec2 p = r.xy / max(r.z + 1.0, 0.05);
  p += uShift * smoothstep(0.3, 1.0, length(p));
  float radius = length(p);
  float soft = 0.008 + blur;
  vec2 dir = p / max(radius, 1e-3);
  float key = lamp(p, vec2(-0.25, 0.42), vec2(0.3, 0.12), soft);
  float side = lamp(p, vec2(0.48, 0.12), vec2(0.06, 0.3), soft);
  float ground = lamp(p, vec2(-0.1, -0.55), vec2(0.45, 0.06), soft);
  float rise = smoothstep(-1.0, 1.0, dir.y);
  if (uLight > 0.5) {
    float edge = 0.008 + blur * 0.8;
    float lobe = smoothstep(0.15, 0.85, 0.5 + 0.5 * sin(atan(dir.y, dir.x) * 2.0 + 0.9));
    float tone = mix(2.4, 0.95, smoothstep(0.5 - edge, 1.0 + edge, radius));
    tone = mix(tone, 0.02, smoothstep(0.98 - edge, 1.12 + edge, radius));
    tone = mix(tone, mix(0.03, 0.3, lobe) * (0.8 + 0.4 * rise), smoothstep(1.15 - edge, 1.3 + edge, radius));
    float width = 0.035 + edge;
    tone += 2.4 * exp(-pow((radius - 1.4) / width, 2.0)) * min(1.0, 0.06 / width) * (0.6 + 0.4 * rise);
    return vec3(tone) * (1.0 - 0.5 * side) * (1.0 - 0.3 * ground) + 0.8 * key;
  }
  float width = 0.015 + soft * 2.0;
  float rim = exp(-abs(radius - 1.0) / width) * 0.031 / width * (0.8 + smoothstep(-0.5, 0.8, p.y));
  float band = 1.0 - 0.95 * smoothstep(1.04 - soft, 1.12 + soft, radius);
  float wall = smoothstep(1.25, 1.55, radius) * (0.6 + 0.4 * rise);
  float streak = smoothstep(0.2, 0.8, 0.5 + 0.5 * sin(atan(dir.y, dir.x) * 3.0 + 0.6));
  vec3 color = vec3(0.004, 0.004, 0.005) + 0.02 * smoothstep(-0.4, 0.6, p.y);
  color += vec3(1.0, 0.97, 0.94) * key * 4.0 + vec3(0.9, 0.95, 1.0) * side * 3.0 + ground * 1.2;
  color += vec3(1.0, 0.98, 0.95) * rim;
  color *= band;
  return color + vec3(mix(0.45, 1.8, streak)) * wall;
}

vec3 shade(vec2 slope, vec3 v, float blur, vec3 f0) {
  float steep = length(slope);
  slope *= 3.0 * tanh(steep / 3.0) / max(steep, 1e-6);
  vec3 n = normalize(vec3(-slope, 1.0));
  vec3 r = reflect(v, n);
  float facing = clamp(dot(n, -v), 0.0, 1.0);
  return studio(r, blur) * (f0 + (1.0 - f0) * pow(1.0 - facing, 5.0));
}

vec3 aces(vec3 x) {
  return clamp((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0);
}

void main() {
  vec2 frag = gl_FragCoord.xy;
  vec2 uv = (2.0 * frag - uResolution) / uUnit;
  vec2 p = uv;
  vec2 rowX = vec2(1.0, 0.0);
  vec2 rowY = vec2(0.0, 1.0);
  float amplitude = uAmplitude * uPresence;
  for (float i = 1.0; i < 9.0; i++) {
    if (i > uDetail) break;
    float a = amplitude / i;
    float soften = exp(0.3 - 0.3 * i);
    float argX = i * uFrequency.x * p.y + uTime;
    p.x += a * cos(argX);
    rowX -= a * sin(argX) * i * uFrequency.x * soften * rowY;
    float argY = i * uFrequency.y * p.x + uTime;
    p.y += a * cos(argY);
    rowY -= a * sin(argY) * i * uFrequency.y * soften * rowX;
  }
  float phase = uTime - p.x - p.y;
  vec2 field = -(rowX + rowY);
  float density = max(length(field), 1e-3);
  vec2 across = field / density;
  float k = uSharpness;
  float sn = sin(phase);
  float cs = cos(phase);
  float th = tanh(k * sn);
  float bevel = (1.0 - th * th) / tanh(k);
  float fade = smoothstep(3.0, 9.0, 3.14159 * uUnit / density);
  float weight = uDepth * uPresence * fade;
  vec2 slope = k * cs * bevel * weight * across + slopeAt(frag / uResolution) * uRipple;

  vec3 v = normalize(vec3(uv * 0.1, -1.0));
  vec3 rgb = shade(slope, v, uRoughness, uTint);
  rgb = aces(rgb * uExposure);
  fragColor = vec4(rgb, 0.85);
}`

function compileShader(gl, source, type) {
  const shader = gl.createShader(type)
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    const info = gl.getShaderInfoLog(shader)
    gl.deleteShader(shader)
    throw new Error('Shader compilation error: ' + info)
  }
  return shader
}

function createProgram(gl, vsSource, fsSource) {
  const vs = compileShader(gl, vsSource, gl.VERTEX_SHADER)
  const fs = compileShader(gl, fsSource, gl.FRAGMENT_SHADER)
  const prog = gl.createProgram()
  gl.attachShader(prog, vs)
  gl.attachShader(prog, fs)
  gl.linkProgram(prog)
  if (!gl.getProgramParameter(prog, gl.LINK_STATUS)) {
    throw new Error('Program link error: ' + gl.getProgramInfoLog(prog))
  }
  const count = gl.getProgramParameter(prog, gl.ACTIVE_UNIFORMS)
  const uniforms = {}
  for (let i = 0; i < count; i++) {
    const info = gl.getActiveUniform(prog, i)
    if (info) uniforms[info.name] = gl.getUniformLocation(prog, info.name)
  }
  return { program: prog, uniforms }
}

function createTarget(gl, w, h, internal, format, type) {
  const tex = gl.createTexture()
  gl.bindTexture(gl.TEXTURE_2D, tex)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.NEAREST)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
  gl.texImage2D(gl.TEXTURE_2D, 0, internal, w, h, 0, format, type, null)
  const fb = gl.createFramebuffer()
  gl.bindFramebuffer(gl.FRAMEBUFFER, fb)
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0)
  return { texture: tex, framebuffer: fb }
}

onMounted(() => {
  const canvas = canvasRef.value
  const container = containerRef.value
  if (!canvas || !container) {
    useFallback.value = true
    return
  }

  try {
    gl = canvas.getContext('webgl2', { alpha: true, antialias: false, premultipliedAlpha: false })
    if (!gl) {
      useFallback.value = true
      return
    }

    gl.getExtension('EXT_color_buffer_float')

    const simProg = createProgram(gl, VERTEX, SIM)
    const slopeProg = createProgram(gl, VERTEX, SLOPE)
    const chromeProg = createProgram(gl, VERTEX, CHROME)

    const vao = gl.createVertexArray()
    gl.bindVertexArray(vao)

    let width = container.clientWidth || 300
    let height = container.clientHeight || 150
    const dpr = Math.min(window.devicePixelRatio || 1, 2)

    canvas.width = Math.round(width * dpr)
    canvas.height = Math.round(height * dpr)

    const simW = Math.max(1, Math.floor(canvas.width / 4))
    const simH = Math.max(1, Math.floor(canvas.height / 4))

    let stateA = createTarget(gl, simW, simH, gl.RG16F, gl.RG, gl.HALF_FLOAT)
    let stateB = createTarget(gl, simW, simH, gl.RG16F, gl.RG, gl.HALF_FLOAT)
    let slopeTgt = createTarget(gl, simW, simH, gl.RG16F, gl.RG, gl.HALF_FLOAT)

    let lastX = 0
    let lastY = 0
    let pointerActive = false
    let impulseStrength = 0
    let mouseAx = 0, mouseAy = 0, mouseBx = 0, mouseBy = 0

    const handlePointerMove = (e) => {
      if (!props.interactive) return
      const rect = canvas.getBoundingClientRect()
      const x = ((e.clientX - rect.left) / rect.width) * simW
      const y = (1.0 - (e.clientY - rect.top) / rect.height) * simH

      if (pointerActive) {
        mouseAx = lastX
        mouseAy = lastY
        mouseBx = x
        mouseBy = y
        impulseStrength = 1.0
      }
      lastX = x
      lastY = y
      pointerActive = true
    }

    const handlePointerLeave = () => {
      pointerActive = false
    }

    container.addEventListener('pointermove', handlePointerMove)
    container.addEventListener('pointerleave', handlePointerLeave)

    const startTime = performance.now()

    const renderLoop = (now) => {
      if (destroyed) return
      try {
        const time = (now - startTime) * 0.001 * props.speed

        // 1. Sim Step
        gl.viewport(0, 0, simW, simH)
        gl.useProgram(simProg.program)
        gl.bindFramebuffer(gl.FRAMEBUFFER, stateB.framebuffer)
        gl.activeTexture(gl.TEXTURE0)
        gl.bindTexture(gl.TEXTURE_2D, stateA.texture)
        gl.uniform1i(simProg.uniforms.uState, 0)
        gl.uniform2f(simProg.uniforms.uSize, simW, simH)
        gl.uniform4f(simProg.uniforms.uStroke, mouseAx, mouseAy, mouseBx, mouseBy)
        gl.uniform2f(simProg.uniforms.uImpulse, impulseStrength * 0.5, 3.5)
        gl.drawArrays(gl.TRIANGLES, 0, 3)

        // Swap state
        const tmp = stateA
        stateA = stateB
        stateB = tmp
        impulseStrength *= 0.85

        // 2. Slope Step
        gl.useProgram(slopeProg.program)
        gl.bindFramebuffer(gl.FRAMEBUFFER, slopeTgt.framebuffer)
        gl.activeTexture(gl.TEXTURE0)
        gl.bindTexture(gl.TEXTURE_2D, stateA.texture)
        gl.uniform1i(slopeProg.uniforms.uState, 0)
        gl.uniform2f(slopeProg.uniforms.uSize, simW, simH)
        gl.drawArrays(gl.TRIANGLES, 0, 3)

        // 3. Render Chrome Step to Canvas
        gl.viewport(0, 0, canvas.width, canvas.height)
        gl.bindFramebuffer(gl.FRAMEBUFFER, null)
        gl.useProgram(chromeProg.program)

        gl.activeTexture(gl.TEXTURE0)
        gl.bindTexture(gl.TEXTURE_2D, slopeTgt.texture)
        gl.uniform1i(chromeProg.uniforms.uSlope, 0)
        gl.uniform2f(chromeProg.uniforms.uSlopeSize, simW, simH)
        gl.uniform2f(chromeProg.uniforms.uResolution, canvas.width, canvas.height)
        gl.uniform1f(chromeProg.uniforms.uUnit, Math.min(canvas.width, canvas.height))
        gl.uniform1f(chromeProg.uniforms.uTime, time)
        gl.uniform1f(chromeProg.uniforms.uAmplitude, props.amplitude)
        gl.uniform2f(chromeProg.uniforms.uFrequency, 0.4, 0.4)
        gl.uniform1f(chromeProg.uniforms.uDetail, props.detail)
        gl.uniform1f(chromeProg.uniforms.uSharpness, 0.8)
        gl.uniform1f(chromeProg.uniforms.uDepth, 1.2)
        gl.uniform1f(chromeProg.uniforms.uPresence, 1.0)
        gl.uniform3f(chromeProg.uniforms.uTint, props.tint[0], props.tint[1], props.tint[2])
        gl.uniform2f(chromeProg.uniforms.uShift, 0.0, 0.0)
        gl.uniform1f(chromeProg.uniforms.uRoughness, props.roughness)
        gl.uniform1f(chromeProg.uniforms.uExposure, 1.0)
        gl.uniform1f(chromeProg.uniforms.uLight, props.lightMode ? 1.0 : 0.0)
        gl.uniform1f(chromeProg.uniforms.uRipple, 1.2)

        gl.drawArrays(gl.TRIANGLES, 0, 3)

        animationFrameId = requestAnimationFrame(renderLoop)
      } catch (err) {
        console.warn('WebGL render error, using fallback:', err)
        useFallback.value = true
      }
    }

    animationFrameId = requestAnimationFrame(renderLoop)

    const handleResize = () => {
      if (!container || !canvas || destroyed) return
      width = container.clientWidth || 300
      height = container.clientHeight || 150
      canvas.width = Math.round(width * dpr)
      canvas.height = Math.round(height * dpr)
    }

    window.addEventListener('resize', handleResize)

    onUnmounted(() => {
      destroyed = true
      if (animationFrameId) cancelAnimationFrame(animationFrameId)
      window.removeEventListener('resize', handleResize)
      container.removeEventListener('pointermove', handlePointerMove)
      container.removeEventListener('pointerleave', handlePointerLeave)
      if (gl) {
        if (stateA && stateA.texture) gl.deleteTexture(stateA.texture)
        if (stateB && stateB.texture) gl.deleteTexture(stateB.texture)
        if (slopeTgt && slopeTgt.texture) gl.deleteTexture(slopeTgt.texture)
        if (stateA && stateA.framebuffer) gl.deleteFramebuffer(stateA.framebuffer)
        if (stateB && stateB.framebuffer) gl.deleteFramebuffer(stateB.framebuffer)
        if (slopeTgt && slopeTgt.framebuffer) gl.deleteFramebuffer(slopeTgt.framebuffer)
      }
    })
  } catch (err) {
    console.warn('Failed to initialize WebGL2 liquid glass shader:', err)
    useFallback.value = true
  }
})
</script>

<style scoped>
.liquid-glass-wrapper {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 8px;
  overflow: hidden;
}

.liquid-glass-canvas {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.liquid-glass-fallback {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(15, 23, 42, 0.95), rgba(8, 20, 48, 0.9));
  overflow: hidden;
  z-index: 0;
}

.glass-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(40px);
  opacity: 0.6;
  animation: floatOrb 10s ease-in-out infinite alternate;
}

.orb-1 {
  width: 280px;
  height: 140px;
  background: radial-gradient(circle, rgba(37, 99, 235, 0.45) 0%, transparent 70%);
  top: -20px;
  left: 10%;
}

.orb-2 {
  width: 320px;
  height: 160px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.3) 0%, transparent 70%);
  bottom: -30px;
  right: 15%;
  animation-duration: 14s;
  animation-direction: alternate-reverse;
}

.orb-3 {
  width: 200px;
  height: 100px;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.35) 0%, transparent 70%);
  top: 30%;
  left: 45%;
  animation-duration: 8s;
}

@keyframes floatOrb {
  0% {
    transform: translate(0, 0) scale(1);
  }
  50% {
    transform: translate(30px, 15px) scale(1.08);
  }
  100% {
    transform: translate(-25px, -10px) scale(0.95);
  }
}

.liquid-glass-content {
  position: relative;
  z-index: 1;
  width: 100%;
  height: 100%;
}
</style>
