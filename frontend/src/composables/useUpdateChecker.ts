import { ref } from 'vue'

export interface UpdateInfo {
  latestVersion: string
  downloadUrl: string
  releaseNotes?: string
}

export interface UpdateStatus {
  isDownloading: boolean
  isInstalling: boolean
  downloadProgress: number
  errorMessage: string | null
}

const hasNewVersionDialog = ref<boolean>(false)
const isLatestVersionDialog = ref<boolean>(false)
const checkUpdateFailedDialog = ref<boolean>(false)
const currentVersion = ref<string | null>(null)
const updateInfo = ref<UpdateInfo | null>(null)
const updateErrorMessage = ref<string>('')
const updateStatus = ref<UpdateStatus>({
  isDownloading: false,
  isInstalling: false,
  downloadProgress: 0,
  errorMessage: null,
})
const extractDir = ref<string | null>(null)

export function useUpdateChecker() {
  /**
   * 比较版本号
   * 返回 1 表示 v1 > v2, -1 表示 v1 < v2, 0 表示相等
   */
  function compareVersions(v1: string, v2: string): number {
    const parts1 = v1.split('.').map(Number)
    const parts2 = v2.split('.').map(Number)
    const maxLength = Math.max(parts1.length, parts2.length)

    for (let i = 0; i < maxLength; i++) {
      const part1 = parts1[i] || 0
      const part2 = parts2[i] || 0
      if (part1 > part2) return 1
      if (part1 < part2) return -1
    }
    return 0
  }

  /**
   * 检查更新
   * @param showIfLatest 如果已是最新版本，是否显示提示
   */
  async function checkForUpdates(showIfLatest: boolean = false) {
    try {
      // 从后端 API 检查更新
      const response = await fetch('/api/update/check')
      const data = await response.json()

      if (data.error) {
        updateErrorMessage.value = data.error
        checkUpdateFailedDialog.value = true
        return
      }

      currentVersion.value = data.current_version
      updateInfo.value = {
        latestVersion: data.latest_version,
        downloadUrl: data.download_url,
        releaseNotes: data.release_notes,
      }

      if (data.has_update) {
        hasNewVersionDialog.value = true
      } else if (showIfLatest) {
        isLatestVersionDialog.value = true
      }
    } catch (error) {
      console.error('检查更新失败：', error)
      updateErrorMessage.value =
        error instanceof Error ? error.message : '网络请求失败，请检查网络连接'
      checkUpdateFailedDialog.value = true
    }
  }

  /**
   * 下载更新
   */
  async function downloadUpdate() {
    try {
      updateStatus.value.isDownloading = true
      updateStatus.value.downloadProgress = 0
      updateStatus.value.errorMessage = null

      const response = await fetch('/api/update/download', {
        method: 'POST',
      })
      const data = await response.json()

      if (data.error) {
        updateStatus.value.errorMessage = data.error
        return false
      }

      if (data.ready_to_install) {
        extractDir.value = data.extract_dir
        return true
      }

      return false
    } catch (error) {
      console.error('下载更新失败：', error)
      updateStatus.value.errorMessage =
        error instanceof Error ? error.message : '下载失败'
      return false
    } finally {
      updateStatus.value.isDownloading = false
    }
  }

  /**
   * 安装更新
   */
  async function installUpdate() {
    if (!extractDir.value) {
      updateStatus.value.errorMessage = '没有可安装的更新'
      return false
    }

    try {
      updateStatus.value.isInstalling = true
      updateStatus.value.errorMessage = null

      const response = await fetch('/api/update/install', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          extract_dir: extractDir.value,
        }),
      })
      const data = await response.json()

      if (data.error) {
        updateStatus.value.errorMessage = data.error
        return false
      }

      return true
    } catch (error) {
      console.error('安装更新失败：', error)
      updateStatus.value.errorMessage =
        error instanceof Error ? error.message : '安装失败'
      return false
    } finally {
      updateStatus.value.isInstalling = false
    }
  }

  /**
   * 获取更新状态（用于轮询）
   */
  async function pollUpdateStatus() {
    try {
      const response = await fetch('/api/update/status')
      const data = await response.json()
      updateStatus.value = data
    } catch (error) {
      console.error('获取更新状态失败：', error)
    }
  }

  /**
   * 开始轮询更新状态
   */
  function startPollingUpdateStatus(interval: number = 500) {
    const timerId = setInterval(async () => {
      await pollUpdateStatus()
      if (!updateStatus.value.isDownloading && !updateStatus.value.isInstalling) {
        clearInterval(timerId)
      }
    }, interval)
    return timerId
  }

  return {
    // 状态
    hasNewVersionDialog,
    isLatestVersionDialog,
    checkUpdateFailedDialog,
    currentVersion,
    updateInfo,
    updateErrorMessage,
    updateStatus,
    // 方法
    checkForUpdates,
    downloadUpdate,
    installUpdate,
    pollUpdateStatus,
    startPollingUpdateStatus,
  }
}
