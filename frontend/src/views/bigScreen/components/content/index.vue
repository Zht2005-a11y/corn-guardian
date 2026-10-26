<template>
  <div class="main">
    <LeftBox />
    <CenterBox />
    <RightBox />
  </div>
</template>

<script setup>
import LeftBox from '@/views/bigScreen/components/content/leftBox/index.vue'
import CenterBox from '@/views/bigScreen/components/content/centerBox/index.vue'
import RightBox from '@/views/bigScreen/components/content/rightBox/index.vue'
</script>

<style lang="scss" scoped>
.main {
  width: 100%;
  height: calc(100vh - 7.5vh);
  display: flex;
  padding: 0.2% 0.4% 0.4% 0.4%;
  box-sizing: border-box;
  justify-content: space-between;
  overflow: hidden;
}
</style>
