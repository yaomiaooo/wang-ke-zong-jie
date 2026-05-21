<template>
  <div class="home-container">
    <div class="hero-section">
      <div class="hero-content">
        <h1 class="hero-title">
          <i class="el-icon-video-camera"></i>
          智能网课总结系统
        </h1>
        <p class="hero-subtitle">
          上传您的教学视频，我们将自动识别并总结板书内容
        </p>
      </div>
    </div>
    
    <div class="upload-section">
      <div class="upload-card">
        <el-upload
          class="upload-area"
          drag
          :action="uploadUrl"
          :on-progress="handleProgress"
          :on-success="handleSuccess"
          :show-file-list="false"
        >
          <div class="upload-content">
            <i class="el-icon-upload upload-icon"></i>
            <div class="upload-text">
              <h3>上传视频文件</h3>
              <p>将视频文件拖到此处，或点击选择文件</p>
              <p class="upload-hint"></p>
            </div>
          </div>
        </el-upload>
        
        <div v-if="uploading" class="progress-section">
          <p class="progress-text">正在上传文件...</p>
          <el-progress 
            :percentage="uploadProgress" 
            :stroke-width="8"
            :text-inside="true"
          />
        </div>
      </div>
    </div>
    
    <div class="features-section">
      <h2>功能特点</h2>
      <div class="features-grid">
        <div class="feature-card">
          <i class="el-icon-view"></i>
          <h3>智能识别</h3>
          <p>自动识别板书区域和内容</p>
        </div>
        <div class="feature-card">
          <i class="el-icon-edit"></i>
          <h3>手动调整</h3>
          <p>支持手动调整识别区域</p>
        </div>
        <div class="feature-card">
          <i class="el-icon-document"></i>
          <h3>智能总结</h3>
          <p>生成结构化的内容总结</p>
        </div>
        <div class="feature-card">
          <i class="el-icon-download"></i>
          <h3>导出PDF</h3>
          <p>一键导出为PDF文档</p>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const router = useRouter()
    
    const uploadUrl = 'http://127.0.0.1:8001/video_upload/'
    const uploading = ref(false)
    const uploadProgress = ref(0)

    const handleProgress = (event) => {
      uploading.value = true
      uploadProgress.value = Math.round(event.percent)
    }
    const handleSuccess = (res) => {
      uploading.value = false
      router.push('/branch')
    }

    return { 
      router,
      uploadUrl, 
      uploading, 
      uploadProgress, 
      handleProgress, 
      handleSuccess
    }
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background-color: #c4b5e0;
  padding: 0;
}

.hero-section {
  padding: 80px 20px 60px;
  text-align: center;
  color: #2d2d2d;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 2.8rem;
  font-weight: 600;
  margin-bottom: 20px;
  letter-spacing: -0.5px;
}

.hero-title i {
  margin-right: 15px;
  color: #5c4d82;
}

.hero-subtitle {
  font-size: 1.3rem;
  color: #5c5c5c;
  margin-bottom: 0;
  line-height: 1.7;
  font-weight: 400;
}

.upload-section {
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}

.upload-card {
  background: #5c4d82;
  border-radius: 24px;
  padding: 50px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
  max-width: 600px;
  width: 100%;
}

.upload-area {
  border: 3px dashed rgba(255, 255, 255, 0.3);
  border-radius: 16px;
  transition: all 0.3s ease;
  background: rgba(255, 255, 255, 0.05);
}

.upload-area:hover {
  border-color: rgba(255, 255, 255, 0.6);
  background-color: rgba(255, 255, 255, 0.1);
}

.upload-content {
  padding: 60px 40px;
  text-align: center;
}

.upload-icon {
  font-size: 4rem;
  color: #ffffff;
  margin-bottom: 20px;
}

.upload-text h3 {
  font-size: 1.5rem;
  color: #ffffff;
  margin-bottom: 12px;
  font-weight: 600;
}

.upload-text p {
  color: rgba(255, 255, 255, 0.8);
  margin-bottom: 8px;
  font-weight: 400;
}

.upload-hint {
  font-size: 0.9rem;
  color: rgba(255, 255, 255, 0.6);
}

.progress-section {
  margin-top: 30px;
  padding: 25px;
  background-color: rgba(255, 255, 255, 0.1);
  border-radius: 12px;
}

.progress-text {
  text-align: center;
  margin-bottom: 15px;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 500;
}

.features-section {
  padding: 70px 20px;
  background: #e8e8e8;
  text-align: center;
}

.features-section h2 {
  font-size: 2.2rem;
  color: #2d2d2d;
  margin-bottom: 50px;
  font-weight: 600;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
  gap: 24px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  padding: 45px 25px;
  border-radius: 20px;
  background: #ffffff;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.08);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-6px);
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.12);
}

.feature-card i {
  font-size: 2.8rem;
  color: #5c4d82;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 1.3rem;
  color: #2d2d2d;
  margin-bottom: 15px;
  font-weight: 600;
}

.feature-card p {
  color: #5c5c5c;
  line-height: 1.6;
}

@media (max-width: 768px) {
  .hero-title {
    font-size: 2rem;
  }
  
  .hero-subtitle {
    font-size: 1.1rem;
  }
  
  .upload-card {
    padding: 30px 20px;
  }
  
  .upload-content {
    padding: 40px 20px;
  }
  
  .features-grid {
    gap: 20px;
  }
  
  .feature-card {
    padding: 30px 20px;
  }
}
</style>
