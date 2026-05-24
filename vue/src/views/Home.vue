<template>
  <div class="home-container">
    <!-- 装饰元素 -->
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    <div class="decoration decoration-3"></div>
    
    <div class="home-content">
      <!-- 左侧功能介绍区域 -->
      <div class="intro-section">
        <div class="brand-badge">
          <span class="brand-text">智能网课总结</span>
        </div>
        
        <h1 class="intro-title">
          Turn your lectures
          <br>
          <span class="highlight">into insights.</span>
        </h1>
        
        <p class="intro-subtitle">
          上传您的教学视频，我们将自动识别并总结板书内容，
          生成结构化的学习笔记，让学习更高效。
        </p>
        
        <div class="feature-tags">
          <span class="tag tag-purple">视频分析</span>
          <span class="tag tag-green">智能笔记</span>
          <span class="tag tag-salmon">要点提取</span>
        </div>
        
        <div class="steps-list">
          <h3>使用步骤</h3>
          <div class="step-item">
            <span class="step-num">1</span>
            <span>上传网课视频</span>
          </div>
          <div class="step-item">
            <span class="step-num">2</span>
            <span>AI 自动分析板书</span>
          </div>
          <div class="step-item">
            <span class="step-num">3</span>
            <span>生成讲义并下载</span>
          </div>
        </div>
      </div>
      
      <!-- 右侧上传区域 -->
      <div class="upload-section">
        <div class="upload-card">
          <div class="card-header">
            <h2>开始上传</h2>
            <p>上传您的网课视频</p>
          </div>
          
          <el-upload
            ref="uploadRef"
            class="upload-area"
            drag
            :action="uploadUrl"
            :on-progress="handleProgress"
            :on-success="handleSuccess"
            :on-error="handleError"
            :before-upload="beforeUpload"
            :show-file-list="false"
            :key="uploadKey"
          >
            <div class="upload-content">
              <div class="upload-icon-wrapper">
                <i class="el-icon-upload upload-icon"></i>
              </div>
              <div class="upload-text">
                <h3>拖拽视频文件到此处</h3>
                <p>或点击选择文件上传</p>
              </div>
              <div class="upload-hint">
                <span>支持 MP4、MOV、AVI 格式</span>
                <span>最大支持 2GB</span>
              </div>
            </div>
          </el-upload>
          
          <div v-if="uploading" class="progress-section">
            <div class="progress-info">
              <span class="progress-label">正在上传...</span>
              <span class="progress-percent">{{ uploadProgress }}%</span>
            </div>
            <el-progress 
              :percentage="uploadProgress" 
              :stroke-width="10"
              :text-inside="true"
              status="exception"
            />
          </div>
          
          <div class="upload-tips">
            <div class="tip-item">
              <i class="el-icon-circle-check"></i>
              <span>视频仅用于本地处理</span>
            </div>
            <div class="tip-item">
              <i class="el-icon-circle-check"></i>
              <span>隐私安全，不会上传到第三方</span>
            </div>
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
import { ElMessage } from 'element-plus'

export default {
  setup() {
    const router = useRouter()
    const globalStore = useGlobalStore()
    const uploadRef = ref(null)
    const uploadKey = ref(0)
    
    const uploadUrl = 'http://127.0.0.1:8001/video_upload/'
    const uploading = ref(false)
    const uploadProgress = ref(0)

    const resetAllState = async () => {
      uploading.value = false
      uploadProgress.value = 0
      uploadKey.value++
      
      await globalStore.fullReset()
      
      if (uploadRef.value) {
        uploadRef.value.clearFiles()
      }
    }

    const beforeUpload = async (file) => {
      await resetAllState()
      globalStore.setCurrentVideoName(file.name)
      return true
    }

    const handleProgress = (event) => {
      uploading.value = true
      uploadProgress.value = Math.round(event.percent)
      globalStore.setUploadProgress(Math.round(event.percent))
      globalStore.setUploading(true)
    }
    
    const handleSuccess = (res) => {
      uploading.value = false
      uploadProgress.value = 0
      globalStore.setUploading(false)
      globalStore.setProcessingStarted(true)
      ElMessage.success('视频上传成功！')
      router.push('/branch')
    }
    
    const handleError = (err) => {
      uploading.value = false
      uploadProgress.value = 0
      globalStore.setUploading(false)
      ElMessage.error('视频上传失败，请重试')
      console.error('上传错误:', err)
    }

    onMounted(async () => {
      await resetAllState()
    })

    onBeforeUnmount(() => {
      uploading.value = false
      uploadProgress.value = 0
    })

    return { 
      router,
      uploadRef,
      uploadKey,
      uploadUrl, 
      uploading, 
      uploadProgress, 
      beforeUpload,
      handleProgress, 
      handleSuccess,
      handleError
    }
  }
}
</script>

<style scoped>
.home-container {
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
  width: 500px;
  height: 500px;
  background: #5c4d82;
  top: -150px;
  left: -150px;
}

.decoration-2 {
  width: 400px;
  height: 400px;
  background: #9b8dc7;
  bottom: -100px;
  right: -100px;
}

