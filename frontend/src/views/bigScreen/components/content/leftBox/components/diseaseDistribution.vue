<template>
  <div class="disease-dist-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>玉米多发叶部病害发生占比</span>
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
      trigger: 'item',
      formatter: '{b}: {c}% ({d}%)'
    },
    legend: {
      orient: 'vertical',
      right: '4%',
      top: 'center',
      textStyle: { color: '#abcfff', fontSize: 10 },
      itemWidth: 8,
      itemHeight: 8
    },
    series: [
      {
        name: '病害占比',
        type: 'pie',
        radius: ['35%', '72%'],
        center: ['36%', '50%'],
        roseType: 'radius',
        itemStyle: {
          borderRadius: 3,
          borderColor: '#061727',
          borderWidth: 1.2
        },
        label: { show: false },
        emphasis: {
          label: {
            show: true,
            fontSize: 11,
            fontWeight: 'bold',
            color: '#fff'
          }
        },
        data: [
          { value: 34.2, name: '玉米大斑病', itemStyle: { color: '#e28557' } },
          { value: 26.8, name: '玉米南方锈病', itemStyle: { color: '#f59e0b' } },
          { value: 18.5, name: '玉米灰斑病', itemStyle: { color: '#539dff' } },
          { value: 12.3, name: '玉米褐斑病', itemStyle: { color: '#a78bfa' } },
          { value: 8.2, name: '玉米小斑病', itemStyle: { color: '#38bdf8' } }
        ]
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
.disease-dist-box {
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
