import { defineStore } from 'pinia'

export const useGlobalStore = defineStore('global', {
  state: () => ({
    advanced: false,
    use_audio: true
  }),
  actions: {
    setAdvanced(value) {
      this.advanced = value
    },
    setUseAudio(value) {
      this.use_audio = value
    }
  }
})
