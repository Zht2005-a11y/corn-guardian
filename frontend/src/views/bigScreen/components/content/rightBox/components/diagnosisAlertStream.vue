<template>
  <div class="alert-stream-box">
    <!-- 原仓库标志性 titleBg 标题条 -->
    <div class="title">
      <span>植保巡检预警与诊断日志流</span>
    </div>

    <!-- 规整的日志列表 (呼吸感适中，主次分明) -->
    <div class="log-stream">
      <div v-for="(item, idx) in logList" :key="idx" class="log-row" :class="item.type">
        <span class="log-timestamp">{{ item.time }}</span>
        <span class="log-badge" :class="item.type">{{ item.tag }}</span>
        <div class="log-text">
          <div class="log-main">{{ item.title }}</div>
          <div class="log-sub">{{ item.desc }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'

const logList = ref([
  {
    time: '14:15:20',
    type: 'danger',
    tag: '重点预警',
    title: '迎风潮湿区 连片大斑病侵染',
    desc: '识别置信度 97.4%，建议立即启动植保无人机飞防作业。'
  },
  {
    time: '13:50:12',
    type: 'warning',
    tag: '环境预警',
    title: '田间相对湿度持续高于 84%',
    desc: '传感器触发南方锈病暴发气象阈值警报。'
  },
  {
    time: '13:20:45',
    type: 'success',
    tag: '飞防完成',
    title: '1号示范田 变量喷雾完成',
    desc: '大疆 T50 喷施 25% 嘧菌酯 60 亩，雾滴均匀度 96.8%。'
  },
  {
    time: '12:45:10',
    type: 'info',
    tag: '例行巡检',
    title: '密植试验区 叶面图像采集完成',
    desc: 'AI 前端算法抗干扰滤波完成，剔除强日光眩光 142 张。'
  }
])

let timer = null

onMounted(() => {
  timer = setInterval(() => {
    const now = new Date()
    const timeStr = `${String(now.getHours()).padStart(2, '0')}:${String(now.getMinutes()).padStart(2, '0')}:${String(now.getSeconds()).padStart(2, '0')}`
    const mockEvents = [
      {
        time: timeStr,
        type: 'danger',
        tag: '病斑检出',
        title: '间作大豆带 检出疑似灰斑病初侵染',
        desc: '条状病斑占比约 14.5%，建议结合苗情叶面施药。'
      },
      {
        time: timeStr,
        type: 'warning',
        tag: '环境诱因',
        title: '叶面湿润时长 (LWHR) 达 6.8 小时',
        desc: '病原菌孢子萌发适宜度上升，请重点观察下部叶片。'
      },
      {
        time: timeStr,
        type: 'info',
        tag: '模型自适应',
        title: '强光眩光抑制滤镜 参数动态更新',
        desc: '针对强日光 68.5kLux 完成光斑反射归一化。'
      }
    ]
    const randomEvent = mockEvents[Math.floor(Math.random() * mockEvents.length)]
    logList.value.unshift(randomEvent)
    if (logList.value.length > 5) {
      logList.value.pop()
    }
  }, 9000)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<style lang="scss" scoped>
.alert-stream-box {
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

  .log-stream {
    flex: 1;
    overflow-y: hidden;
    padding: 6px 8px;
    box-sizing: border-box;
    display: flex;
    flex-direction: column;
    gap: 6px;

    .log-row {
      display: flex;
      align-items: flex-start;
      gap: 6px;
      background: rgba(6, 72, 156, 0.2);
      border: 1px solid rgba(83, 157, 255, 0.25);
      border-radius: 4px;
      padding: 5px 8px;

      &.danger {
        border-left: 3px solid #e28557;
      }

      &.warning {
        border-left: 3px solid #f59e0b;
      }

      &.success {
        border-left: 3px solid #539dff;
      }

      &.info {
        border-left: 3px solid #38bdf8;
      }

      .log-timestamp {
        font-size: 10px;
        color: #93bde8;
        font-family: monospace;
        white-space: nowrap;
        margin-top: 1px;
      }

      .log-badge {
        font-size: 9px;
        padding: 1px 4px;
        border-radius: 3px;
        white-space: nowrap;
        font-weight: bold;

        &.danger {
          background: rgba(226, 133, 87, 0.3);
          color: #ff9d66;
        }

        &.warning {
          background: rgba(245, 158, 11, 0.3);
          color: #fbbf24;
        }

        &.success {
          background: rgba(83, 157, 255, 0.3);
          color: #e0eeff;
        }

        &.info {
          background: rgba(56, 189, 248, 0.25);
          color: #7dd3fc;
        }
      }

      .log-text {
        flex: 1;

        .log-main {
          font-size: 11px;
          font-weight: bold;
          color: #ffffff;
        }

        .log-sub {
          font-size: 10px;
          color: #abcfff;
          line-height: 1.3;
        }
      }
    }
  }
}
</style>
