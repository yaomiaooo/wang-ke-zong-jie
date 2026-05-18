<template>
  <div class="annotation-page">
    <div class="content-wrapper">
      <div class="page-header">
        <h1 class="page-title">
          <i class="el-icon-edit"></i>
          板书区域标注
        </h1>
        <p class="page-subtitle">调整识别区域以获得更精确的板书内容</p>
      </div>

      <div class="annotation-content">
        <div class="image-section">
          <div ref="imgContainer" class="image-container">
            <img :src="frameImgUrl" alt="Frame" v-show="frameImgUrl" />
            <div
              v-for="(r, idx) in regions"
              :key="idx"
              class="region"
              :style="{
                left: r.x + 'px',
                top: r.y + 'px',
                width: r.width + 'px',
                height: r.height + 'px',
                border: idx === selectedIndex ? '3px solid #409EFF' : '2px solid #409EFF'
              }"
              @click="selectRegion(idx)"
              :data-index="idx"
            ></div>
          </div>
        </div>

        <div class="control-panel">
          <div class="control-section">
            <h3>
              <i class="el-icon-setting"></i>
              区域控制
            </h3>
            <div class="button-group">
              <el-button @click="addRegion" type="primary" size="large">
                <i class="el-icon-plus"></i>
                新增区域
              </el-button>
              <el-button @click="deleteRegion" type="danger" size="large" :disabled="selectedIndex === null">
                <i class="el-icon-delete"></i>
                删除选中
              </el-button>
            </div>
          </div>

          <div class="help-section">
            <h3>
              <i class="el-icon-info"></i>
              操作说明
            </h3>
            <div class="help-content">
              <div class="help-item">
                <i class="el-icon-mouse"></i>
                <span>点击区域可选中</span>
              </div>
              <div class="help-item">
                <i class="el-icon-rank"></i>
                <span>拖拽可移动位置</span>
              </div>
              <div class="help-item">
                <i class="el-icon-full-screen"></i>
                <span>拖拽边角可调整大小</span>
              </div>
            </div>
          </div>

          <div class="navigation-section">
            <el-button type="primary" @click="onNext" size="large" class="next-button">
              <i class="el-icon-right"></i>
              下一步
            </el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick } from 'vue'
import interact from 'interactjs'
import axios from 'axios'
import { useRouter } from 'vue-router'

export default {
  setup() {
    const router = useRouter()
    const frameImgUrl = ref('')
    const regions = ref([])
    const selectedIndex = ref(null)

    const fetchData = async () => {
      try {
        // 第1步：发送get请求让后端取帧获得图片
        const statusRes = await axios.get('http://127.0.0.1:8001/extract_key_frame')
        if (statusRes.data.special_frame_extraction_status !== 'success') {
            throw new Error('后端关键帧提取失败')
        }

        // 第2步：发送get请求让后端生成矩形信息
        const initRes = await axios.get('http://127.0.0.1:8001/auto_rectangle')
        if (initRes.data.rectangle_extraction_status !== 'success') {
            throw new Error('后端板书区域自动识别失败')
        }

        // 第3步：并行发送 /api/vertices 和 /api/frame
        const [verticesRes, frameRes] = await Promise.all([
          axios.get('http://127.0.0.1:8001/user_get_rectangles'),
          axios.get('http://127.0.0.1:8001/user_get_special_frame', {
            responseType: 'blob'
          })
        ])

        // 显示图像
        const blob = new Blob([frameRes.data], { type: 'image/jpeg' })
        frameImgUrl.value = URL.createObjectURL(blob)

        // 转换顶点数据为 {x, y, width, height}
        regions.value = (verticesRes.data.regions || []).map(corners => {
          const xs = [corners[0], corners[2], corners[4], corners[6]]
          const ys = [corners[1], corners[3], corners[5], corners[7]]
          const x = Math.min(...xs)
          const y = Math.min(...ys)
          const width = Math.max(...xs) - x
          const height = Math.max(...ys) - y
          return { x, y, width, height }
        })

        await nextTick()
        initInteractions()

      } catch (err) {
        console.error('数据加载失败:', err)
      }
    }

    // 初始化拖拽与缩放
    const initInteractions = () => {
      interact('.region')
        .draggable({
          modifiers: [interact.modifiers.restrict({ restriction: 'parent' })],
          inertia: true,
        })
        .resizable({
          edges: { left: true, right: true, bottom: true, top: true },
          modifiers: [interact.modifiers.restrictSize({ min: { width: 20, height: 20 } })],
          inertia: true,
        })
        .on('dragmove', event => {
          const idx = +event.target.getAttribute('data-index')
          regions.value[idx].x += event.dx
          regions.value[idx].y += event.dy
        })
        .on('resizemove', event => {
          const idx = +event.target.getAttribute('data-index')
          const delta = event.deltaRect
          regions.value[idx].x += delta.left
          regions.value[idx].y += delta.top
          regions.value[idx].width = event.rect.width
          regions.value[idx].height = event.rect.height
        })
    }

    const selectRegion = idx => {
      selectedIndex.value = idx
    }

    const addRegion = () => {
      regions.value.push({ x: 20, y: 20, width: 100, height: 100 })
    }

    const deleteRegion = () => {
      if (selectedIndex.value !== null) {
        regions.value.splice(selectedIndex.value, 1)
        selectedIndex.value = null
      }
    }

    const onNext = async () => {
      // 提交所有矩形的四点坐标（左上，右上，右下，左下）
      const payload = {
        rectangles: regions.value.map(r => [
          [r.x, r.y],
          [r.x + r.width, r.y],
          [r.x + r.width, r.y + r.height],
          [r.x, r.y + r.height]
        ])
      }

      try {
        await axios.post('http://127.0.0.1:8001/user_change_rectangles', payload)
        router.push('/information')
      } catch (err) {
        console.error('提交区域失败:', err)
      }
    }

    onMounted(fetchData)

    return {
      frameImgUrl,
      regions,
      selectedIndex,
      selectRegion,
      addRegion,
      deleteRegion,
      onNext,
    }
  }
}
</script>

