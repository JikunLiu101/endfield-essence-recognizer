<template>
  <!-- 发现新版本 -->
  <v-dialog v-model="hasNewVersionDialog" max-width="600">
    <v-card>
      <v-card-title>发现新版本！</v-card-title>
      <v-card-text>
        <p><strong>当前版本：</strong>{{ currentVersion }}</p>
        <p><strong>最新版本：</strong>{{ updateInfo?.latestVersion }}</p>
        <div v-if="updateInfo?.releaseNotes" class="mt-4">
          <strong>更新说明：</strong>
          <pre class="release-notes">{{ updateInfo.releaseNotes }}</pre>
        </div>

        <!-- 下载进度 -->
        <div v-if="updateStatus.isDownloading" class="mt-4">
          <p><strong>正在下载更新...</strong></p>
          <v-progress-linear
            :model-value="updateStatus.downloadProgress"
            height="25"
            color="primary"
          >
            <template #default="{ value }">
              <strong>{{ Math.ceil(value) }}%</strong>
            </template>
          </v-progress-linear>
        </div>

        <!-- 安装中 -->
        <div v-if="updateStatus.isInstalling" class="mt-4">
          <v-alert type="info">
            <strong>正在安装更新，程序将在 3 秒后自动重启...</strong>
          </v-alert>
        </div>

        <!-- 错误信息 -->
        <div v-if="updateStatus.errorMessage" class="mt-4">
          <v-alert type="error">{{ updateStatus.errorMessage }}</v-alert>
        </div>
      </v-card-text>
      <v-card-actions>
        <v-btn
          @click="hasNewVersionDialog = false"
          :disabled="updateStatus.isDownloading || updateStatus.isInstalling"
        >
          稍后提醒
        </v-btn>
        <v-btn
          href="https://ef.yituliu.cn/resources/essence-recognizer"
          target="_blank"
          :disabled="updateStatus.isDownloading || updateStatus.isInstalling"
        >
          前往官网
        </v-btn>
        <v-spacer></v-spacer>
        <v-btn
          v-if="!updateStatus.isDownloading && !updateStatus.isInstalling && !downloadCompleted"
          color="primary"
          variant="elevated"
          @click="handleDownloadAndInstall"
        >
          自动下载并安装
        </v-btn>
        <v-btn
          v-if="downloadCompleted && !updateStatus.isInstalling"
          color="success"
          variant="elevated"
          @click="handleInstall"
        >
          立即安装
        </v-btn>
      </v-card-actions>
    </v-card>
  </v-dialog>

  <!-- 已是最新版本 -->
  <v-snackbar v-model="isLatestVersionDialog" color="info">
    <strong>已是最新版本：</strong>{{ currentVersion }}
    <template #actions>
      <v-btn text @click="isLatestVersionDialog = false">关闭</v-btn>
    </template>
  </v-snackbar>

  <!-- 检查更新失败 -->
  <v-snackbar v-model="checkUpdateFailedDialog" color="error">
    <strong>检查更新失败：</strong>{{ updateErrorMessage }}
    <template #actions>
      <v-btn text @click="checkUpdateFailedDialog = false">关闭</v-btn>
    </template>
  </v-snackbar>
</template>

<script lang="ts" setup>
import { ref } from 'vue'
import { useUpdateChecker } from '@/composables/useUpdateChecker'

const {
  hasNewVersionDialog,
  isLatestVersionDialog,
  checkUpdateFailedDialog,
  currentVersion,
  updateInfo,
  updateErrorMessage,
  updateStatus,
  downloadUpdate,
  installUpdate,
  startPollingUpdateStatus,
} = useUpdateChecker()

const downloadCompleted = ref(false)

async function handleDownloadAndInstall() {
  downloadCompleted.value = false
  
  // 开始轮询更新状态
  startPollingUpdateStatus()
  
  const success = await downloadUpdate()
  if (success) {
    downloadCompleted.value = true
  }
}

async function handleInstall() {
  const success = await installUpdate()
  if (success) {
    // 安装成功，程序将自动重启
    // 这里不需要做额外处理
  }
}
</script>

<style scoped>
.release-notes {
  max-height: 300px;
  overflow-y: auto;
  padding: 12px;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 4px;
  font-size: 0.875rem;
  white-space: pre-wrap;
  word-wrap: break-word;
}
</style>