.decoration-3 {
  width: 250px;
  height: 250px;
  background: #7eb89e;
  top: 40%;
  right: 5%;
}

.home-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 80px;
  max-width: 1200px;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* 左侧功能介绍区 */
.intro-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  background: #ffffff;
  padding: 14px 28px;
  border-radius: 50px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
  margin-bottom: 40px;
  width: fit-content;
}

.brand-icon {
  font-size: 1.5rem;
}

.brand-text {
  font-weight: 700;
  font-size: 1.125rem;
  color: #2d2d2d;
}

.intro-title {
  font-family: 'Georgia', serif;
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin: 0 0 28px 0;
  color: #2d2d2d;
}

.highlight {
  color: #5c4d82;
}

.intro-subtitle {
  font-size: 1.125rem;
  color: #5c5c5c;
  line-height: 1.8;
  margin: 0 0 36px 0;
  max-width: 500px;
}

.feature-tags {
  display: flex;
  gap: 14px;
  flex-wrap: wrap;
  margin-bottom: 50px;
}

.tag {
  padding: 12px 22px;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 600;
}

.tag-purple {
  background: rgba(92, 77, 130, 0.15);
  color: #5c4d82;
}

.tag-green {
  background: rgba(126, 184, 158, 0.2);
  color: #4a7c63;
}

.tag-salmon {
  background: rgba(235, 150, 150, 0.2);
  color: #b56b6b;
}

/* 使用步骤 */
.steps-list {
  background: #ffffff;
  padding: 28px 32px;
  border-radius: 20px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06);
}

.steps-list h3 {
  font-size: 1.1rem;
  font-weight: 700;
  color: #2d2d2d;
  margin: 0 0 20px 0;
}

.step-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 0;
  color: #5c5c5c;
  font-size: 1rem;
}

.step-num {
  width: 32px;
  height: 32px;
  background: #5c4d82;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 0.9rem;
  flex-shrink: 0;
}

/* 右侧上传区域 */
.upload-section {
  display: flex;
  align-items: center;
}

.upload-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
}

.card-header {
  text-align: center;
  margin-bottom: 36px;
}

.card-header h2 {
  font-family: 'Georgia', serif;
  font-size: 2rem;
  margin: 0 0 10px 0;
  color: #2d2d2d;
}

.card-header p {
  color: #888;
  margin: 0;
  font-size: 1rem;
}

/* 上传区域 */
.upload-area {
  border: 3px dashed #d4c8e0;
  border-radius: 20px;
  transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
  background: linear-gradient(135deg, #faf9fc 0%, #f5f0fa 100%);
  cursor: pointer;
}

.upload-area:hover {
  border-color: #5c4d82;
  background: linear-gradient(135deg, #f0ecf7 0%, #e8e0f5 100%);
  transform: translateY(-4px);
  box-shadow: 0 12px 40px rgba(92, 77, 130, 0.2);
}

.upload-area:hover .upload-icon-wrapper {
  background: #5c4d82;
  transform: scale(1.1);
}

.upload-area:hover .upload-icon {
  color: #ffffff;
}

.upload-content {
  padding: 50px 30px;
  text-align: center;
}

.upload-icon-wrapper {
  width: 80px;
  height: 80px;
  background: rgba(92, 77, 130, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
  transition: all 0.4s ease;
}

.upload-icon {
  font-size: 2.5rem;
  color: #5c4d82;
  transition: all 0.4s ease;
}

.upload-text h3 {
  font-size: 1.3rem;
  color: #2d2d2d;
  margin-bottom: 10px;
  font-weight: 600;
}

.upload-text p {
  color: #888;
  margin: 0;
  font-size: 1rem;
}

.upload-hint {
  display: flex;
  flex-direction: column;
  gap: 6px;
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px dashed #d4c8e0;
}

.upload-hint span {
  font-size: 0.85rem;
  color: #aaa;
}

/* 进度条 */
.progress-section {
  margin-top: 28px;
  padding: 24px;
  background: #faf9fc;
  border-radius: 16px;
}

.progress-info {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14px;
}

.progress-label {
  color: #5c4d82;
  font-weight: 600;
}

.progress-percent {
  color: #5c4d82;
  font-weight: 700;
}

/* 上传提示 */
.upload-tips {
  margin-top: 28px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #888;
  font-size: 0.9rem;
}

.tip-item i {
  color: #7eb89e;
  font-size: 1.1rem;
}

/* 响应式 */
@media (max-width: 1000px) {
  .home-content {
    grid-template-columns: 1fr;
    gap: 50px;
  }
  
  .intro-section {
    text-align: center;
    align-items: center;
  }
  
  .intro-subtitle {
    max-width: none;
  }
  
  .steps-list {
    width: 100%;
    max-width: 450px;
  }
  
  .decoration {
    display: none;
  }
}

@media (max-width: 600px) {
  .home-container {
    padding: 30px 15px;
  }
  
  .intro-title {
    font-size: 2.5rem;
  }
  
  .upload-card {
    padding: 32px 24px;
  }
  
  .upload-content {
    padding: 36px 20px;
  }
}
</style>
