<template>
  <div class="result-container">
    <div class="content-layout">
      <!-- 左侧视频播放区域 -->
      <div class="video-section" v-if="hasVideo">
        <div class="video-card">
          <h3 class="section-title">
            <i class="el-icon-video-camera"></i>
            视频预览
          </h3>
          <div class="video-wrapper">
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
          <div class="video-info" v-if="videoDuration">
            <span>视频时长: {{ formatDuration(videoDuration) }}</span>
          </div>
        </div>
      </div>

      <!-- 右侧讲义区域 -->
      <div class="lecture-section">
        <div class="lecture-card">
          <div class="lecture-header">
            <h3 class="section-title">
              <i class="el-icon-document"></i>
              讲义内容
            </h3>
            <div class="header-actions">
              <button class="download-btn" @click="downloadPdf">
                <i class="el-icon-download"></i>
                下载 PDF
              </button>
              <button class="home-btn" @click="goHome">
                <i class="el-icon-home"></i>
                返回首页
              </button>
            </div>
          </div>
          
          <div ref="markdownContent" v-html="renderedHtml" class="markdown-body" />
          <div v-if="error" class="error">{{ error }}</div>
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

const downloadPdf = async () => {
  await renderMath()
  window.open('http://127.0.0.1:8001/generate_pdf', '_blank')
}

const goHome = async () => {
  await globalStore.fullReset()
  router.push('/')
}
</script>

<style scoped>
.result-container {
  min-height: calc(100vh - 60px);
  background-color: #c4b5e0;
  padding: 30px 20px;
}

.content-layout {
  max-width: 100%;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
  padding: 0 30px;
  box-sizing: border-box;
}

/* 视频区域 */
.video-section {
  position: sticky;
  top: 80px;
  height: fit-content;
  align-self: start;
}

.video-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 10px;
  margin: 0 0 20px 0;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d2d2d;
}

.section-title i {
  color: #5c4d82;
}

.video-wrapper {
  background: #1a1a1a;
  border-radius: 12px;
  overflow: hidden;
}

.video-wrapper video {
  display: block;
  width: 100%;
  height: 500px;
  object-fit: contain;
  background: #000;
}

.video-info {
  margin-top: 15px;
  text-align: center;
  color: #5c5c5c;
  font-size: 0.9rem;
}

/* 讲义区域 */
.lecture-section {
  min-width: 0;
}

.lecture-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 35px 40px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.lecture-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  flex-wrap: wrap;
  gap: 15px;
}

.header-actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.home-btn,
.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  padding: 12px 20px;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 0.95rem;
}

.home-btn {
  background-color: transparent;
  color: #5c4d82;
  border: 2px solid #5c4d82;
}

.home-btn:hover {
  background-color: rgba(92, 77, 130, 0.1);
  transform: translateY(-2px);
}

.download-btn {
  background-color: #5c4d82;
  color: #ffffff;
  border: 2px solid #5c4d82;
  box-shadow: 0 4px 12px rgba(92, 77, 130, 0.25);
}

.download-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.35);
}

/* Markdown 样式 */
.markdown-body {
  font-size: 16px;
  line-height: 1.8;
  color: #2d2d2d;
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
  background-color: #e8e8e8;
  padding: 4px 10px;
  border-radius: 8px;
  color: #5c4d82;
  font-size: 0.9em;
}

.error {
  color: #8b4a4a;
  text-align: center;
  padding: 25px;
  background-color: #fcebeb;
  border: 2px solid #dfb5b5;
  border-radius: 16px;
  margin-top: 30px;
}

/* 响应式设计 */
@media (max-width: 1200px) {
  .content-layout {
    grid-template-columns: 1fr 1fr;
  }
  
  .video-wrapper video {
    height: 400px;
  }
}

@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
    padding: 0 20px;
  }
  
  .video-section {
    position: relative;
    top: 0;
  }
  
  .video-wrapper video {
    height: 400px;
  }
}

@media (max-width: 768px) {
  .result-container {
    padding: 20px 15px;
  }
  
  .lecture-card {
    padding: 25px 20px;
  }
  
  .lecture-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .header-actions {
    width: 100%;
  }
  
  .home-btn,
  .download-btn {
    flex: 1;
    justify-content: center;
  }
  
  .video-wrapper video {
    height: 300px;
  }
}
</style>
