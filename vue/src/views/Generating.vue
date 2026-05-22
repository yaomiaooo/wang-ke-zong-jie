<template>
  <div class="generating-container">
    <!-- 装饰元素 -->
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
              <p>提取关键帧并识别板书区域</p>
            </div>
          </div>
          
          <div class="step-connector" :class="{ active: progress > 30 }"></div>
          
          <div class="step-item" :class="{ active: progress > 30, completed: progress > 60 }">
            <div class="step-icon">
              <i class="el-icon-view"></i>
            </div>
            <div class="step-content">
              <h3>内容识别</h3>
              <p>使用OCR技术识别板书文字</p>
            </div>
          </div>
          
          <div class="step-connector" :class="{ active: progress > 60 }"></div>
          
          <div class="step-item" :class="{ active: progress > 60, completed: progress >= 100 }">
            <div class="step-icon">
              <i class="el-icon-edit"></i>
            </div>
            <div class="step-content">
              <h3>智能整理</h3>
              <p>整理和结构化识别内容</p>
            </div>
          </div>
          
          <div class="step-connector" :class="{ active: progress >= 100 }"></div>
          
          <div class="step-item" :class="{ active: progress >= 100 }">
            <div class="step-icon">
              <i class="el-icon-document"></i>
            </div>
            <div class="step-content">
              <h3>生成总结</h3>
              <p>生成最终的内容总结</p>
            </div>
          </div>
        </div>
      </div>

      <!-- 主内容区域 -->
      <div class="main-content-wrapper">
        <!-- 左侧主内容区域 -->
        <div class="main-section">
          <div class="content-card">
            <div class="card-header">
              <div class="loading-icon">
                <i class="el-icon-loading"></i>
              </div>
              <h1 class="page-title">正在处理您的视频</h1>
              <p class="page-subtitle">请耐心等待，我们正在为您生成精彩的内容总结</p>
            </div>

            <!-- 视频处理进度 -->
            <div class="progress-section">
              <div class="progress-header">
                <i class="el-icon-video-camera"></i>
                <span>视频处理进度</span>
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
              </div>
            </div>

            <!-- 音频识别进度 -->
            <div class="progress-section" v-if="useAudio">
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
                  color="#67C23A"
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
                  <p>处理时间取决于视频长度和复杂度</p>
                </div>
                <div class="tip-item">
                  <i class="el-icon-cpu"></i>
                  <p>我们正在使用AI技术进行智能分析</p>
                </div>
                <div class="tip-item">
                  <i class="el-icon-check"></i>
                  <p>完成后将自动跳转到结果页面</p>
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
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'

export default {
  setup() {
    const router = useRouter()
    const globalStore = useGlobalStore()
    const videoPlayer = ref(null)
    const videoUrl = ref('')
    const videoDuration = ref(0)

    const useAudio = computed(() => globalStore.use_audio)

    const progress = ref(0)
    const work = ref('')
    const audioProgress = ref(0)
    const audioWork = ref('')
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

    const checkProgress = () => {
      fetch('http://127.0.0.1:8001/get_progress')
        .then(res => res.json())
        .then(data => {
          progress.value = data.progress
          work.value = data.work || '' 
        })
        .catch(err => {
          console.error('进度获取失败:', err)
        })
      
      if (useAudio.value) {
        fetch('http://127.0.0.1:8002/get_progress')
          .then(res => res.json())
          .then(data => {
            audioProgress.value = data.percent
            audioWork.value = data.message || ''
          })
          .catch(err => console.error('音频进度获取失败:', err))
      }

      if (progress.value >= 100 && (!useAudio.value || audioProgress.value >= 100)) {
        clearInterval(timer)
        setTimeout(() => router.push('/result'), 1000)
      }
    }

    onMounted(() => {
      loadVideo()
      timer = setInterval(checkProgress, 1000)
    })

    onBeforeUnmount(() => {
      clearInterval(timer)
    })

    return { 
      progress, 
      work,
      audioProgress,
      audioWork,
      useAudio,
      videoPlayer,
      videoUrl,
      videoDuration,
      formatDuration,
      onVideoLoaded
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

/* 装饰元素 */
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

/* 步骤条 */
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
  font-size: 0.85rem;
  color: #999;
  margin: 0;
  line-height: 1.4;
  transition: all 0.3s ease;
}

.step-item.active .step-content p {
  color: #5c5c5c;
}

/* 步骤连接线 */
.step-connector {
  flex: 1;
  height: 3px;
  background: transparent;
  border-top: 3px dashed #e8e0f0;
  margin: 0 15px;
  margin-top: -45px;
  transition: all 0.3s ease;
}

.step-connector.active {
  border-top-color: #5c4d82;
}

/* 主内容区域 */
.main-content-wrapper {
  display: grid;
  grid-template-columns: 1fr 0.7fr;
  gap: 40px;
}

/* 左侧主内容区域 */
.main-section {
  display: flex;
  align-items: flex-start;
}

.content-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 50px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
}

.card-header {
  text-align: center;
  margin-bottom: 45px;
}

.loading-icon {
  font-size: 3.5rem;
  margin-bottom: 20px;
  animation: spin 2s linear infinite;
  color: #5c4d82;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.page-title {
  font-family: 'Georgia', serif;
  font-size: 2.4rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: #2d2d2d;
}

.page-subtitle {
  font-size: 1.15rem;
  color: #5c5c5c;
  margin: 0;
}

/* 进度区域 */
.progress-section {
  margin-bottom: 30px;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.3rem;
  font-weight: 600;
  color: #2d2d2d;
}

.progress-header i {
  color: #5c4d82;
  font-size: 1.4rem;
}

.progress-content {
  background: #faf9fc;
  border-radius: 16px;
  padding: 25px;
  border: 2px solid #e8e0f0;
}

.progress-content.audio {
  border-color: #c8e6c9;
}

.work-text {
  margin-top: 15px;
  color: #5c5c5c;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 0.95rem;
}

.work-text i {
  color: #5c4d82;
}

/* 提示区域 */
.tips-section {
  background: #faf9fc;
  border-radius: 16px;
  padding: 30px;
  border: 2px solid #e8e0f0;
}

.tips-section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d2d2d;
}

