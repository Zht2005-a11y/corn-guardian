<script setup>
import diseaseTrend from '@/views/bigScreen/components/content/rightBox/components/diseaseTrend.vue'
import plotSeverityBar from '@/views/bigScreen/components/content/rightBox/components/plotSeverityBar.vue'
import diagnosisAlertStream from '@/views/bigScreen/components/content/rightBox/components/diagnosisAlertStream.vue'

const items = [diseaseTrend, plotSeverityBar, diagnosisAlertStream]
</script>

<template>
  <div class="rightBox">
    <div v-for="item in 3" :key="item" :class="`item${item}`">
      <component :is="items[item - 1]" />
    </div>
  </div>
</template>

<style lang="scss" scoped>
@mixin layout($num) {
  @if $num == 1 {
    height: 38%;
  } @else if $num == 2 {
    height: 33%;
  } @else {
    height: 28%;
  }
}

.rightBox {
  width: 27.5%;
  height: 100%;
  margin: 0 0.2% 0 0;
  padding: 0.3% 0.25%;
  box-sizing: border-box;
  border: 1.1px solid #004dcf;
  background-image: linear-gradient(
    to bottom,
    rgba(6, 72, 156, 0.18),
    rgba(34, 94, 172, 0.18),
    rgba(50, 108, 182, 0.18),
    rgba(15, 79, 161, 0.18)
  );
  border-radius: 10px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;

  @for $i from 1 through 3 {
    .item#{$i} {
      @include layout($i);
    }
  }
}
</style>
