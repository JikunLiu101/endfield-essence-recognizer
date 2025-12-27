<template>
  <v-container>
    <v-row class="my-4">
      <v-col cols="12" sm="6" xl="3">
        <v-number-input
          v-model="width"
          controlVariant="split"
          variant="outlined"
          density="comfortable"
          label="宽度"
          hide-details
        />
      </v-col>
      <v-col cols="12" sm="6" xl="3">
        <v-number-input
          v-model="height"
          controlVariant="split"
          variant="outlined"
          density="comfortable"
          label="高度"
          hide-details
        />
      </v-col>
      <v-col cols="12" md="6" xl="3">
        <v-select
          v-model="format"
          variant="outlined"
          density="comfortable"
          :items="['jpg', 'png', 'webp']"
          label="格式"
          hide-details
        />
      </v-col>
      <v-col cols="12" md="6" xl="3">
        <v-slider
          v-model="quality"
          variant="outlined"
          density="comfortable"
          label="质量"
          :min="1"
          :max="100"
          :step="1"
          :disabled="['png'].includes(format)"
          hide-details
        >
          <template #append>
            <v-number-input
              v-model="quality"
              controlVariant="split"
              variant="outlined"
              density="comfortable"
              hide-details
              :step="1"
            />
          </template>
        </v-slider>
      </v-col>
    </v-row>
    <div class="my-4">
      <v-slider v-model="interval" :min="0" :max="1" label="截图间隔（秒）" hide-details>
        <template #append>
          <v-number-input
            v-model="interval"
            controlVariant="split"
            variant="outlined"
            density="comfortable"
            hide-details
            :step="0.1"
            :precision="null"
          />
        </template>
      </v-slider>
    </div>
    <img :src="screenshotUrl" alt="Screenshot" class="my-4" style="max-width: 100%; height: auto" />
  </v-container>
</template>

<script lang="ts" setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'

const interval = ref<number>(0.1)
const width = ref<number>(1920)
const height = ref<number>(1080)
const format = ref<string>('jpg')
const quality = ref<number>(75)
const screenshotUrl = ref<string>('')

let timer: number | null = null

const updateScreenshot = async () => {
  const params = new URLSearchParams({
    width: width.value.toString(),
    height: height.value.toString(),
    format: format.value,
    quality: quality.value.toString(),
  })
  const url = `${import.meta.env.VITE_API_BASE_URL}/screenshot?${params.toString()}&t=${Date.now()}`
  // const oldUrl = screenshotUrl.value
  // fetch(url)
  //   .then((response) => response.blob())
  //   .then((blob) => {
  //     const newUrl = URL.createObjectURL(blob)
  //     screenshotUrl.value = newUrl
  //     // 释放旧的对象URL以防内存泄漏
  //     if (oldUrl) {
  //       URL.revokeObjectURL(oldUrl)
  //     }
  //   })
  //   .catch((error) => {
  //     console.error('Failed to fetch screenshot:', error)
  //   })

  await fetch(url)
    .then((response) => response.json())
    .then((dataUrl) => {
      screenshotUrl.value = dataUrl
    })
}

const startTimer = () => {
  if (timer) clearInterval(timer)
  if (interval.value > 0) {
    timer = window.setInterval(updateScreenshot, interval.value * 1000)
  }
}

onMounted(() => {
  updateScreenshot() // 初始加载
  startTimer()
})

onUnmounted(() => {
  if (timer) {
    window.clearInterval(timer)
  }
})

watch([width, height, format, quality, interval], startTimer)
</script>

<style scoped lang="scss"></style>
