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
             
              <button class="action-btn" @click="downloadWord">
                <i class="el-icon-document"></i>
                导出 Word
              </button>
              <button class="action-btn" @click="downloadMd">
                <i class="el-icon-tickets"></i>
                导出 MD
              </button>
               <button class="action-btn polish-btn" @click="polishLecture" :disabled="isPolishing">
                <i class="el-icon-magic-stick"></i>
                {{ isPolishing ? '整理中...' : '一键整理' }}
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

    <!-- 编辑讲义对话框 -->
    <el-dialog
      v-model="editDialogVisible"
      title=""
      width="85%"
      :close-on-click-modal="false"
      :show-close="true"
      class="edit-dialog"
      destroy-on-close
    >
      <template #header>
        <div class="edit-dialog-header">
          <h2>编辑讲义</h2>
          <span class="save-status" v-if="isSaving">正在保存...</span>
          <span class="save-status success" v-else-if="lastSaved">已保存 {{ lastSaved }}</span>
        </div>
      </template>
      
      <div class="edit-content">
        <div class="edit-toolbar">
          <div class="title-input-wrapper">
            <label>讲义标题：</label>
            <input 
              v-model="editTitle" 
              type="text" 
              class="title-input"
              placeholder="请输入讲义标题"
              maxlength="200"
              @input="markAsChanged"
            />
            <span class="char-count">{{ editTitle.length }}/200</span>
          </div>
          <div class="format-buttons">
            <button type="button" @click="insertFormat('**', '**')" title="加粗"><b>B</b></button>
            <button type="button" @click="insertFormat('*', '*')" title="斜体"><i>I</i></button>
            <button type="button" @click="insertFormat('\n## ', '')" title="二级标题">H2</button>
            <button type="button" @click="insertFormat('\n### ', '')" title="三级标题">H3</button>
            <button type="button" @click="insertFormat('\n- ', '')" title="无序列表">•</button>
            <button type="button" @click="insertFormat('\n1. ', '')" title="有序列表">1.</button>
            <button type="button" @click="insertFormat('\n> ', '')" title="引用">"</button>
            <button type="button" @click="insertFormat('\n```\n', '\n```')" title="代码块">&lt;/&gt;</button>
            <button type="button" @click="insertFormat('`', '`')" title="行内代码"><code>`</code></button>
            <button type="button" @click="insertFormat('\n---\n', '')" title="分隔线">—</button>
            <button type="button" @click="insertFormat('$$\n', '\n$$')" title="数学公式">∑</button>
            <button type="button" @click="insertFormat('| 表头1 | 表头2 |\n|------|------|\n| 内容1 | 内容2 |', '')" title="表格">▦</button>
          </div>
        </div>
        
        <div class="editor-wrapper">
          <textarea 
            ref="editorTextarea"
            v-model="editContent"
            class="editor-textarea"
            placeholder="在此编辑讲义内容，支持 Markdown 格式..."
            @input="markAsChanged"
            @keydown="handleKeydown"
          ></textarea>
        </div>
        
        <div class="preview-toggle">
          <el-switch
            v-model="showPreview"
            active-text="预览"
            inactive-text="编辑"
            @change="togglePreview"
          />
        </div>
        
        <div v-if="showPreview" class="preview-wrapper">
          <h3 class="preview-title">预览</h3>
          <div class="preview-content" v-html="previewHtml"></div>
        </div>
      </div>
      
      <template #footer>
        <div class="dialog-footer">
          <button class="btn-cancel" @click="cancelEdit">取消</button>
          <button class="btn-save" @click="saveLecture">
            <i class="el-icon-document"></i>
            保存讲义
          </button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import { useLectureStore } from '../stores/lecture'
import { useAuthStore } from '../stores/auth'
import MarkdownIt from 'markdown-it'
import { ElMessage, ElMessageBox } from 'element-plus'

const router = useRouter()
const globalStore = useGlobalStore()
const lectureStore = useLectureStore()
const authStore = useAuthStore()

const videoUrl = ref('')
const hasVideo = ref(false)
const videoPlayer = ref(null)
const videoDuration = ref(0)

const renderedHtml = ref('')
const markdownContent = ref(null)
const error = ref('')
const isPolishing = ref(false)

const md = new MarkdownIt({
  html: true,
  linkify: true,
  breaks: true
})

// 编辑相关状态
const editDialogVisible = ref(false)
const editTitle = ref('')
const editContent = ref('')
const editOriginalTitle = ref('')
const editOriginalContent = ref('')
const hasChanges = ref(false)
const isSaving = ref(false)
const lastSaved = ref('')
const showPreview = ref(false)
const editorTextarea = ref(null)
const previewHtml = ref('')
const actualLectureId = ref(null)

// 获取当前讲义ID
const currentLectureId = computed(() => {
  return actualLectureId.value || 1
})

const VIDEO_API_URL = 'http://127.0.0.1:8001/get_current_video/'

const fixLatexInline = (str) =>
  str
    .replace(/\\overrightarrow{[^}]+}/g, (m) => `\\(${m}\\)`)
    .replace(/\|\\overrightarrow{[^}]+}\|/g, (m) => `\\(${m}\\)`)
    .replace(/(\b[a-zA-Z]\b)\s*⃗/g, (_, v) => `\\(\\vec{${v}}\\)`)
    .replace(/\|0\|/g, '\\(\\left|0\\right|\\)')
    .replace(/\|a\|/g, '\\(\\left|a\\right|\\)')

// 解析内容中的图片标记 [IMAGE:frame_XXXX.jpg]
const parseImageMarkers = (content) => {
  if (!content || typeof content !== 'string') {
    console.log('parseImageMarkers: 内容为空或不是字符串')
    return content
  }
  
  // 调试：测试正则表达式
  const testContent = '测试 [IMAGE:frame_0012.jpg] 标记'
  const testPattern = /\[IMAGE:([^\]]+)\]/gi
  console.log('测试正则匹配:', testContent.match(testPattern))
  console.log('测试替换结果:', testContent.replace(testPattern, '![图片]($1)'))
  
  // 调试：打印原始内容片段（转换为 ASCII 查看）
  console.log('parseImageMarkers 输入内容长度:', content.length)
  console.log('parseImageMarkers 输入内容 (前 500 字符):', content.substring(0, 500))
  
  // 检查是否包含 IMAGE 字符串
  console.log('包含 IMAGE 字符串:', content.includes('IMAGE'))
  console.log('包含 [IMAGE:', content.includes('[IMAGE'))
  
  // 使用正则表达式替换为 Markdown 图片格式
  const imagePattern = /\[IMAGE:([^\]]+)\]/gi
  const matches = content.match(imagePattern)
  console.log('正则找到的匹配:', matches)
  
  if (matches && matches.length > 0) {
    const result = content.replace(imagePattern, (match, filename) => {
      const cleanFilename = filename.trim()
      console.log('匹配到图片标记:', match, '提取的文件名:', cleanFilename)
      if (cleanFilename) {
        const imageUrl = `http://127.0.0.1:8001/frame/${encodeURIComponent(cleanFilename)}/`
        const imgTag = `<img src="${imageUrl}" alt="${cleanFilename}" class="frame-image" />`
        console.log('生成的 img 标签:', imgTag)
        return imgTag
      }
      return match
    })
    console.log('parseImageMarkers 输出内容 (前 500 字符):', result.substring(0, 500))
    return result
  } else {
    // 方法 2：如果正则没匹配到，尝试手动解析
    console.log('正则未匹配到，尝试手动解析')
    const parts = content.split('[IMAGE:')
    if (parts.length > 1) {
      let result = parts[0]
      for (let i = 1; i < parts.length; i++) {
        const endIndex = parts[i].indexOf(']')
        if (endIndex > 0) {
          const filename = parts[i].substring(0, endIndex).trim()
          const rest = parts[i].substring(endIndex + 1)
          const imageUrl = `http://127.0.0.1:8001/frame/${encodeURIComponent(filename)}/`
          result += `<img src="${imageUrl}" alt="${filename}" class="frame-image" />${rest}`
          console.log('手动解析：', filename)
        } else {
          result += '[IMAGE:' + parts[i]
        }
      }
      console.log('parseImageMarkers 输出内容 (前 500 字符):', result.substring(0, 500))
      return result
    }
  }
  
  return content
}

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