<style scoped>
.annotation-page { 
  padding: 40px 20px; 
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.content-wrapper {
  max-width: 1400px;
  margin: 0 auto;
  background: white;
  border-radius: 20px;
  padding: 40px;
  box-shadow: 0 20px 40px rgba(0,0,0,0.1);
}

.page-header {
  text-align: center;
  margin-bottom: 40px;
}

.page-title {
  font-size: 2.2rem;
  font-weight: bold;
  color: #333;
  margin-bottom: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 15px;
}

.page-title i {
  color: #667eea;
}

.page-subtitle {
  color: #666;
  font-size: 1.1rem;
  margin: 0;
}

.annotation-content {
  display: grid;
  grid-template-columns: 1fr 300px;
  gap: 30px;
  align-items: start;
}

.image-section {
  display: flex;
  justify-content: center;
  align-items: flex-start;
  overflow: auto;
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
  padding: 20px;
  border: 2px solid #e9ecef;
}

.image-container { 
  position: relative; 
  overflow: auto;
  width: 100%;
  max-width: unset;
}

.image-container img {
  display: block;
  width: auto;
  height: auto;
  max-width: none;
  max-height: none;
  user-select: none;
  pointer-events: none;
  border-radius: 10px;
}

.region {
  position: absolute;
  box-sizing: border-box;
  background-color: rgba(64,159,255, 0.2);
  cursor: move;
  border-radius: 4px;
  transition: all 0.2s ease;
}

.region:hover {
  background-color: rgba(64,159,255, 0.3);
}

.control-panel {
  display: flex;
  flex-direction: column;
  gap: 30px;
}

.control-section,
.help-section,
.navigation-section {
  background: linear-gradient(145deg, #f8f9fa, #e9ecef);
  border-radius: 15px;
  padding: 25px;
}

.control-section h3,
.help-section h3 {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #333;
}

.control-section h3 i,
.help-section h3 i {
  color: #667eea;
}

.button-group {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.button-group .el-button {
  justify-content: flex-start;
  font-weight: 500;
}

.help-content {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.help-item {
  display: flex;
  align-items: center;
  gap: 12px;
  color: #666;
  font-size: 0.95rem;
}

.help-item i {
  color: #667eea;
  font-size: 1.1rem;
  width: 20px;
}

.navigation-section {
  text-align: center;
}

.next-button {
  background: linear-gradient(135deg, #667eea, #764ba2);
  border: none;
  width: 100%;
  height: 50px;
  font-size: 1.1rem;
  font-weight: 600;
  transition: all 0.3s ease;
}

.next-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(102, 126, 234, 0.4);
}

@media (max-width: 1024px) {
  .annotation-content {
    grid-template-columns: 1fr;
    gap: 20px;
  }
  
  .control-panel {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
  }
}

@media (max-width: 768px) {
  .content-wrapper {
    padding: 25px 20px;
  }
  
  .control-panel {
    grid-template-columns: 1fr;
  }
}
</style>
