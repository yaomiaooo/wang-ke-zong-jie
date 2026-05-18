<template>
  <div class="branch-container">
    <div class="content-wrapper">
      <div class="header-section">
        <h1 class="page-title">
          <i class="el-icon-setting"></i>
          板书区域设置
        </h1>
        <p class="page-subtitle">选择是否需要固定板书识别区域</p>
      </div>

      <div class="form-card">
        <el-form :model="form" label-position="top" class="branch-form">
          <div class="form-section">
            <el-form-item label="板书区域固定" class="switch-item">
              <div class="switch-wrapper">
                <el-switch 
                  v-model="form.fixed" 
                  active-text="是" 
                  inactive-text="否"
                  size="large"
                />
                <div class="switch-description">
                  {{ form.fixed ? '将手动选择板书区域' : '使用完整画面识别' }}
                </div>
              </div>
            </el-form-item>

            <div class="explanation-card">
              <div class="explanation-header">
                <i class="el-icon-info"></i>
                <span>功能说明</span>
              </div>
              <div class="explanation-content">
                <div class="explanation-item">
                  <strong>固定区域模式：</strong>
                  <p>用户可以控制视频只有部分区域被识别，防止无用信息（如教室里的标语等）干扰结果。适合板书位置相对固定的场景。</p>
                </div>
                <div class="explanation-item">
                  <strong>完整画面模式：</strong>
                  <p>后续的自动识别将直接使用完整画面，适合板书位置变化较大的场景。</p>
                </div>
              </div>
            </div>
          </div>

          <div class="button-section">
            <el-button @click="onPrev" size="large" class="nav-button">
              <i class="el-icon-arrow-left"></i>
              上一步
            </el-button>
            <el-button type="primary" @click="onNext" size="large" class="nav-button primary">
              下一步
              <i class="el-icon-arrow-right"></i>
            </el-button>
          </div>
        </el-form>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'

export default {
  setup() {
    const router = useRouter()
    const form = ref({ fixed: false })
    const globalStore = useGlobalStore()
    const onPrev = () => {
      router.back()
    }
    const onNext = () => {
      globalStore.setAdvanced(form.value.fixed)
      if (form.value.fixed) {
        router.push('/annotation')
      } else {
        router.push('/information')
      }
    }

    return { form, onPrev, onNext }
  }
}
</script>

<style scoped>
.branch-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.content-wrapper {
  max-width: 800px;
  width: 100%;
}

.header-section {
  text-align: center;
  margin-bottom: 40px;
  color: white;
}

.page-title {
  font-size: 2.5rem;
  font-weight: bold;
  margin-bottom: 15px;
  text-shadow: 0 2px 4px rgba(0,0,0,0.3);
}

.page-title i {
  margin-right: 15px;
  color: #ffd700;
}

.page-subtitle {
  font-size: 1.1rem;
  opacity: 0.9;
  margin: 0;
}

.form-card {
  background: white;
  border-radius: 20px;
  padding: 50px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.form-section {
  margin-bottom: 40px;
}

.switch-item {
  margin-bottom: 30px;
}

.switch-wrapper {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 15px;
}

.switch-description {
  font-size: 1rem;
  color: #666;
  font-weight: 500;
}

.explanation-card {
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
  padding: 30px;
  border-left: 4px solid #667eea;
}

.explanation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.explanation-header i {
  color: #667eea;
  font-size: 1.3rem;
}

.explanation-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.explanation-item strong {
  color: #333;
  display: block;
  margin-bottom: 8px;
}

.explanation-item p {
  color: #666;
  line-height: 1.6;
  margin: 0;
}

.button-section {
  display: flex;
  justify-content: space-between;
  gap: 20px;
}

.nav-button {
  flex: 1;
  height: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.nav-button.primary {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
}

.nav-button.primary:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.nav-button i {
  margin: 0 8px;
}

@media (max-width: 768px) {
  .form-card {
    padding: 30px 20px;
  }
  
  .button-section {
    flex-direction: column;
  }
}
</style>
