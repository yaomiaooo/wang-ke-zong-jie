<template>
  <div class="result-container">
    <!-- 装饰元素 -->
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    
    <div class="result-content">
      <!-- 主内容区域 -->
      <div class="main-content-wrapper">
        <!-- 左侧讲义区域 -->
        <div class="lecture-section">
          <div class="lecture-card">
            <div class="lecture-header">
              <h2 class="page-title">
                <i class="el-icon-document"></i>
                讲义内容
              </h2>
              <button class="edit-btn" @click="editLecture">
                <i class="el-icon-edit"></i>
                编辑讲义
              </button>
            </div>
            
            <div ref="markdownContent" v-html="renderedHtml" class="markdown-body" />
            <div v-if="error" class="error-message">{{ error }}</div>
          </div>
        </div>

        <!-- 右侧视频区域 -->
        <div class="right-panel">
          <div class="video-section">
            <div class="video-card">
              <div class="video-header">
                <h3 class="section-title">
                  <i class="el-icon-video-camera"></i>
                  视频预览
                </h3>
              </div>
              <div class="video-wrapper" v-if="hasVideo">
                <video 
                  ref="videoPlayer"
                  :src="videoUrl"
                  controls
                  @loadedmetadata="onVideoLoaded"
                  @timeupdate="onTimeUpdate"
                  @ended="onVideoEnded"
                >
                  您的浏览器不支持视频播放
                </video>
              </div>
              <div class="video-placeholder" v-else>
                <i class="el-icon-video-camera"></i>
                <p>暂无视频</p>
              </div>
              <div class="video-info" v-if="videoDuration">
                <span><i class="el-icon-clock"></i> 视频时长: {{ formatDuration(videoDuration) }}</span>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮区域 -->
          <div class="action-panel">
            <div class="action-buttons">
              <button class="action-btn" @click="downloadPdf">
                <i class="el-icon-document"></i>
                导出 PDF
              </button>
              <button class="action-btn" @click="downloadWord">
                <i class="el-icon-document"></i>
                导出 Word
              </button>
              <button class="action-btn" @click="downloadMd">
                <i class="el-icon-tickets"></i>
                导出 MD
              </button>
            </div>
            
            <div class="bottom-buttons">
              <button class="action-btn home-btn" @click="goHome">
                <i class="el-icon-home"></i>
                返回首页
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import MarkdownIt from 'markdown-it'
import { ElMessage } from 'element-plus'

const router = useRouter()
const globalStore = useGlobalStore()

const videoUrl = ref('')
const hasVideo = ref(false)
const videoPlayer = ref(null)
const videoDuration = ref(0)

const renderedHtml = ref('')
const markdownContent = ref(null)
const error = ref('')

const VIDEO_API_URL = 'http://127.0.0.1:8001/get_current_video/'

const fixLatexInline = (str) =>
  str
    .replace(/\\overrightarrow{[^}]+}/g, (m) => `\\(${m}\\)`)
    .replace(/\|\\overrightarrow{[^}]+}\|/g, (m) => `\\(${m}\\)`)
    .replace(/(\b[a-zA-Z]\b)\s*⃗/g, (_, v) => `\\(\\vec{${v}}\\)`)
    .replace(/\|0\|/g, '\\(\\left|0\\right|\\)')
    .replace(/\|a\|/g, '\\(\\left|a\\right|\\)')

const renderMath = () => {
  if (window.MathJax) {
    window.MathJax.typesetPromise?.()
  }
}

const formatDuration = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const onVideoLoaded = () => {
  if (videoPlayer.value) {
    videoDuration.value = videoPlayer.value.duration
  }
}

const onTimeUpdate = () => {
  // 可以在这里同步讲义内容和视频进度
}

const onVideoEnded = () => {
  console.log('视频播放完毕')
}

const loadVideo = async () => {
  try {
    const response = await fetch(VIDEO_API_URL)
    if (response.ok) {
      hasVideo.value = true
      videoUrl.value = VIDEO_API_URL
    } else {
      hasVideo.value = false
    }
  } catch (err) {
    console.error('获取视频失败:', err)
    hasVideo.value = false
  }
}

const downloadPdf = async () => {
  await renderMath()
  window.open('http://127.0.0.1:8001/generate_pdf', '_blank')
}

const downloadWord = async () => {
  ElMessage.info('正在生成 Word 文档...')
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()
    if (json.status === 'success' && json.content) {
      // 创建 Blob 并下载
      const blob = new Blob([json.content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'lecture.md'
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('Markdown 文件已下载，请使用 Typora 等工具转换为 Word')
    }
  } catch (err) {
    ElMessage.error('下载失败')
    console.error(err)
  }
}

const downloadMd = async () => {
  ElMessage.info('正在导出 MD 格式...')
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()
    if (json.status === 'success' && json.content) {
      const blob = new Blob([json.content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'lecture.md'
      a.click()
      URL.revokeObjectURL(url)
      ElMessage.success('MD 文件已导出')
    }
  } catch (err) {
    ElMessage.error('导出失败')
    console.error(err)
  }
}

const editLecture = () => {
  ElMessage.info('编辑功能开发中...')
  // 可以在这里添加编辑讲义的逻辑
}

const goHome = async () => {
  await globalStore.fullReset()
  router.push('/')
}

onMounted(async () => {
  // 加载视频
  await loadVideo()
  
  // 加载讲义内容
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()

    if (json.status === 'success' && json.content) {
      const md = new MarkdownIt({ html: true })
      const fixed = fixLatexInline(json.content)
      renderedHtml.value = md.render(fixed)

      await nextTick()
      renderMath()
    } else {
      error.value = '后端返回失败：' + (json.message || '未知错误')
    }
  } catch (err) {
    error.value = '获取总结失败，请检查后端服务是否启动'
    console.error(err)
  }
})
</script>

<style scoped>
.result-container {
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

.result-content {
  max-width: 1500px;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* 主内容区域 */
.main-content-wrapper {
  display: grid;
  grid-template-columns: 1fr 0.65fr;
  gap: 40px;
}

/* 讲义区域 */
.lecture-section {
  display: flex;
  align-items: flex-start;
}

.lecture-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 35px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
  max-height: calc(100vh - 120px);
  overflow-y: auto;
}

.lecture-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 25px;
  gap: 15px;
}

.page-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-family: 'Georgia', serif;
  font-size: 1.6rem;
  font-weight: 600;
  color: #2d2d2d;
}