.tips-section h3 i {
  color: #5c4d82;
  font-size: 1.3rem;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 15px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 15px;
  background: #ffffff;
  border-radius: 12px;
}

.tip-item i {
  font-size: 1.3rem;
  color: #5c4d82;
  flex-shrink: 0;
}

.tip-item p {
  margin: 0;
  font-size: 0.9rem;
  line-height: 1.4;
  color: #5c5c5c;
}

/* 右侧视频预览区域 */
.right-section {
  display: flex;
  align-items: flex-start;
}

.video-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 35px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
  display: flex;
  flex-direction: column;
}

.video-header {
  margin-bottom: 25px;
}

.video-title {
  font-family: 'Georgia', serif;
  font-size: 1.6rem;
  font-weight: 600;
  color: #2d2d2d;
  margin: 0 0 8px 0;
  display: flex;
  align-items: center;
  gap: 10px;
}

.video-title i {
  color: #5c4d82;
}

.video-subtitle {
  font-size: 0.95rem;
  color: #5c5c5c;
  margin: 0;
}

.video-wrapper {
  background: #1a1a1a;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 20px;
  position: relative;
  width: 100%;
  aspect-ratio: 16 / 9;
  flex-shrink: 0;
}

.video-wrapper video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-info {
  display: flex;
  justify-content: center;
  margin-bottom: 20px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #5c5c5c;
  font-size: 0.95rem;
}

.info-item i {
  color: #5c4d82;
}

.video-status {
  background: #faf9fc;
  border-radius: 12px;
  padding: 20px;
  border: 2px solid #e8e0f0;
}

.status-indicator {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  font-size: 1rem;
  color: #5c5c5c;
}

.status-indicator.processing {
  color: #5c4d82;
}

.status-indicator i {
  font-size: 1.2rem;
}

.status-indicator.processing i {
  animation: spin 2s linear infinite;
}

.status-indicator:not(.processing) i {
  color: #52c41a;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content-wrapper {
    grid-template-columns: 1fr;
    max-width: 700px;
    margin: 0 auto;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
  
  .video-card {
    max-width: 100%;
  }
  
  .steps-wrapper {
    flex-wrap: wrap;
    justify-content: center;
    gap: 20px;
  }
  
  .step-connector {
    display: none;
  }
  
  .step-item {
    width: 140px;
  }
}

@media (max-width: 768px) {
  .generating-container {
    padding: 20px 15px;
  }
  
  .steps-container {
    padding: 25px 20px;
  }
  
  .step-item {
    width: 120px;
  }
  
  .step-icon {
    width: 55px;
    height: 55px;
  }
  
  .step-icon i {
    font-size: 1.4rem;
  }
  
  .step-content h3 {
    font-size: 0.9rem;
  }
  
  .step-content p {
    font-size: 0.75rem;
  }
  
  .content-card {
    padding: 30px 25px;
  }
  
  .page-title {
    font-size: 1.9rem;
  }
  
  .loading-icon {
    font-size: 2.5rem;
  }
  
  .video-card {
    padding: 25px;
  }
}
</style>
