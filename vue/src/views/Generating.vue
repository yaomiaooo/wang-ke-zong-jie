<template>
  <div class="generating-container">
    <div class="content-wrapper">
      <div class="header-section">
        <div class="loading-icon">
          <i class="el-icon-loading"></i>
        </div>
        <h1 class="page-title">正在处理您的视频</h1>
        <p class="page-subtitle">请耐心等待，我们正在为您生成精彩的内容总结</p>
      </div>

      <div class="progress-card">
        <div class="progress-section main-progress">
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

        <div v-if="useAudio" class="progress-section audio-progress">
          <div class="progress-header">
            <i class="el-icon-microphone"></i>
            <span>音频识别进度</span>
          </div>
          <div class="progress-content">
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
      </div>

      <div class="status-cards">
        <div class="status-card" :class="{ active: progress > 0 }">
          <i class="el-icon-video-camera"></i>
          <h3>视频分析</h3>
          <p>提取关键帧并识别板书区域</p>
        </div>
        <div class="status-card" :class="{ active: progress > 30 }">
          <i class="el-icon-view"></i>
          <h3>内容识别</h3>
          <p>使用OCR技术识别板书文字</p>
        </div>
        <div class="status-card" :class="{ active: progress > 60 }">
          <i class="el-icon-edit"></i>
          <h3>智能整理</h3>
          <p>整理和结构化识别内容</p>
        </div>
        <div class="status-card" :class="{ active: progress >= 100 }">
          <i class="el-icon-document"></i>
          <h3>生成总结</h3>
          <p>生成最终的内容总结</p>
        </div>
      </div>

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
</template>

<script>
import { ref, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import { computed } from 'vue'

export default {
  setup() {
    const router = useRouter()
    const globalStore = useGlobalStore()

    const useAudio = computed(() => globalStore.use_audio)

    const progress = ref(0)
    const work = ref('')
    const audioProgress = ref(0)
    const audioWork = ref('')
    let timer = null

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
      
      if (useAudio) {
        fetch('http://127.0.0.1:8002/get_progress')
          .then(res => res.json())
          .then(data => {
            audioProgress.value = data.percent
            audioWork.value = data.message || ''
          })
          .catch(err => console.error('音频进度获取失败:', err))
      }

      if (progress.value >= 100 && (!useAudio || audioProgress.value >= 100)) {
        clearInterval(timer)
        setTimeout(() => router.push('/result'), 1000)
      }
    }

    onMounted(() => {
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
      useAudio
    }
  }
}
</script>

<style scoped>
.generating-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.content-wrapper {
  max-width: 1000px;
  margin: 0 auto;
}

.header-section {
  text-align: center;
  margin-bottom: 50px;
  color: white;
}

.loading-icon {
  font-size: 4rem;
  margin-bottom: 20px;
  animation: spin 2s linear infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.page-title {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 15px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.page-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
}

.progress-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  margin-bottom: 40px;
}

.progress-section {
  margin-bottom: 30px;
}

.progress-section:last-child {
  margin-bottom: 0;
}

.progress-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
}

.progress-header i {
  color: #667eea;
  font-size: 1.4rem;
}

.audio-progress .progress-header i {
  color: #67C23A;
}

.progress-content {
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
  padding: 25px;
}

.work-text {
  margin-top: 15px;
  color: #666;
  font-style: italic;
  display: flex;
  align-items: center;
  gap: 8px;
}

.work-text i {
  color: #409EFF;
}

.status-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 40px;
}

.status-card {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 15px;
  padding: 30px 20px;
  text-align: center;
  color: white;
  transition: all 0.3s ease;
  border: 2px solid transparent;
}

.status-card.active {
  background: rgba(255, 255, 255, 0.2);
  border-color: #ffd700;
  transform: translateY(-5px);
}

.status-card i {
  font-size: 2.5rem;
  margin-bottom: 15px;
  color: #ffd700;
}

.status-card h3 {
  font-size: 1.2rem;
  margin-bottom: 10px;
  font-weight: 600;
}

.status-card p {
  font-size: 0.9rem;
  opacity: 0.8;
  margin: 0;
  line-height: 1.4;
}

.tips-section {
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  padding: 30px;
  color: white;
}

.tips-section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
  font-size: 1.3rem;
  font-weight: 600;
}

.tips-section h3 i {
  color: #ffd700;
  font-size: 1.4rem;
}

.tips-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 20px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 15px;
  padding: 15px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 10px;
}

.tip-item i {
  font-size: 1.5rem;
  color: #ffd700;
  flex-shrink: 0;
}

.tip-item p {
  margin: 0;
  line-height: 1.4;
}

@media (max-width: 768px) {
  .progress-card {
    padding: 25px 20px;
  }
  
  .status-cards {
    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
    gap: 15px;
  }
  
  .status-card {
    padding: 20px 15px;
  }
  
  .tips-grid {
    grid-template-columns: 1fr;
  }
}
</style>