const downloadWord = async () => {
  ElMessage.info('正在生成 Word 文档，请稍候...')
  try {
    // 调用后端 Word 生成接口
    const response = await fetch('http://127.0.0.1:8001/generate_word')
    if (response.ok) {
      // 获取文件名
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'lecture.docx'
      if (contentDisposition) {
        const match = contentDisposition.match(/filename[^;=\n]*=((['"]).*?\2|[^;\n]*)/)
        if (match) {
          filename = match[1].replace(/['"]/g, '')
        }
      }
      // 下载文件
      const blob = await response.blob()
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      ElMessage.success('Word 文档已成功导出')
    } else {
      const text = await response.text()
      ElMessage.error('Word 导出失败：' + text)
    }
  } catch (err) {
    ElMessage.error('Word 导出失败：' + err.message)
    console.error(err)
  }
}

const downloadMd = async () => {
  ElMessage.info('正在导出 Markdown 格式...')
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()
    if (json.status === 'success' && json.content) {
      const blob = new Blob([json.content], { type: 'text/markdown;charset=utf-8' })
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = 'lecture.md'
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
      ElMessage.success('Markdown 文件已成功导出')
    } else {
      ElMessage.error('获取讲义内容失败')
    }
  } catch (err) {
    ElMessage.error('Markdown 导出失败')
    console.error(err)
  }
}

const polishLecture = async () => {
  if (isPolishing.value) return

  try {
    isPolishing.value = true
    ElMessage.info('正在整理讲义，请稍候...')

    const payload = {
      lecture_id: actualLectureId.value,
      task_id: globalStore.realtime_task_id || ''
    }

    const response = await fetch('http://127.0.0.1:8001/realtime/polish/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    })

    const data = await response.json()

    if (!data.success) {
      ElMessage.error(data.message || '讲义整理失败')
      return
    }

    const polishedContent = data.content || ''

    // 你的 Result.vue 原本会先 parseImageMarkers 再 markdown 渲染
    // 这里保持兼容：如果是非实时 [IMAGE:xxx] 会被转换；
    // 如果是实时 Markdown 图片链接，会直接渲染。
    const contentWithImages = parseImageMarkers(polishedContent)
    const fixed = fixLatexInline(contentWithImages)
    renderedHtml.value = md.render(fixed)

    editContent.value = polishedContent
    editOriginalContent.value = polishedContent

    await nextTick()
    renderMath()

    ElMessage.success('讲义整理完成')
  } catch (err) {
    console.error('一键整理失败:', err)
    ElMessage.error('一键整理失败，请检查后端服务')
  } finally {
    isPolishing.value = false
  }
}

const editLecture = async () => {
  // 从页面内容中提取标题（从 markdown 文件路径或标题元素）
  const titleEl = document.querySelector('.lecture-header .page-title')
  let currentTitle = titleEl?.textContent?.replace('讲义内容', '').trim() || '未命名讲义'
  
  // 从渲染的 HTML 中提取原始 markdown 内容
  let currentContent = ''
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()
    if (json.status === 'success') {
      currentContent = json.content || ''
    }
  } catch (e) {
    console.error('获取讲义内容失败:', e)
  }
  
  editTitle.value = currentTitle
  editContent.value = currentContent
  editOriginalTitle.value = currentTitle
  editOriginalContent.value = currentContent
  hasChanges.value = false
  lastSaved.value = ''
  showPreview.value = false
  editDialogVisible.value = true
}

const markAsChanged = () => {
  if (editTitle.value === editOriginalTitle.value && editContent.value === editOriginalContent.value) {
    hasChanges.value = false
  } else {
    hasChanges.value = true
  }
}

const insertFormat = (before, after) => {
  const textarea = editorTextarea.value
  if (!textarea) return
  
  const start = textarea.selectionStart
  const end = textarea.selectionEnd
  const selectedText = editContent.value.substring(start, end)
  
  // 在选中文本前后插入格式符号
  const newText = editContent.value.substring(0, start) + before + selectedText + after + editContent.value.substring(end)
  editContent.value = newText
  
  // 设置光标位置
  nextTick(() => {
    if (selectedText) {
      textarea.selectionStart = start + before.length
      textarea.selectionEnd = end + before.length
    } else {
      textarea.selectionStart = textarea.selectionEnd = start + before.length
    }
    textarea.focus()
  })
  
  markAsChanged()
}

const handleKeydown = (e) => {
  // Ctrl+S 保存
  if (e.ctrlKey && e.key === 's') {
    e.preventDefault()
    saveLecture()
  }
  // Tab 插入缩进
  if (e.key === 'Tab') {
    e.preventDefault()
    insertFormat('  ', '')
  }
}

const togglePreview = async (show) => {
  if (show) {
    const md = new MarkdownIt({ html: true })
    const fixed = fixLatexInline(editContent.value)
    previewHtml.value = md.render(fixed)
    await nextTick()
    if (window.MathJax) {
      window.MathJax.typesetPromise?.()
    }
  }
}

// 保存讲义
const saveLecture = async () => {
  // 验证标题
  if (!editTitle.value.trim()) {
    ElMessage.error('请输入讲义标题')
    return
  }
  
  if (editTitle.value.length > 200) {
    ElMessage.error('标题不能超过200个字符')
    return
  }
  
  if (editContent.value.length > 1000000) {
    ElMessage.error('内容过大，请精简')
    return
  }
  
  isSaving.value = true
  try {
    console.log('保存讲义 - actualLectureId:', actualLectureId.value, 'lectureId:', currentLectureId.value)
    
    const response = await fetch(`http://127.0.0.1:8001/lectures/${currentLectureId.value}/save/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Token ${authStore.token}`
      },
      body: JSON.stringify({
        title: editTitle.value,
        content: editContent.value
      })
    })
    
    console.log('响应状态:', response.status)
    const result = await response.json()
    console.log('响应结果:', result)
    
    if (result.success) {
      editOriginalTitle.value = editTitle.value
      editOriginalContent.value = editContent.value
      hasChanges.value = false
      lastSaved.value = new Date().toLocaleTimeString()
      ElMessage.success('讲义已保存')
      
      // 更新 store 中的数据
      const index = lectureStore.lectures.findIndex(l => l.id === currentLectureId.value)
      if (index !== -1) {
        lectureStore.lectures[index] = { ...lectureStore.lectures[index], ...result.lecture }
      }
      
      // 更新页面上的标题
      const titleEl = document.querySelector('.lecture-header .page-title')
      if (titleEl) {
        titleEl.innerHTML = `<i class="el-icon-document"></i> ${editTitle.value}`
      }
      
      // 刷新页面上的讲义内容预览
      await loadLectureContent()
    } else {
      ElMessage.error(result.message || '保存失败')
    }
  } catch (err) {
    console.error('保存讲义失败:', err)
    ElMessage.error('保存失败: ' + err.message)
  } finally {
    isSaving.value = false
  }
}

// 取消编辑
const cancelEdit = async () => {
  if (hasChanges.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的更改，确定要放弃吗？',
        '提示',
        {
          confirmButtonText: '放弃',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }
      )
      editDialogVisible.value = false
    } catch {
      // 用户取消，继续编辑
    }
  } else {
    editDialogVisible.value = false
  }
}

const goHome = async () => {
  if (hasChanges.value) {
    try {
      await ElMessageBox.confirm(
        '您有未保存的更改，确定要返回吗？',
        '提示',
        {
          confirmButtonText: '放弃并返回',
          cancelButtonText: '继续编辑',
          type: 'warning'
        }
      )
      await globalStore.fullReset()
      router.push('/')
    } catch {
      // 用户取消
    }
  } else {
    await globalStore.fullReset()
    router.push('/')
  }
}

// 加载讲义内容
const loadLectureContent = async () => {
  try {
    const res = await fetch('http://127.0.0.1:8001/get_ocr_summary')
    const json = await res.json()
    console.log('get_ocr_summary 响应:', json)

    if (json.status === 'success' && json.content) {
      // 尝试从响应中获取 lecture_id
      if (json.lecture_id) {
        actualLectureId.value = json.lecture_id
      } else if (json.id) {
        actualLectureId.value = json.id
      }
      
      // 调试：打印原始内容
      console.log('原始内容:', json.content)
      
      // 调试：检查是否包含图片标记
      const hasImageMarker = json.content.includes('[IMAGE:')
      const hasMarkdownImage = json.content.includes('![图片]')
      console.log('是否包含图片标记 [IMAGE:', hasImageMarker)
      console.log('是否包含 Markdown 图片:', hasMarkdownImage)
      
      // 先处理 Latex
      const fixed = fixLatexInline(json.content)
      
      // 如果后端返回的是 [IMAGE:...] 标记，则解析为<img>标签
      // 如果后端返回的是 Markdown 图片语法，则直接让 MarkdownIt 解析
      let contentWithImages = fixed
      if (hasImageMarker) {
        contentWithImages = parseImageMarkers(fixed)
      }
      console.log('解析后内容:', contentWithImages)
      
      // 配置 MarkdownIt，确保 HTML 标签能正确渲染
      const md = new MarkdownIt({
        html: true,
        xhtmlOut: true,
        breaks: true,
        linkify: true
      })
      
      const html = md.render(contentWithImages)
      console.log('最终 HTML:', html)
      
      renderedHtml.value = html

      await nextTick()
      renderMath()
    } else {
      error.value = '后端返回失败：' + (json.message || '未知错误')
    }
  } catch (err) {
    error.value = '获取总结失败，请检查后端服务是否启动'
    console.error(err)
  }
}

onMounted(async () => {
  // 加载视频
  await loadVideo()
  
  // 加载讲义内容
  await loadLectureContent()
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

/* 编辑对话框样式 */
.edit-dialog {
  border-radius: 20px;
  overflow: hidden;
}

.edit-dialog-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 10px;
}

.edit-dialog-header h2 {
  margin: 0;
  font-size: 1.3rem;
  color: #5c4d82;
}

.save-status {
  font-size: 0.85rem;
  color: #999;
}

.save-status.success {
  color: #67c23a;
}

.edit-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.edit-toolbar {
  background: #f8f6fc;
  border-radius: 12px;
  padding: 15px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.title-input-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.title-input-wrapper label {
  font-weight: 600;
  color: #5c4d82;
  white-space: nowrap;
}

.title-input {
  flex: 1;
  padding: 10px 15px;
  border: 2px solid #e8e4f0;
  border-radius: 8px;
  font-size: 1rem;
  transition: border-color 0.3s;
}

.title-input:focus {
  outline: none;
  border-color: #5c4d82;
}

.char-count {
  font-size: 0.8rem;
  color: #999;
  white-space: nowrap;
}

.format-buttons {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.format-buttons button {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid #e8e4f0;
  background: #fff;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  transition: all 0.2s;
  color: #5c4d82;
}

.format-buttons button:hover {
  background: #5c4d82;
  color: #fff;
  border-color: #5c4d82;
}

.editor-wrapper {
  border: 2px solid #e8e4f0;
  border-radius: 12px;
  overflow: hidden;
}

.editor-textarea {
  width: 100%;
  min-height: 400px;
  padding: 20px;
  border: none;
  resize: vertical;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.95rem;
  line-height: 1.6;
  box-sizing: border-box;
}

.editor-textarea:focus {
  outline: none;
  box-shadow: inset 0 0 0 2px rgba(92, 77, 130, 0.2);
}

.preview-toggle {
  display: flex;
  align-items: center;
  justify-content: flex-end;
}

.preview-wrapper {
  border: 2px solid #e8e4f0;
  border-radius: 12px;
  padding: 20px;
  background: #fafafa;
  max-height: 500px;
  overflow-y: auto;
}

.preview-title {
  margin: 0 0 15px 0;
  font-size: 1rem;
  color: #5c4d82;
  border-bottom: 2px solid #e8e4f0;
  padding-bottom: 10px;
}

.preview-content {
  font-size: 0.95rem;
  line-height: 1.8;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  padding: 10px 0;
}

.btn-cancel {
  padding: 12px 24px;
  border: 2px solid #e8e4f0;
  background: #fff;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  color: #666;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-cancel:hover {
  border-color: #999;
  color: #333;
}

.btn-save {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 12px 24px;
  border: none;
  background: #5c4d82;
  border-radius: 10px;
  font-size: 1rem;
  font-weight: 600;
  color: #fff;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-save:hover {
  background: #4a3c6e;
  transform: translateY(-2px);
}

/* Element Plus 覆盖样式 */
:deep(.el-dialog__header) {
  padding: 20px 30px 10px;
  border-bottom: 2px solid #f0ecf7;
  margin-right: 0;
}

:deep(.el-dialog__body) {
  padding: 20px 30px;
}

:deep(.el-dialog__footer) {
  padding: 10px 30px 20px;
  border-top: 2px solid #f0ecf7;
}

:deep(.el-switch) {
  --el-switch-off-color: #e8e4f0;
  --el-color-primary: #5c4d82;
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
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
  margin-bottom: 20px;
  padding-bottom: 20px;
  border-bottom: 2px solid #f0ecf7;
}

.action-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 14px 24px;
  font-size: 1rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #5c4d82;
  background: #5c4d82;
  color: #ffffff;
  width: 100%;
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

/* 帧图片样式 */
.markdown-body :deep(.frame-image) {
  max-width: 300px !important;
  height: auto;
  border-radius: 12px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.15);
  margin: 1em 0;
  display: block;
}

/* 确保 MarkdownIt 渲染的图片也应用样式 */
.markdown-body :deep(img) {
  max-width: 300px;
  height: auto;
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

.polish-btn {
  background: linear-gradient(135deg, #7c5cff 0%, #5c4d82 100%) !important;
  color: #ffffff !important;
}

.polish-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}
</style>
