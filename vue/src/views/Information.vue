<template>
  <div class="information-container">
    <!-- 装饰元素 -->
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    
    <div class="information-content">
      <!-- 左侧主内容区域 -->
      <div class="main-section">
        <div class="content-card">
          <div class="card-header">
            <h1 class="page-title">
              <i class="el-icon-setting"></i>
              参数配置
            </h1>
            <p class="page-subtitle">设置视频处理参数以获得最佳识别效果</p>
          </div>

          <el-form :model="form" :rules="rules" ref="infoForm" label-position="top" class="info-form">
          <!-- 基础信息 -->
          <div class="form-section">
            <h3 class="section-title">
              <i class="el-icon-document"></i>
              基础信息
            </h3>
            <div class="form-row">
              <el-form-item label="讲义标题" prop="title">
                <el-input 
                  v-model="form.title" 
                  placeholder="请输入讲义标题"
                  size="large"
                />
              </el-form-item>
              <el-form-item label="视频科目" prop="subject">
                <el-input 
                  v-model="form.subject" 
                  placeholder="请输入科目名称（如：数学、物理等）"
                  size="large"
                />
              </el-form-item>
              <el-form-item label="所属分类" v-if="categories.length > 0">
                <el-select 
                  v-model="form.category_id" 
                  placeholder="请选择分类（可选）"
                  size="large"
                  style="width: 100%"
                >
                  <el-option label="无分类" :value="null" />
                  <el-option 
                    v-for="cat in categories" 
                    :key="cat.id" 
                    :label="cat.name" 
                    :value="cat.id"
                  />
                </el-select>
              </el-form-item>
            </div>
          </div>

          <!-- 生成模式 -->
          <div class="form-section">
            <h3 class="section-title">
              <i class="el-icon-refresh"></i>
              生成模式
            </h3>

            <div class="form-row">
              <el-form-item label="请选择讲义生成方式">
                <el-radio-group v-model="form.generationMode" size="large">
                  <el-radio-button label="normal">非实时生成</el-radio-button>
                  <el-radio-button label="realtime">实时生成</el-radio-button>
                </el-radio-group>

                <div class="mode-tip" v-if="form.generationMode === 'normal'">
                  非实时模式会等待整个视频处理完成后，一次性生成完整讲义，支持音频识别。
                </div>

                <div class="mode-tip realtime" v-else>
                  实时模式会按视频片段逐段处理，并持续输出已生成讲义。为保证响应速度，实时模式默认只使用视频画面 OCR。
                </div>
              </el-form-item>
            </div>
          </div>

          <!-- 识别设置 -->
          <div class="form-section">
            <h3 class="section-title">
              <i class="el-icon-time"></i>
              识别设置
            </h3>
            <div class="form-row">
              <el-form-item label="识别间隔（秒）" prop="interval">
                <div class="input-with-label">
                  <el-input-number 
                    v-model="form.interval" 
                    :min="1" 
                    :max="60"
                    size="large"
                    style="width: 45%"
                  />
                  <span class="input-hint">建议值：10-30秒</span>
                </div>
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
                <div class="input-with-label">
                  <el-input-number 
                    v-model="form.skipLimit" 
                    :min="0" 
                    :max="10"
                    :disabled="form.fast"
                    size="large"
                    style="width: 45%"
                  />
                  <span class="input-hint" :class="{ disabled: form.fast }">快速模式下不可用</span>
                </div>
              </el-form-item>
            </div>
          </div>

          <!-- 音频处理 -->
          <div class="form-section">
            <h3 class="section-title">
              <i class="el-icon-microphone"></i>
              音频处理
            </h3>
            <div class="form-row">
              <el-form-item label="同时启用音频识别">
                <div class="switch-wrapper">
                  <el-switch 
                    v-model="form.useAudio" 
                    active-text="开启" 
                    inactive-text="关闭"
                    size="large"
                    :disabled="form.generationMode === 'realtime'"
                  />
                  <span class="switch-description">
                    {{ form.generationMode === 'realtime' ? '实时模式暂不启用音频识别' : (form.useAudio ? '同时处理音频内容' : '仅处理视频内容') }}
                  </span>
                </div>
              </el-form-item>
            </div>
          </div>

          </el-form>

          <!-- 按钮区域 -->
          <div class="button-section">
            <button class="action-button prev-btn" @click="onPrev">
              <i class="el-icon-arrow-left"></i>
              上一步
            </button>
            
            <button class="action-button next-btn" @click="onNext">
              <i class="el-icon-right"></i>
              开始处理
            </button>
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
            <p class="video-subtitle">即将处理的视频内容</p>
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

          <!-- <div class="video-tips">
            <h4>
              <i class="el-icon-info"></i>
              温馨提示
            </h4>
            <ul>
              <li><i class="el-icon-circle-check"></i> 请确保视频文件完整且格式正确</li>
              <li><i class="el-icon-circle-check"></i> 建议视频分辨率不低于 720p</li>
              <li><i class="el-icon-circle-check"></i> 良好的光线条件有助于提高识别准确率</li>
            </ul>
          </div> -->

          <!-- 参数说明 -->
          <div class="explanation-card">
            <div class="explanation-header">
              <i class="el-icon-warning"></i>
              <span>参数说明</span>
            </div>
            <div class="explanation-content">
              <div class="explanation-item">
                <strong>识别间隔</strong>
                <p>每隔几秒对视频进行一次板书识别，间隔越小识别越精细但处理时间越长。</p>
              </div>
              <div class="explanation-item">
                <strong>跳过机制</strong>
                <p>当检测到教师遮挡板书时，系统会跳过该帧的识别，避免遗漏重要内容。</p>
              </div>
              <div class="explanation-item">
                <strong>快速模式</strong>
                <p>开启后将不检测遮挡情况，直接进行识别，处理速度更快。</p>
              </div>
              <div class="explanation-item">
                <strong>音频识别</strong>
                <p>同时处理视频中的音频内容，可以获得更完整的课程信息。</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import { useAuthStore } from '../stores/auth'
