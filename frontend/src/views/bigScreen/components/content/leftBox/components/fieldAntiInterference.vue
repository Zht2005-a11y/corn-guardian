<template>
  <div class="anti-interfere-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>复杂大田环境抗干扰鲁棒性评测</span>
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
    tooltip: { trigger: 'item' },
    radar: {
      indicator: [
        { name: '强日光眩光抑制', max: 100 },
        { name: '露水反光过滤', max: 100 },
        { name: '泥水溅渍剥离', max: 100 },
        { name: '杂草重叠分割', max: 100 },
        { name: '微细早期病斑捕获', max: 100 },
        { name: '复合多病并发区分', max: 100 }
      ],
      center: ['50%', '52%'],
      radius: '62%',
      splitNumber: 4,
      axisName: {
        color: '#abcfff',
        fontSize: 10
      },
      splitLine: {
        lineStyle: {
          color: [
            'rgba(83, 157, 255, 0.1)',
            'rgba(83, 157, 255, 0.2)',
            'rgba(83, 157, 255, 0.3)',
            'rgba(83, 157, 255, 0.4)'
          ]
        }
      },
      splitArea: {
        show: true,
        areaStyle: {
          color: ['rgba(6, 72, 156, 0.1)', 'rgba(6, 72, 156, 0.25)']
        }
      },
      axisLine: {
        lineStyle: {
          color: 'rgba(83, 157, 255, 0.35)'
        }
      }
    },
    series: [
      {
        name: '抗逆鲁棒性评分',
        type: 'radar',
        data: [
          {
            value: [96.5, 94.8, 92.3, 95.1, 91.7, 93.4],
            name: '当前模型性能',
            symbol: 'circle',
            symbolSize: 4,
            itemStyle: { color: '#539dff' },
            lineStyle: { width: 1.5, color: '#539dff' },
            areaStyle: {
              color: 'rgba(83, 157, 255, 0.35)'
            }
          }
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
.anti-interfere-box {
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
