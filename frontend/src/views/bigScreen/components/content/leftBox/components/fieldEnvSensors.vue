<template>
  <div class="field-sensors-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>大田微环境感知与诱因监测</span>
    </div>

    <!-- 4 项环境感知指标卡 (清爽规整，不拥挤) -->
    <div class="metrics-grid">
      <div class="metric-item">
        <span class="m-label">大田气温</span>
        <span class="m-val">28.4 <small>°C</small></span>
      </div>
      <div class="metric-item highlight">
        <span class="m-label">空气相对湿度</span>
        <span class="m-val orange">84.2 <small>%</small></span>
      </div>
      <div class="metric-item">
        <span class="m-label">光照辐射度</span>
        <span class="m-val">68.5 <small>kLux</small></span>
      </div>
      <div class="metric-item highlight">
        <span class="m-label">孢子捕捉密度</span>
        <span class="m-val orange">142 <small>个/m³</small></span>
      </div>
    </div>

    <!-- ECharts 双轴趋势图 -->
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
    grid: {
      top: '18%',
      bottom: '12%',
      left: '10%',
      right: '6%',
      containLabel: true
    },
    tooltip: {
      trigger: 'axis'
    },
    xAxis: {
      type: 'category',
      data: ['06:00', '09:00', '12:00', '15:00', '18:00', '当前'],
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
      axisLabel: { color: '#abcfff', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        name: '湿度(%)',
        min: 60,
        max: 100,
        axisLine: { lineStyle: { color: 'rgba(255,255,255,0.15)' } },
        splitLine: { lineStyle: { color: 'rgba(255,255,255,0.06)' } },
        axisLabel: { color: '#abcfff', fontSize: 10 },
        nameTextStyle: { color: '#93bde8', fontSize: 10 }
      },
      {
        type: 'value',
        name: '诱发指数',
        min: 0,
        max: 100,
        splitLine: { show: false },
        axisLabel: { color: '#e28557', fontSize: 10 },
        nameTextStyle: { color: '#e28557', fontSize: 10 }
      }
    ],
    series: [
      {
        name: '叶面相对湿度',
        type: 'line',
        smooth: true,
        data: [92, 88, 76, 79, 83, 84.2],
        itemStyle: { color: '#539dff' },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(83, 157, 255, 0.35)' },
            { offset: 1, color: 'rgba(83, 157, 255, 0.02)' }
          ])
        }
      },
      {
        name: '病害诱发指数',
        type: 'bar',
        yAxisIndex: 1,
        barWidth: '24%',
        data: [78, 65, 42, 50, 72, 81],
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#e28557' },
            { offset: 1, color: 'rgba(226, 133, 87, 0.2)' }
          ]),
          borderRadius: [3, 3, 0, 0]
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
.field-sensors-box {
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

  .metrics-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 6px;
    padding: 6px 8px;
    box-sizing: border-box;

    .metric-item {
      background: rgba(6, 72, 156, 0.25);
      border: 1px solid rgba(83, 157, 255, 0.3);
      border-radius: 4px;
      padding: 4px 8px;
      display: flex;
      justify-content: space-between;
      align-items: center;

      &.highlight {
        border-color: rgba(226, 133, 87, 0.5);
      }

      .m-label {
        font-size: 11px;
        color: #93bde8;
      }

      .m-val {
        font-size: 13px;
        font-weight: bold;
        color: #ffffff;
        font-family: monospace;

        &.orange {
          color: #e28557;
        }

        small {
          font-size: 10px;
          color: #abcfff;
          font-weight: normal;
        }
      }
    }
  }

  .chart-area {
    flex: 1;
    width: 100%;
  }
}
</style>