import { useLectureStore } from '../stores/lecture'
import { ElMessage } from 'element-plus'

export default {
  setup() {
    const router = useRouter()
    const infoForm = ref(null)
    const globalStore = useGlobalStore()
    const authStore = useAuthStore()
    const lectureStore = useLectureStore()
    const videoPlayer = ref(null)
    const videoUrl = ref('')
    const videoDuration = ref(0)

    const categories = ref([])

    const form = ref({
      title: '',
      subject: '',
      category_id: null,
      interval: 15,
      skipLimit: 2,
      fast: false,
      useAudio: true,
      generationMode: 'normal',
      segmentSec: 60
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

    const loadCategories = async () => {
      if (authStore.isAuthenticated) {
        try {
          lectureStore.setAuthHeader(authStore.token)
          const res = await lectureStore.fetchCategories()
          if (res.success) {
            categories.value = res.categories
          }
        } catch (err) {
          console.error('加载分类失败:', err)
        }
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

    const onPrev = () => {
      router.back()
    }

    const onNext = () => {
      infoForm.value.validate(async (valid) => {
        if (!valid) {
          ElMessage({
            message: '请填写完整的参数信息后再继续',
            type: 'warning',
            duration: 1500
          })
          return
        }

        globalStore.setGenerationMode(form.value.generationMode)

        // 实时模式暂不启用音频，避免 Whisper 整段识别拖慢实时输出
        if (form.value.generationMode === 'realtime') {
          form.value.useAudio = false
        }

        globalStore.setUseAudio(form.value.useAudio)

        let lectureId = null

        if (authStore.isAuthenticated && form.value.title) {
          try {
            lectureStore.setAuthHeader(authStore.token)
            const res = await lectureStore.createLecture({
              title: form.value.title,
              subject: form.value.subject,
              category_id: form.value.category_id,
              status: 'processing',
              processing_params: {
                generation_mode: form.value.generationMode
              }
            })

            if (res.success) {
              lectureId = res.lecture.id
              ElMessage.success('讲义已创建，正在处理...')
            }
          } catch (err) {
            console.error('创建讲义失败:', err)
            ElMessage.warning('讲义存档创建失败，但仍将继续处理视频')
          }
        }

        // 非实时模式：完全保留原流程
        if (form.value.generationMode === 'normal') {
          router.push('/generating')

          const payload = {
            advanced: globalStore.advanced,
            subject: form.value.subject,
            interval_sec: form.value.interval,
            max_skip: form.value.skipLimit,
            fast: form.value.fast,
            use_audio: form.value.useAudio,
            lecture_id: lectureId
          }

          fetch('http://127.0.0.1:8001/execute/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
          }).catch(err => {
            console.error('请求失败', err)
            ElMessage.error('处理请求发送失败')
          })
          if (form.value.useAudio) {
            fetch('http://127.0.0.1:8002/process_video')
              .then(res => res.json())
              .then(data => {
                if (!data.status) {
                  console.error('音频识别失败:', data.error || data.message)
                }
              })
              .catch(err => {
                console.error('音频识别请求失败:', err)
              })
          }

          // 注意：
          // 原来这里还会额外调用 8002/process_video。
          // 现在删除这次额外调用，因为 django1 的 /execute/ 在 use_audio=true 时已经会调用 8002。
          // 这样可以避免 Whisper 重复执行和临时文件互相覆盖。
          return
        }

        // 实时模式：走新增实时接口
        try {
          const realtimePayload = {
            subject: form.value.subject,
            interval_sec: form.value.interval,
            segment_sec: form.value.segmentSec || 60,
            lecture_id: lectureId,
            use_audio: false
          }

          const response = await fetch('http://127.0.0.1:8001/realtime/start/', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(realtimePayload)
          })

          const data = await response.json()

          if (!data.success) {
            ElMessage.error(data.message || '实时任务启动失败')
            return
          }

          globalStore.setRealtimeTaskId(data.task_id)
          ElMessage.success('实时生成任务已启动')
          router.push(`/generating?mode=realtime&task_id=${data.task_id}`)
        } catch (err) {
          console.error('实时任务启动失败:', err)
          ElMessage.error('实时任务启动失败，请检查后端服务')
        }
      })
    }

    onMounted(() => {
      loadCategories()
      loadVideo()
    })

    return {
      form,
      rules,
      infoForm,
      categories,
      videoPlayer,
      videoUrl,
      videoDuration,
      formatDuration,
      onVideoLoaded,
      onPrev,
      onNext,
    }
  }
}
</script>

<style scoped>
.information-container {
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

.information-content {
  display: grid;
  grid-template-columns: 1fr 0.7fr;
  gap: 40px;
  max-width: 1500px;
  width: 100%;
  position: relative;
  z-index: 1;
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

.page-title {
  font-family: 'Georgia', serif;
  font-size: 2.4rem;
  font-weight: 700;
  margin-bottom: 12px;
  color: #2d2d2d;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
}

.page-title i {
  color: #5c4d82;
  font-size: 1.5em;
}

.page-subtitle {
  font-size: 1.15rem;
  color: #5c5c5c;
  margin: 0;
}

/* 表单区域 */
.form-section {
  margin-bottom: 35px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
  font-size: 1.3rem;
  font-weight: 600;
  color: #2d2d2d;
}

.section-title i {
  color: #5c4d82;
  font-size: 1.4rem;
}

.form-row {
  display: flex;
  flex-direction: column;
  gap: 22px;
}

.form-row :deep(.el-form-item) {
  margin-bottom: 0;
}

.input-with-label {
  display: flex;
  align-items: center;
  gap: 15px;
}

.input-hint {
  font-size: 0.9rem;
  color: #888;
}

.input-hint.disabled {
  color: #ccc;
}

.switch-wrapper {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.switch-description {
  font-size: 0.95rem;
  color: #5c5c5c;
}

/* 自定义开关主题色 */
:deep(.el-switch) {
  --el-switch-on-color: #5c4d82;
  --el-switch-off-color: #d4c8e0;
  --el-switch-on-text-color: #ffffff;
  --el-switch-off-text-color: #888888;
}

/* 开关选中状态文字颜色 */
:deep(.el-switch__label.is-active) {
  color: #5c4d82;
  font-weight: 600;
}

/* 参数说明卡片 */
.explanation-card {
  background: #faf9fc;
  border-radius: 16px;
  padding: 28px;
  margin-bottom: 35px;
  border: 2px solid #e8e0f0;
}

.explanation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #7a5c29;
}

.explanation-header i {
  color: #8b6914;
}

.explanation-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.explanation-item {
  padding: 15px;
  background: #ffffff;
  border-radius: 12px;
}

.explanation-item strong {
  display: block;
  margin-bottom: 8px;
  color: #5c4d82;
  font-weight: 600;
}

.explanation-item p {
  margin: 0;
  font-size: 0.9rem;
  color: #5c5c5c;
  line-height: 1.6;
}

/* 按钮区域 */
.button-section {
  display: flex;
  justify-content: center;
  gap: 20px;
  margin-top: 10px;
}

.action-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 40px;
  font-size: 1.05rem;
  font-weight: 600;
  border-radius: 12px;
  border: 2px solid transparent;
  cursor: pointer;
  transition: all 0.3s ease;
  outline: none;
  min-width: 150px;
}

.action-button i {
  font-size: 1.1rem;
}

.action-button:active {
  transform: scale(0.98);
}

.prev-btn {
  background: #faf9fc;
  border-color: #d4c8e0;
  color: #5c5c5c;
}

.prev-btn:hover {
  border-color: #5c4d82;
  background: #f0ecf7;
  color: #5c4d82;
}

.prev-btn:active {
  background: #e8e0f0;
}

.next-btn {
  background: #5c4d82;
  border-color: #5c4d82;
  color: #ffffff;
}

.next-btn:hover {
  background: #4a3d6a;
  border-color: #4a3d6a;
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(92, 77, 130, 0.35);
}

.next-btn:active {
  background: #3d3257;
  transform: translateY(0);
  box-shadow: 0 4px 15px rgba(92, 77, 130, 0.25);
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
  margin-bottom: 25px;
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

.video-tips {
  background: #faf9fc;
  border-radius: 12px;
  padding: 20px;
  flex-grow: 1;
}

.video-tips h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 0 15px 0;
  font-size: 1rem;
  font-weight: 600;
  color: #2d2d2d;
}

.video-tips h4 i {
  color: #5c4d82;
}

.video-tips ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.video-tips li {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  margin-bottom: 12px;
  font-size: 0.9rem;
  color: #5c5c5c;
}

.video-tips li:last-child {
  margin-bottom: 0;
}

.video-tips li i {
  color: #52c41a;
  margin-top: 2px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .information-content {
    grid-template-columns: 1fr;
    max-width: 700px;
  }
  
  .video-card {
    max-width: 100%;
  }
}

@media (max-width: 768px) {
  .information-container {
    padding: 20px 15px;
  }
  
  .content-card {
    padding: 30px 25px;
  }
  
  .page-title {
    font-size: 1.9rem;
  }
  
  .explanation-grid {
    grid-template-columns: 1fr;
  }
  
  .button-section {
    flex-direction: column;
    gap: 15px;
  }
  
  .action-button {
    width: 100%;
    justify-content: center;
  }
  
  .video-card {
    padding: 25px;
  }
}

.mode-tip {
  margin-top: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  background: #f6f3fb;
  color: #5c4d82;
  font-size: 0.92rem;
  line-height: 1.6;
}

.mode-tip.realtime {
  background: #f0f9ff;
  color: #3b6f9e;
}
</style>