import { defineStore } from 'pinia'

export const useGlobalStore = defineStore('global', {
  state: () => ({
    advanced: false,
    use_audio: true,
    uploadProgress: 0,
    isUploading: false,
    currentVideoName: '',
    processingStarted: false
  }),
  
  getters: {
    isProcessing: (state) => state.processingStarted
  },
  
  actions: {
    setAdvanced(value) {
      this.advanced = value
    },
    
    setUseAudio(value) {
      this.use_audio = value
    },
    
    setUploadProgress(value) {
      this.uploadProgress = value
    },
    
    setUploading(value) {
      this.isUploading = value
    },
    
    setCurrentVideoName(name) {
      this.currentVideoName = name
    },
    
    setProcessingStarted(value) {
      this.processingStarted = value
    },
    
    resetAll() {
      this.advanced = false
      this.use_audio = true
      this.uploadProgress = 0
      this.isUploading = false
      this.currentVideoName = ''
      this.processingStarted = false
    },
    
    async resetBackend() {
      try {
        const response = await fetch('http://127.0.0.1:8001/reset_session/', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          }
        })
        const data = await response.json()
        return data
      } catch (error) {
        console.error('重置后端状态失败:', error)
        return { success: false, message: error.message }
      }
    },
    
    async fullReset() {
      this.resetAll()
      await this.resetBackend()
    }
  }
})
