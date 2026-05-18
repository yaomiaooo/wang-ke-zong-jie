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
    const uploadUrl = 'http://127.0.0.1:8001/video_upload/'  // 后端上传接口
    const uploading = ref(false)
    const uploadProgress = ref(0)

    const handleProgress = (event) => {
      uploading.value = true
      uploadProgress.value = Math.round(event.percent)
    }
    const handleSuccess = (res) => {
      uploading.value = false
      router.push('/branch')  // 上传成功后跳转
    }

    return { uploadUrl, uploading, uploadProgress, handleProgress, handleSuccess }
  }
}
</script>

<style scoped>
.home-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 0;
}

.hero-section {
  padding: 60px 20px;
  text-align: center;
  color: white;
}

.hero-content {
  max-width: 800px;
  margin: 0 auto;
}

.hero-title {
  font-size: 3rem;
  font-weight: bold;
  margin-bottom: 20px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.hero-title i {
  margin-right: 15px;
  color: #ffd700;
}

.hero-subtitle {
  font-size: 1.2rem;
  opacity: 0.9;
  margin-bottom: 0;
  line-height: 1.6;
}

.upload-section {
  padding: 40px 20px;
  display: flex;
  justify-content: center;
}

.upload-card {
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
  max-width: 600px;
  width: 100%;
}

.upload-area {
  border: 3px dashed #d9d9d9;
  border-radius: 15px;
  transition: all 0.3s ease;
}

.upload-area:hover {
  border-color: #409EFF;
  background-color: #f8f9ff;
}

.upload-content {
  padding: 60px 40px;
  text-align: center;
}

.upload-icon {
  font-size: 4rem;
  color: #409EFF;
  margin-bottom: 20px;
}

.upload-text h3 {
  font-size: 1.5rem;
  color: #333;
  margin-bottom: 10px;
}

.upload-text p {
  color: #666;
  margin-bottom: 8px;
}

.upload-hint {
  font-size: 0.9rem;
  color: #999;
}

.progress-section {
  margin-top: 30px;
  padding: 20px;
  background-color: #f8f9fa;
  border-radius: 10px;
}

.progress-text {
  text-align: center;
  margin-bottom: 15px;
  color: #666;
  font-weight: 500;
}

.features-section {
  padding: 60px 20px;
  background: white;
  text-align: center;
}

.features-section h2 {
  font-size: 2.5rem;
  color: #333;
  margin-bottom: 50px;
  font-weight: bold;
}

.features-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 30px;
  max-width: 1200px;
  margin: 0 auto;
}

.feature-card {
  padding: 40px 20px;
  border-radius: 15px;
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  box-shadow: 0 10px 30px rgba(0,0,0,0.1);
  transition: transform 0.3s ease;
}

.feature-card:hover {
  transform: translateY(-5px);
}

.feature-card i {
  font-size: 3rem;
  color: #667eea;
  margin-bottom: 20px;
}

.feature-card h3 {
  font-size: 1.3rem;
  color: #333;
  margin-bottom: 15px;
  font-weight: 600;
}

.feature-card p {
  color: #666;
  line-height: 1.6;
}
</style>
