<template>
  <div style="width: 100%; height: 100%; padding: 0; overflow: hidden">
    <iframe
      ref="iframeRef"
      src="https://ef.yituliu.cn/"
      style="width: 100%; height: 100%; border: none"
    ></iframe>
  </div>
</template>

<script lang="ts" setup>
// import { nextTick, onMounted, ref, useTemplateRef } from 'vue'

// const iframeSrc = ref(`${import.meta.env.VITE_API_BASE_URL}/others/friend-links`)

// const iframeRef = useTemplateRef<HTMLIFrameElement>('iframeRef')
// onMounted(async () => {
//   await nextTick()
//   const iframe = iframeRef.value
//   if (iframe) {
//     iframe.onload = () => {
//       try {
//         const doc = iframe.contentDocument || iframe.contentWindow?.document
//         if (doc) {
//           const grid = doc.querySelector('.links-grid')
//           if (grid) {
//             // 可以在这里操作 grid 元素
//             console.log('找到 links-grid 元素:', grid)
//           } else {
//             console.log('未找到 links-grid 元素')
//           }
//         }
//       } catch (error) {
//         console.error('无法访问 iframe 内容，可能是跨域问题:', error)
//       }
//     }
//   }
// })

// const content = ref('加载中...')

// onMounted(async () => {
//   try {
//     const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/yituliu/others/friend-links`)
//     const html = await response.text()
//     const parser = new DOMParser()
//     const doc = parser.parseFromString(html, 'text/html')
//     const grid = doc.querySelector('.links-grid')
//     if (grid) {
//       content.value = grid.outerHTML
//     } else {
//       content.value = '未找到 links-grid 元素'
//     }
//   } catch (error) {
//     console.error('加载失败:', error)
//     content.value = '无法加载内容，请检查网络或跨域设置'
//   }
// })
</script>

<style scoped lang="scss"></style>
