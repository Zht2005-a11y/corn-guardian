<template>
  <div class="disease-trend-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>发病风险指数与温湿度趋势预测</span>
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
      trigger: 'axis'
    },
    legend: {
      data: ['大斑病风险', '南方锈病风险', '田间相对湿度'],
      top: '2%',
      right: '2%',
      textStyle: { color: '#abcfff', fontSize: 10 },
      itemWidth: 10,
      itemHeight: 8
    },
    grid: {
      top: '24%',
      bottom: '12%',
      left: '10%',
      right: '8%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      axisLabel: { color: '#abcfff', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '风险指数',
        min: 0,
        max: 100,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#abcfff', fontSize: 10 },
        nameTextStyle: { color: '#93bde8', fontSize: 10 }
      },
      {
        type: 'value',
        name: '湿度(%)',
        min: 50,
        max: 100,
        splitLine: { show: false },
        axisLabel: { color: '#539dff', fontSize: 10 },
        nameTextStyle: { color: '#539dff', fontSize: 10 }
      }
    ],
    series: [
      {
        name: '大斑病风险',
        type: 'line',
        smooth: true,
        data: [45, 52, 68, 74, 82, 88, 85],
        itemStyle: { color: '#e28557' },
        lineStyle: { width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(226, 133, 87, 0.35)' },
            { offset: 1, color: 'rgba(226, 133, 87, 0.02)' }
          ])
        }
      },
      {
        name: '南方锈病风险',
        type: 'line',
        smooth: true,
        data: [35, 42, 58, 64, 76, 79, 81],
        itemStyle: { color: '#f59e0b' },
        lineStyle: { width: 1.8 }
      },
      {
        name: '田间相对湿度',
        type: 'line',
        yAxisIndex: 1,
        smooth: true,
        data: [72, 75, 82, 85, 89, 86, 84],
        itemStyle: { color: '#539dff' },
        lineStyle: { type: 'dashed', width: 1.5 }
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
.disease-trend-box {
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
