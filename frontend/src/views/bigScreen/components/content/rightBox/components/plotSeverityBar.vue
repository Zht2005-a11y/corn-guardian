<template>
  <div class="plot-bar-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>各试验地块病情严重度指数</span>
    </div>
    <div ref="chartRef" class="chart-area"></div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref(null)
let myChart = null

const initChart = () => {
  if (!chartRef.value) return
  myChart = echarts.init(chartRef.value)

  const option = {
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'shadow' }
    },
    grid: {
      top: '20%',
      bottom: '12%',
      left: '10%',
      right: '6%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      data: ['1号示范田', '密植试验区', '间作大豆带', '灌溉试验带', '迎风潮湿区'],
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      axisLabel: { color: '#abcfff', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: '病情指数 (DI)',
      min: 0,
      max: 100,
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
      axisLabel: { color: '#abcfff', fontSize: 10 },
      nameTextStyle: { color: '#93bde8', fontSize: 10 }
    },
    series: [
      {
        name: '病情指数',
        type: 'bar',
        barWidth: '36%',
        data: [
          {
            value: 38,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#539dff' },
                { offset: 1, color: '#004dcf' }
              ])
            }
          },
          {
            value: 74,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#f59e0b' },
                { offset: 1, color: '#b45309' }
              ])
            }
          },
          {
            value: 29,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#38bdf8' },
                { offset: 1, color: '#0284c7' }
              ])
            }
          },
          {
            value: 58,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#60a5fa' },
                { offset: 1, color: '#1d4ed8' }
              ])
            }
          },
          {
            value: 86,
            itemStyle: {
              color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
                { offset: 0, color: '#e28557' },
                { offset: 1, color: '#c2410c' }
              ])
            }
          }
        ],
        itemStyle: {
          borderRadius: [3, 3, 0, 0]
        },
        label: {
          show: true,
          position: 'top',
          color: '#e0eeff',
          fontSize: 10
        }
      }
    ]
  }

  myChart.setOption(option)
}

const handleResize = () => {
  myChart && myChart.resize()
}

onMounted(() => {
  initChart()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  if (myChart) myChart.dispose()
})
</script>

<style lang="scss" scoped>
.plot-bar-box {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;

  .title {
    width: 100%;
    height: 31px;
    min-height: 31px;
    display: flex;
    align-items: center;
    background-image: url('@/assets/img/bigScreen/titleBg.png');
    background-size: 100% 100%;
    background-repeat: no-repeat;

    span {
      margin-left: 35px;
      font-size: 14px;
      font-weight: bold;
      background-image: linear-gradient(to bottom, #ffffff, #e0eeff, #abcfff, #7cb4ff, #539dff);
      background-clip: text;
      -webkit-background-clip: text;
      color: transparent;
    }
  }

  .chart-area {
    flex: 1;
    width: 100%;
  }
}
</style>
