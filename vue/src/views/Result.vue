<template>
  <div class="result-wrapper">
    <div class="btns">
      <button class="download-btn" @click="downloadPdf">下载 PDF</button>
    </div>
    <div ref="markdownContent" v-html="renderedHtml" class="markdown-body" />
    <div v-if="error" class="error">{{ error }}</div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import MarkdownIt from 'markdown-it'

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
  await renderMath() // 确保公式渲染完毕
  window.open('http://127.0.0.1:8001/generate_pdf', '_blank')
}
</script>

<style scoped>
.result-wrapper {
  max-width: 860px;
  margin: 40px auto;
  padding: 40px 30px;
  background-color: #fff;
  border-radius: 12px;
  box-shadow: 0 4px 24px rgba(0, 0, 0, 0.08);
  font-size: 16px;
  line-height: 1.75;
  font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
  color: #2c3e50;
  position: relative;
}

.markdown-body h1,
.markdown-body h2,
.markdown-body h3 {
  margin-top: 1.6em;
  margin-bottom: 0.6em;
  color: #1f2f3f;
  border-bottom: 1px solid #e0e0e0;
  padding-bottom: 0.3em;
}

.markdown-body p {
  margin: 1em 0;
  word-break: break-word;
}

.markdown-body ul,
.markdown-body ol {
  padding-left: 2em;
  margin-bottom: 1em;
}

.markdown-body li {
  margin-bottom: 0.4em;
}

.markdown-body code {
  font-family: monospace;
  background-color: #f5f5f5;
  padding: 2px 6px;
  border-radius: 4px;
  color: #d6336c;
}

.download-btn {
  display: inline-block;
  background-color: #4f46e5;
  color: #fff;
  font-weight: bold;
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.2);
  cursor: pointer;
  transition: background-color 0.3s;
}

.download-btn:hover {
  background-color: #3730a3;
}

.btns {
  text-align: right;
  margin-bottom: 24px;
}

.error {
  color: red;
  text-align: center;
  padding: 20px;
  background-color: #fff3f3;
  border: 1px solid #f5c2c7;
  border-radius: 8px;
  margin-top: 20px;
}
</style>
