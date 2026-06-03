<template>
  <div class="generating-container">
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>

    <div class="generating-content">
      <!-- 步骤条 -->
      <div class="steps-container">
        <div class="steps-wrapper">
          <div class="step-item" :class="{ active: progress > 0, completed: progress > 30 }">
            <div class="step-icon">
              <i class="el-icon-video-camera"></i>
            </div>
            <div class="step-content">
              <h3>视频分析</h3>
              <p>{{ isRealtimeMode ? '分段提取视频帧' : '提取关键帧并识别板书区域' }}</p>
            </div>
          </div>

          <div class="step-connector" :class="{ active: progress > 30 }"></div>

          <div class="step-item" :class="{ active: progress > 30, completed: progress > 60 }">
            <div class="step-icon">
              <i class="el-icon-view"></i>
            </div>
            <div class="step-content">
              <h3>内容识别</h3>
              <p>使用 OCR 技术识别板书文字</p>
            </div>
          </div>

          <div class="step-connector" :class="{ active: progress > 60 }"></div>

          <div class="step-item" :class="{ active: progress > 60, completed: progress >= 100 }">
            <div class="step-icon">
              <i class="el-icon-edit"></i>
            </div>
            <div class="step-content">
              <h3>智能整理</h3>
              <p>{{ isRealtimeMode ? '逐段生成实时讲义' : '整理和结构化识别内容' }}</p>
            </div>
          </div>

          <div class="step-connector" :class="{ active: progress >= 100 }"></div>

          <div class="step-item" :class="{ active: progress >= 100 }">
            <div class="step-icon">
              <i class="el-icon-document"></i>
            </div>
            <div class="step-content">
              <h3>生成总结</h3>
              <p>{{ isRealtimeMode ? '合并实时讲义结果' : '生成最终的内容总结' }}</p>
            </div>
          </div>
        </div>
      </div>

      <div class="main-content-wrapper">
        <div class="main-section">
          <div class="content-card">
            <div class="card-header">
              <div class="loading-icon" v-if="progress < 100">
                <i class="el-icon-loading"></i>
              </div>
              <div class="loading-icon success" v-else>
                <i class="el-icon-circle-check"></i>
              </div>

              <h1 class="page-title">
                {{ isRealtimeMode ? '正在实时生成讲义' : '正在处理您的视频' }}
              </h1>

              <p class="page-subtitle">
                {{ isRealtimeMode ? '系统会边处理视频边显示已生成的图文讲义内容' : '请耐心等待，我们正在为您生成精彩的内容总结' }}
              </p>
            </div>

            <!-- 视频处理进度 -->
            <div class="progress-section">
              <div class="progress-header">
                <i class="el-icon-video-camera"></i>
                <span>{{ isRealtimeMode ? '实时生成进度' : '视频处理进度' }}</span>
              </div>

              <div class="progress-content">
                <el-progress
                  :percentage="progress"
                  :status="progress === 100 ? 'success' : ''"
                  :stroke-width="12"
                  :text-inside="false"
                />

                <div class="work-text" v-if="work">
                  <i class="el-icon-info"></i>
                  当前任务：{{ work }}
                </div>

                <div class="segment-text" v-if="isRealtimeMode && totalSegments > 0">
                  已处理片段：{{ currentSegment }} / {{ totalSegments }}
                </div>
              </div>
            </div>

            <!-- 实时讲义预览 -->
            <div class="realtime-section" v-if="isRealtimeMode">
              <div class="realtime-header">
                <div>
                  <h3>
                    <i class="el-icon-document"></i>
                    实时图文讲义预览
                  </h3>
                  <p>下方内容会随着视频处理进度自动更新，关键板书截图会直接插入讲义中</p>
                </div>

                <button
                  class="stop-button"
                  v-if="realtimeStatus === 'processing' || realtimeStatus === 'pending'"
                  @click="stopRealtimeTask"
                >
                  停止生成
                </button>
              </div>

              <div class="realtime-content markdown-body" v-if="realtimeContent" v-html="renderedRealtimeContent"></div>

              <div class="empty-realtime" v-else>
                <i class="el-icon-loading"></i>
                正在识别第一段视频内容，请稍候...
              </div>
            </div>

            <!-- 音频识别进度：非实时模式才显示 -->
            <div class="progress-section" v-if="useAudio && !isRealtimeMode">
              <div class="progress-header">
                <i class="el-icon-microphone"></i>
                <span>音频识别进度</span>
              </div>

              <div class="progress-content audio">
                <el-progress
                  :percentage="audioProgress"
                  :status="audioProgress === 100 ? 'success' : ''"
                  :stroke-width="12"
                  :text-inside="false"
                />

                <div class="work-text" v-if="audioWork">
                  <i class="el-icon-info"></i>
                  当前任务：{{ audioWork }}
                </div>
              </div>
            </div>

            <!-- 处理提示 -->
            <div class="tips-section">
              <h3>
                <i class="el-icon-lightbulb"></i>
                处理提示
              </h3>

              <div class="tips-grid">
                <div class="tip-item">
                  <i class="el-icon-time"></i>
                  <p>{{ isRealtimeMode ? '实时模式会分段输出图文讲义内容' : '处理时间取决于视频长度和复杂度' }}</p>
                </div>

                <div class="tip-item">
                  <i class="el-icon-cpu"></i>
                  <p>我们正在使用 AI 技术进行智能分析</p>
                </div>

                <div class="tip-item">
                  <i class="el-icon-check"></i>
                  <p>完成后将自动跳转到结果页面，并可在我的讲义中查看</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 右侧视频预览区域 -->
        <div class="right-section">
          <div class="video-card">
            <div class="video-header">
              <h2 class="video-title">
                <i class="el-icon-video-camera"></i>
                视频预览
              </h2>
              <p class="video-subtitle">正在处理的视频内容</p>
            </div>

            <div class="video-wrapper">
              <video
                ref="videoPlayer"
                :src="videoUrl"
                controls
                @loadedmetadata="onVideoLoaded"
              >
                您的浏览器不支持视频播放
              </video>
            </div>

            <div class="video-info" v-if="videoDuration">
              <div class="info-item">
                <i class="el-icon-clock"></i>
                <span>视频时长: {{ formatDuration(videoDuration) }}</span>
              </div>
            </div>

            <div class="video-status">
              <div class="status-indicator" :class="{ processing: progress < 100 }">
                <i class="el-icon-loading" v-if="progress < 100"></i>
                <i class="el-icon-circle-check" v-else></i>
                <span>{{ progress < 100 ? '处理中...' : '处理完成' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

    </div>
  </div>
</template>

<script>
import { ref, onMounted, onBeforeUnmount, computed, nextTick } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import { ElMessage } from 'element-plus'
import MarkdownIt from 'markdown-it'

export default {
  setup() {
    const router = useRouter()
    const route = useRoute()
    const globalStore = useGlobalStore()

    const md = new MarkdownIt({
      html: true,
      linkify: true,
      breaks: true
    })

    const videoPlayer = ref(null)
    const videoUrl = ref('')
    const videoDuration = ref(0)

    const useAudio = computed(() => globalStore.use_audio)
    const isRealtimeMode = computed(() => {
      return route.query.mode === 'realtime' || globalStore.generation_mode === 'realtime'
    })

    const progress = ref(0)
    const work = ref('')
    const audioProgress = ref(0)
    const audioWork = ref('')

    const realtimeTaskId = ref(route.query.task_id || globalStore.realtime_task_id || '')
    const realtimeContent = ref('')
    const realtimeStatus = ref('')
    const currentSegment = ref(0)
    const totalSegments = ref(0)

    const renderedRealtimeContent = computed(() => {
      if (!realtimeContent.value) return ''
      return md.render(realtimeContent.value)
    })

    let timer = null

    const formatDuration = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    const onVideoLoaded = () => {
      if (videoPlayer.value) {
        videoDuration.value = videoPlayer.value.duration
      }
    }

    const loadVideo = async () => {
      try {
        const res = await fetch('http://127.0.0.1:8001/get_current_video/')
        if (res.ok) {
          const blob = await res.blob()
          videoUrl.value = URL.createObjectURL(blob)
        }
      } catch (err) {
        console.error('加载视频失败:', err)
      }
    }

    const checkNormalProgress = () => {
      fetch('http://127.0.0.1:8001/get_progress')
        .then(res => res.json())
        .then(data => {
          progress.value = data.progress || 0
          work.value = data.work || ''
        })
        .catch(err => {
          console.error('视频进度获取失败:', err)
        })

      if (useAudio.value) {
        fetch('http://127.0.0.1:8002/get_progress')
          .then(res => res.json())
          .then(data => {
            audioProgress.value = data.percent || 0
            audioWork.value = data.message || '等待音频识别'
          })
          .catch(err => {
            console.error('音频进度获取失败:', err)
          })
      }

      if (progress.value >= 100 && (!useAudio.value || audioProgress.value >= 100)) {
        clearInterval(timer)
        setTimeout(() => router.push('/result'), 1000)
      }
    }

    const checkRealtimeProgress = () => {
      if (!realtimeTaskId.value) {
        work.value = '未找到实时任务 ID，请返回重新开始'
        return
      }

      fetch(`http://127.0.0.1:8001/realtime/status/${realtimeTaskId.value}/`)
        .then(res => res.json())
        .then(data => {
          if (!data.success) {
            work.value = data.message || '实时任务状态获取失败'
            return
          }

          const task = data.task
          realtimeStatus.value = task.status
          progress.value = task.progress || 0
          work.value = task.message || ''
          realtimeContent.value = task.content || ''
          currentSegment.value = task.current_segment || 0
          totalSegments.value = task.total_segments || 0

          nextTick(() => {
            const box = document.querySelector('.realtime-content')
            if (box) {
              box.scrollTop = box.scrollHeight
            }
          })

          if (task.status === 'completed') {
            clearInterval(timer)
            ElMessage.success('实时图文讲义生成完成')
            setTimeout(() => router.push('/result'), 1000)
          }

          if (task.status === 'failed') {
            clearInterval(timer)
            ElMessage.error(task.message || '实时生成失败')
          }

          if (task.status === 'stopped') {
            clearInterval(timer)
            ElMessage.warning('实时生成已停止')
          }
        })
        .catch(err => {
          console.error('实时进度获取失败:', err)
          work.value = '实时进度获取失败，请检查后端服务'
        })
    }

    const stopRealtimeTask = async () => {
      if (!realtimeTaskId.value) return

      try {
        const res = await fetch(`http://127.0.0.1:8001/realtime/stop/${realtimeTaskId.value}/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        })
        const data = await res.json()
        if (data.success) {
          ElMessage.success('已发送停止指令')
        } else {
          ElMessage.error(data.message || '停止失败')
        }
      } catch (err) {
        console.error('停止实时任务失败:', err)
        ElMessage.error('停止实时任务失败')
      }
    }

    onMounted(() => {
      loadVideo()

      if (isRealtimeMode.value) {
        globalStore.setGenerationMode('realtime')
        if (realtimeTaskId.value) {
          globalStore.setRealtimeTaskId(realtimeTaskId.value)
        }
        checkRealtimeProgress()
        timer = setInterval(checkRealtimeProgress, 2000)
      } else {
        checkNormalProgress()
        timer = setInterval(checkNormalProgress, 1000)
      }
    })

    onBeforeUnmount(() => {
      if (timer) {
        clearInterval(timer)
      }
    })

    return {
      progress,
      work,
      audioProgress,
      audioWork,
      useAudio,
      isRealtimeMode,
      realtimeContent,
      renderedRealtimeContent,
      realtimeStatus,
      currentSegment,
      totalSegments,
      videoPlayer,
      videoUrl,
      videoDuration,
      formatDuration,
      onVideoLoaded,
      stopRealtimeTask
    }
  }
}
</script>

<style scoped>
.generating-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f0e8 0%, #e8e0f0 100%);
}

.decoration {
  position: absolute;
  border-radius: 100%;
  opacity: 0.4;
}

.decoration-1 {
  width: 400px;
  height: 400px;
  background: #5c4d82;
  top: -100px;
  left: -100px;
}

.decoration-2 {
  width: 300px;
  height: 300px;
  background: #9b8dc7;
  bottom: -50px;
  right: -50px;
}

.generating-content {
  display: flex;
  flex-direction: column;
  gap: 30px;
  max-width: 1500px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.steps-container {
  background: #ffffff;
  border-radius: 24px;
  padding: 35px 50px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
}

.steps-wrapper {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.step-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 0 0 auto;
  width: 180px;
}

.step-icon {
  width: 70px;
  height: 70px;
  border-radius: 50%;
  background: #faf9fc;
  border: 3px solid #e8e0f0;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 15px;
  transition: all 0.3s ease;
}

.step-icon i {
  font-size: 1.8rem;
  color: #b8a9d4;
  transition: all 0.3s ease;
}

.step-item.active .step-icon {
  border-color: #5c4d82;
  background: #5c4d82;
}

.step-item.active .step-icon i {
  color: #ffffff;
}

.step-item.completed .step-icon {
  background: #5c4d82;
  border-color: #5c4d82;
}

.step-content {
  text-align: center;
}

.step-content h3 {
  font-size: 1rem;
  font-weight: 600;
  color: #b8a9d4;
  margin: 0 0 6px 0;
  transition: all 0.3s ease;
}

.step-item.active .step-content h3 {
  color: #5c4d82;
}

.step-content p {
  font-size: 0.82rem;
  color: #9b8dc7;
  margin: 0;
  line-height: 1.4;
}

.step-connector {
  flex: 1;
  height: 3px;
  background: #e8e0f0;
  margin: 0 20px;
  transform: translateY(-35px);
  transition: all 0.3s ease;
}

.step-connector.active {
  background: #5c4d82;
}

.main-content-wrapper {
  display: grid;
  grid-template-columns: 1.25fr 0.75fr;
  gap: 30px;
  align-items: start;
}

.content-card,
.video-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 35px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
}

.card-header {
  text-align: center;
  margin-bottom: 30px;
}

.loading-icon {
  width: 78px;
  height: 78px;
  margin: 0 auto 18px;
  border-radius: 50%;
  background: #f6f3fb;
  display: flex;
  align-items: center;
  justify-content: center;
}

.loading-icon i {
  font-size: 2.2rem;
  color: #5c4d82;
}

.loading-icon.success {
  background: #f0f9eb;
}

.loading-icon.success i {
  color: #67C23A;
}

.page-title {
  font-size: 2rem;
  color: #3f335f;
  margin: 0 0 10px;
}

.page-subtitle {
  color: #8c7baa;
  margin: 0;
  line-height: 1.6;
}

.progress-section {
  margin-bottom: 25px;
  padding: 22px;
  border-radius: 18px;
  background: #faf9fc;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #5c4d82;
  font-weight: 600;
  margin-bottom: 18px;
}

.progress-content {
  width: 100%;
}

.work-text,
.segment-text {
  margin-top: 14px;
  color: #6d5c8d;
  font-size: 0.95rem;
  line-height: 1.6;
}

.realtime-section {
  margin-bottom: 25px;
  padding: 22px;
  border-radius: 18px;
  background: #f8fbff;
  border: 1px solid #d9ecff;
}

.realtime-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 18px;
}

.realtime-header h3 {
  margin: 0 0 6px;
  color: #3b6f9e;
  font-size: 1.15rem;
}

.realtime-header p {
  margin: 0;
  color: #6f8fac;
  font-size: 0.9rem;
}

.stop-button {
  border: none;
  background: #f56c6c;
  color: #ffffff;
  border-radius: 999px;
  padding: 9px 18px;
  cursor: pointer;
  font-size: 0.92rem;
  transition: all 0.2s ease;
}

.stop-button:hover {
  opacity: 0.9;
  transform: translateY(-1px);
}

.realtime-content {
  max-height: 520px;
  overflow-y: auto;
  background: #ffffff;
  border-radius: 14px;
  padding: 22px;
  border: 1px solid #e6f1ff;
  color: #2f3f56;
  line-height: 1.85;
}

.realtime-content :deep(img),
.markdown-body :deep(img) {
  max-width: 100%;
  display: block;
  margin: 16px auto;
  border-radius: 12px;
  box-shadow: 0 8px 24px rgba(92, 77, 130, 0.18);
}

.realtime-content :deep(h2) {
  color: #3f335f;
  border-bottom: 1px solid #e8e0f0;
  padding-bottom: 8px;
}

.realtime-content :deep(p) {
  margin: 10px 0;
}

.empty-realtime {
  padding: 28px;
  text-align: center;
  color: #7c98b6;
  background: #ffffff;
  border-radius: 14px;
}

.tips-section {
  padding: 22px;
  border-radius: 18px;
  background: #fffaf0;
}

.tips-section h3 {
  margin: 0 0 16px;
  color: #5c4d82;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.tip-item {
  background: #ffffff;
  padding: 16px;
  border-radius: 14px;
  text-align: center;
  color: #6d5c8d;
}

.tip-item i {
  font-size: 1.5rem;
  color: #5c4d82;
}

.tip-item p {
  margin: 8px 0 0;
  font-size: 0.9rem;
  line-height: 1.5;
}

.video-header {
  margin-bottom: 20px;
}

.video-title {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #3f335f;
  margin: 0 0 8px;
}

.video-subtitle {
  color: #8c7baa;
  margin: 0;
}

.video-wrapper video {
  width: 100%;
  border-radius: 16px;
  background: #000000;
}

.video-info {
  margin-top: 16px;
  color: #6d5c8d;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.video-status {
  margin-top: 18px;
}

.status-indicator {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  color: #67C23A;
  font-weight: 600;
}

.status-indicator.processing {
  color: #5c4d82;
}

@media (max-width: 1100px) {
  .main-content-wrapper {
    grid-template-columns: 1fr;
  }

  .steps-wrapper {
    flex-wrap: wrap;
    gap: 20px;
  }

  .step-connector {
    display: none;
  }
}

@media (max-width: 768px) {
  .generating-container {
    padding: 20px 12px;
  }

  .steps-container,
  .content-card,
  .video-card {
    padding: 22px;
  }

  .tips-grid {
    grid-template-columns: 1fr;
  }

  .realtime-header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>