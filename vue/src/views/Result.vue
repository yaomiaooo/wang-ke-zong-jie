<template>
  <div class="result-wrapper">
    <div class="btns">
      <button class="home-btn" @click="goHome">
        <i class="el-icon-home"></i>
        返回首页
      </button>
      <button class="download-btn" @click="downloadPdf">
        <i class="el-icon-download"></i>
        下载 PDF
      </button>
    </div>
    <div ref="markdownContent" v-html="renderedHtml" class="markdown-body" />
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import MarkdownIt from 'markdown-it'

const router = useRouter()
const globalStore = useGlobalStore()

const renderedHtml = ref('')
const markdownContent = ref(null)
const error = ref('')

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

onMounted(async () => {
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
.result-wrapper {
  max-width: 860px;
  margin: 40px auto;
  padding: 50px;
  background-color: #ffffff;
  border-radius: 24px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.12);
  font-size: 16px;
  line-height: 1.8;
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  color: #2d2d2d;
  position: relative;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin-top: 1.8em;
  margin-bottom: 0.8em;
  color: #2d2d2d;
  border-bottom: 2px solid #e8e8e8;
  padding-bottom: 0.4em;
  font-weight: 600;
}

.markdown-body h1 {
  font-size: 1.8rem;
}

.markdown-body h2 {
  font-size: 1.5rem;
}

.markdown-body h3 {
  font-size: 1.3rem;
}

.markdown-body p {
  margin: 1.2em 0;
  word-break: break-word;
  color: #5c5c5c;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 1.8em;
  margin-bottom: 1.2em;
  color: #5c5c5c;
}

.markdown-body li {
  margin-bottom: 0.6em;
}

.markdown-body code {
  font-family: 'Courier New', monospace;
  background-color: #e8e8e8;
  padding: 4px 10px;
  border-radius: 8px;
  color: #5c4d82;
  font-size: 0.9em;
}

.btns {
  display: flex;
  justify-content: flex-end;
  gap: 15px;
  margin-bottom: 30px;
}

.home-btn,
.download-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  padding: 14px 28px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
  font-size: 1rem;
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

.error {
  color: #8b4a4a;
  text-align: center;
  padding: 25px;
  background-color: #fcebeb;
  border: 2px solid #dfb5b5;
  border-radius: 16px;
  margin-top: 30px;
}

@media (max-width: 768px) {
  .result-wrapper {
    padding: 30px 20px;
    margin: 20px;
  }
  
  .btns {
    flex-direction: column;
    align-items: stretch;
  }
  
  .home-btn,
  .download-btn {
    justify-content: center;
  }
}
</style>