.page-title i {
  color: #5c4d82;
}

/* 编辑按钮 */
.edit-btn {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 18px;
  font-size: 0.9rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #d4c8e0;
  background: #faf9fc;
  color: #5c4d82;
  flex-shrink: 0;
}

.edit-btn:hover {
  border-color: #5c4d82;
  background: #f0ecf7;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(92, 77, 130, 0.15);
}

.edit-btn i {
  font-size: 1rem;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

/* 视频区域 */
.video-section {
  display: flex;
  align-items: flex-start;
}

.video-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
}

.video-header {
  margin-bottom: 20px;
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0;
  font-size: 1.4rem;
  font-weight: 600;
  color: #2d2d2d;
}

.section-title i {
  color: #5c4d82;
  font-size: 1.5rem;
}

.video-wrapper {
  background: #1a1a1a;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 20px;
  width: 100%;
  aspect-ratio: 16 / 9;
}

.video-wrapper video {
  display: block;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-placeholder {
  background: #1a1a1a;
  border-radius: 16px;
  padding: 60px 20px;
  text-align: center;
  margin-bottom: 20px;
}

.video-placeholder i {
  font-size: 4rem;
  color: #666;
}

.video-placeholder p {
  color: #999;
  margin-top: 15px;
}

.video-info {
  display: flex;
  justify-content: center;
  color: #5c5c5c;
  font-size: 0.95rem;
}

.video-info i {
  color: #5c4d82;
  margin-right: 6px;
}

/* 右侧面板 */
.right-panel {
  display: flex;
  flex-direction: column;
  gap: 25px;
}

/* 操作按钮面板 */
.action-panel {
  background: #ffffff;
  border-radius: 24px;
  padding: 30px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
}

/* 操作按钮区域 */
.action-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0ecf7;
}

.action-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px 20px;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #5c4d82;
  background: #5c4d82;
  color: #ffffff;
  min-width: 120px;
}

.action-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.action-btn:active {
  transform: translateY(0);
}

.action-btn i {
  font-size: 1.1rem;
}

.secondary-btn {
  background: #faf9fc;
  color: #5c4d82;
  border-color: #d4c8e0;
}

.secondary-btn:hover {
  border-color: #5c4d82;
  background: #f0ecf7;
}

/* Markdown 样式 */
.markdown-body {
  font-size: 16px;
  line-height: 1.8;
  color: #2d2d2d;
  margin-bottom: 30px;
}

.markdown-body :deep(h1),
.markdown-body :deep(h2),
.markdown-body :deep(h3) {
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  color: #2d2d2d;
  border-bottom: 2px solid #e8e8e8;
  padding-bottom: 0.4em;
  font-weight: 600;
}

.markdown-body :deep(h1) {
  font-size: 1.8rem;
}

.markdown-body :deep(h2) {
  font-size: 1.5rem;
}

.markdown-body :deep(h3) {
  font-size: 1.3rem;
}

.markdown-body :deep(p) {
  margin: 1.2em 0;
  word-break: break-word;
  color: #5c5c5c;
}

.markdown-body :deep(ul),
.markdown-body :deep(ol) {
  padding-left: 1.8em;
  margin-bottom: 1.2em;
  color: #5c5c5c;
}

.markdown-body :deep(li) {
  margin-bottom: 0.6em;
}

.markdown-body :deep(code) {
  font-family: 'Courier New', monospace;
  background-color: #f0ecf7;
  padding: 4px 10px;
  border-radius: 8px;
  color: #5c4d82;
  font-size: 0.9em;
}

.error-message {
  color: #b56b6b;
  text-align: center;
  padding: 25px;
  background-color: #fcebeb;
  border: 2px solid #dfb5b5;
  border-radius: 16px;
  margin-bottom: 20px;
}

/* 底部按钮 */
.bottom-buttons {
  display: flex;
  justify-content: center;
}

.home-btn {
  background: #faf9fc;
  color: #5c5c5c;
  border-color: #d4c8e0;
  min-width: 150px;
  width: 100%;
}

.home-btn:hover {
  border-color: #5c4d82;
  background: #f0ecf7;
  color: #5c4d82;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .main-content-wrapper {
    grid-template-columns: 1fr;
    gap: 30px;
  }
  
  .lecture-card,
  .video-card,
  .action-panel {
    max-width: 100%;
  }
  
  .action-buttons {
    justify-content: center;
  }
}

@media (max-width: 768px) {
  .result-container {
    padding: 20px 15px;
  }
  
  .lecture-card,
  .video-card,
  .action-panel {
    padding: 25px 20px;
  }
  
  .lecture-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 15px;
  }
  
  .section-title {
    font-size: 1.3rem;
  }
  
  .page-title {
    font-size: 1.4rem;
  }
  
  .edit-btn {
    width: 100%;
    justify-content: center;
  }
  
  .action-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .action-btn {
    width: 100%;
  }
  
  .markdown-body {
    font-size: 14px;
  }
  
  .bottom-buttons {
    flex-direction: column;
    gap: 10px;
  }
  
  .home-btn {
    width: 100%;
  }
}
</style>
