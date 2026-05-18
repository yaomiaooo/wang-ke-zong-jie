<template>
  <div class="information-container">
    <div class="content-wrapper">
      <div class="header-section">
        <h1 class="page-title">
          <i class="el-icon-setting"></i>
          参数配置
        </h1>
        <p class="page-subtitle">设置视频处理参数以获得最佳识别效果</p>
      </div>

      <div class="form-card">
        <el-form :model="form" :rules="rules" ref="infoForm" label-position="top" class="info-form">
          <div class="form-grid">
            <div class="form-section">
              <h3 class="section-title">
                <i class="el-icon-document"></i>
                基础信息
              </h3>
              <el-form-item label="视频科目" prop="subject">
                <el-input 
                  v-model="form.subject" 
                  placeholder="请输入科目名称（如：数学、物理等）"
                  size="large"
                />
              </el-form-item>
            </div>

            <div class="form-section">
              <h3 class="section-title">
                <i class="el-icon-time"></i>
                识别设置
              </h3>
              <el-form-item label="识别间隔（秒）" prop="interval">
                <el-input-number 
                  v-model="form.interval" 
                  :min="1" 
                  size="large"
                  style="width: 50%"
                />
              </el-form-item>

              <el-form-item label="快速模式">
                <div class="switch-wrapper">
                  <el-switch 
                    v-model="form.fast" 
                    active-text="开启" 
                    inactive-text="关闭"
                    size="large"
                  />
                  <span class="switch-description">
                    {{ form.fast ? '不检测遮挡，直接识别' : '检测遮挡情况' }}
                  </span>
                </div>
              </el-form-item>

              <el-form-item label="最多跳过次数" prop="skipLimit">
                <el-input-number 
                  v-model="form.skipLimit" 
                  :min="0" 
                  :disabled="form.fast"
                  size="large"
                  style="width: 50%"
                />
              </el-form-item>
            </div>

            <div class="form-section">
              <h3 class="section-title">
                <i class="el-icon-microphone"></i>
                音频处理
              </h3>
              <el-form-item label="同时启用音频识别">
                <div class="switch-wrapper">
                  <el-switch 
                    v-model="form.useAudio" 
                    active-text="开启" 
                    inactive-text="关闭"
                    size="large"
                  />
                  <span class="switch-description">
                    {{ form.useAudio ? '同时处理音频内容' : '仅处理视频内容' }}
                  </span>
                </div>
              </el-form-item>
            </div>
          </div>

          <div class="explanation-card">
            <div class="explanation-header">
              <i class="el-icon-warning"></i>
              <span>参数说明</span>
            </div>
            <div class="explanation-content">
              <p><strong>识别间隔：</strong>每隔几秒对视频进行一次板书识别，间隔越小识别越精细但处理时间越长。</p>
              <p><strong>跳过机制：</strong>当检测到教师遮挡板书时，系统会跳过该帧的识别。但为避免遗漏重要内容，设置了最大跳过次数限制。</p>
              <p><strong>快速模式：</strong>开启后将不检测遮挡情况，直接进行识别，处理速度更快但可能包含被遮挡的内容。</p>
              <p><strong>音频识别：</strong>同时处理视频中的音频内容，可以获得更完整的课程信息。</p>
            </div>
          </div>

          <div class="button-section">
            <el-button type="primary" @click="onNext" size="large" class="submit-button">
              <i class="el-icon-right"></i>
              开始处理
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
import { ElMessage } from 'element-plus'

export default {
  setup() {
    const router = useRouter()
    const infoForm = ref(null)
    const globalStore = useGlobalStore()

    const form = ref({
      subject: '',
      interval: 15,
      skipLimit: 2,
      fast: false,
      useAudio: true 
    })

    const rules = {
      subject: [
        { required: true, message: '科目名称不能为空', trigger: 'blur' }
      ],
      interval: [
        { type: 'number', required: true, min: 1, message: '必须是正整数', trigger: 'change' }
      ],
      skipLimit: [
        { type: 'number', required: true, min: 1, message: '必须是正整数', trigger: 'change' }
      ]
    }

    const onNext = () => {
        infoForm.value.validate((valid) => {
            if (valid) {
                globalStore.setUseAudio(form.value.useAudio)
                router.push('/generating')
                const payload = {
                    advanced: globalStore.advanced,           // 是否固定区域
                    subject: form.value.subject,              // 科目名称
                    interval_sec: form.value.interval,        // 每几秒识别一次
                    max_skip: form.value.skipLimit,            // 最多跳过几次
                    fast: form.value.fast,
                    use_audio: form.value.useAudio
                }

                fetch('http://127.0.0.1:8001/execute/', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                }).catch(err => {
                    console.error('请求失败', err)
                })

                if (form.value.useAudio) {
                  fetch('http://127.0.0.1:8002/process_video')
                  .catch(err => {
                    console.error('请求失败（音频处理）', err)
                })}
            }
            else {
              ElMessage({
                message: '请填写完整的参数信息后再继续',
                type: 'warning',
                duration: 1500
              })
            }
        })
    }

    return {
      form,
      rules,
      infoForm,
      onNext,
    }
  }
}
</script>

<style scoped>
.information-container {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  padding: 40px 20px;
}

.content-wrapper {
  max-width: 900px;
  margin: 0 auto;
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

.form-grid {
  display: grid;
  gap: 40px;
}

.form-section {
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
  padding: 30px;
  border-left: 4px solid #667eea;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
  font-size: 1.3rem;
  font-weight: 600;
  color: #333;
}

.section-title i {
  color: #667eea;
  font-size: 1.4rem;
}

.switch-wrapper {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.switch-description {
  font-size: 0.9rem;
  color: #666;
  font-style: italic;
}

.explanation-card {
  background: linear-gradient(145deg, #fff3cd, #ffeaa7);
  border-radius: 15px;
  padding: 30px;
  border-left: 4px solid #f39c12;
  margin: 30px 0;
}

.explanation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #856404;
}

.explanation-header i {
  color: #f39c12;
  font-size: 1.3rem;
}

.explanation-content p {
  margin-bottom: 15px;
  line-height: 1.6;
  color: #856404;
}

.explanation-content strong {
  color: #6c5ce7;
}

.button-section {
  text-align: center;
  margin-top: 40px;
}

.submit-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  padding: 15px 50px;
  font-size: 1.2rem;
  font-weight: 600;
  border-radius: 10px;
  transition: all 0.3s ease;
}

.submit-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

.submit-button i {
  margin-right: 8px;
}

@media (max-width: 768px) {
  .form-card {
    padding: 30px 20px;
  }
  
  .form-grid {
    gap: 25px;
  }
  
  .form-section {
    padding: 20px;
  }
}
</style>
