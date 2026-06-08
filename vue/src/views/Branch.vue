<template>
  <div class="branch-container">
    <!-- 装饰元素 -->
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    
    <div class="branch-content">
      <!-- 左侧主内容区域 -->
      <div class="main-section">
        <div class="content-card">
          <div class="card-header">
            <h1 class="page-title">
              <i class="el-icon-setting"></i>
              板书区域设置
            </h1>
            <p class="page-subtitle">选择是否需要固定板书识别区域</p>
          </div>

          <div class="form-section">
            <div class="toggle-section">
              <div class="toggle-label">
                <span class="label-text">板书区域固定</span>
              </div>
              <div class="toggle-buttons">
                <button 
                  class="toggle-btn" 
                  :class="{ active: form.fixed }"
                  @click="toggleFixed(true)"
                >
                  <i class="el-icon-check"></i>
                  是
                </button>
                <button 
                  class="toggle-btn" 
                  :class="{ active: !form.fixed }"
                  @click="toggleFixed(false)"
                >
                  <i class="el-icon-close"></i>
                  否
                </button>
              </div>
            </div>

            <div class="description-text">
              {{ form.fixed ? '将手动选择板书区域进行精准识别' : '使用完整画面进行自动识别' }}
            </div>
          </div>

          <div class="explanation-section">
            <div class="explanation-header">
              <i class="el-icon-info"></i>
              <span>功能说明</span>
            </div>
            <div class="explanation-grid">
              <div class="explanation-card" :class="{ active: form.fixed }">
                <div class="card-icon fixed-icon">
                  <i class="el-icon-lock"></i>
                </div>
                <h3>固定区域模式</h3>
                <p>用户可以精确控制视频中被识别的区域，有效避免无用信息（如教室环境、装饰等）干扰识别结果，适合板书位置相对固定的场景。</p>
              </div>
              <div class="explanation-card" :class="{ active: !form.fixed }">
                <div class="card-icon auto-icon">
                  <i class="el-icon-unlock"></i>
                </div>
                <h3>完整画面模式</h3>
                <p>自动识别将直接使用完整画面进行分析，适合板书位置变化较大或需要识别整个画面内容的场景。</p>
              </div>
            </div>
          </div>

          <div class="button-section">
            <button class="nav-button prev-btn" @click="onPrev">
              <i class="el-icon-arrow-left"></i>
              上一步
            </button>
            <button class="nav-button next-btn" @click="onNext">
              下一步
              <i class="el-icon-arrow-right"></i>
            </button>
          </div>
        </div>
      </div>

      <!-- 右侧内容区域 -->
      <div class="right-section">
        <!-- 板书框选区域 -->
        <transition name="fade">
          <div class="annotation-card" v-if="form.fixed">
            <div class="annotation-header">
              <h2 class="annotation-title">
                <i class="el-icon-edit"></i>
                板书区域标注
              </h2>
              <p class="annotation-subtitle">调整识别区域以获得更精确的板书内容</p>
            </div>

            <div class="image-container-wrapper">
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

            <div class="annotation-controls">
              <div class="control-row">
                <button class="control-btn add-btn" @click="addRegion">
                  <i class="el-icon-plus"></i>
                  新增区域
                </button>
                <button 
                  class="control-btn delete-btn" 
                  @click="deleteRegion" 
                  :disabled="selectedIndex === null"
                >
                  <i class="el-icon-delete"></i>
                  删除选中
                </button>
              </div>
            </div>

            <div class="annotation-help">
              <h4>
                <i class="el-icon-info"></i>
                操作提示
              </h4>
              <ul>
                <li><i class="el-icon-mouse"></i>点击区域可选中</li>
                <li><i class="el-icon-rank"></i>拖拽可移动位置</li>
                <li><i class="el-icon-full-screen"></i>拖拽边角可调整大小</li>
              </ul>
            </div>
          </div>
        </transition>

        <!-- 视频预览区域 -->
        <transition name="fade">
          <div class="video-preview-card" v-if="!form.fixed">
            <div class="preview-header">
              <h2 class="preview-title">
                <i class="el-icon-video-camera"></i>
                视频预览
              </h2>
              <p class="preview-subtitle">使用完整画面进行自动识别</p>
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
              <span>视频时长: {{ formatDuration(videoDuration) }}</span>
            </div>

            <div class="preview-tips">
              <div class="tip-item">
                <i class="el-icon-circle-check"></i>
                <span>自动识别完整画面内容</span>
              </div>
              <div class="tip-item">
                <i class="el-icon-circle-check"></i>
                <span>适合板书位置变化的场景</span>
              </div>
            </div>
          </div>
        </transition>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, nextTick, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useGlobalStore } from '../stores/global'
import interact from 'interactjs'
import axios from 'axios'

export default {
  setup() {
    const router = useRouter()
    const globalStore = useGlobalStore()

    const form = ref({ fixed: false })
    const frameImgUrl = ref('')
    const regions = ref([])
    const selectedIndex = ref(null)

    const videoUrl = ref('')
    const videoPlayer = ref(null)
    const videoDuration = ref(0)

    const imgContainer = ref(null)

    // 图片显示尺寸
    const displayWidth = ref(0)
    const displayHeight = ref(0)

    // 图片原始尺寸
    const originalWidth = ref(0)
    const originalHeight = ref(0)

    const VIDEO_API_URL = 'http://127.0.0.1:8001/get_current_video/'

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

    const loadVideo = async () => {
      try {
        const response = await fetch(VIDEO_API_URL)
        if (response.ok) {
          videoUrl.value = VIDEO_API_URL
        }
      } catch (err) {
        console.error('获取视频失败:', err)
      }
    }

    const toggleFixed = async (value) => {
      form.value.fixed = value

      if (value) {
        await fetchFrameAndRegions()
      } else {
        await loadVideo()
      }
    }

    /**
     * 等待图片加载完成，并记录：
     * 1. 图片原始尺寸 naturalWidth / naturalHeight
     * 2. 图片页面显示尺寸 offsetWidth / offsetHeight
     */
    const waitImageLoaded = () => {
      return new Promise((resolve, reject) => {
        nextTick(() => {
          const img = imgContainer.value?.querySelector('img')

          if (!img) {
            reject(new Error('图片元素不存在，请检查模板中 imgContainer 是否绑定正确'))
            return
          }

          const updateSize = () => {
            originalWidth.value = img.naturalWidth
            originalHeight.value = img.naturalHeight
            displayWidth.value = img.offsetWidth
            displayHeight.value = img.offsetHeight

            console.log('图片原始尺寸:', originalWidth.value, originalHeight.value)
            console.log('图片显示尺寸:', displayWidth.value, displayHeight.value)

            if (
              originalWidth.value <= 0 ||
              originalHeight.value <= 0 ||
              displayWidth.value <= 0 ||
              displayHeight.value <= 0
            ) {
              reject(new Error('图片尺寸获取失败'))
              return
            }

            resolve()
          }

          if (img.complete && img.naturalWidth > 0) {
            updateSize()
          } else {
            img.onload = updateSize
            img.onerror = () => reject(new Error('图片加载失败'))
          }
        })
      })
    }

    /**
     * 后端返回的是原始图片坐标，需要转成页面显示坐标。
     *
     * 后端格式：
     * [
     *   [x1,y1,x2,y2,x3,y3,x4,y4],
     *   ...
     * ]
     *
     * 前端格式：
     * [
     *   { x, y, width, height },
     *   ...
     * ]
     */
    const convertOriginalRegionsToDisplay = (rawRegions) => {
      if (
        !rawRegions ||
        !Array.isArray(rawRegions) ||
        !originalWidth.value ||
        !originalHeight.value ||
        !displayWidth.value ||
        !displayHeight.value
      ) {
        return []
      }

      const scaleX = displayWidth.value / originalWidth.value
      const scaleY = displayHeight.value / originalHeight.value

      console.log('原图坐标 -> 显示坐标 scaleX:', scaleX, 'scaleY:', scaleY)

      return rawRegions.map(corners => {
        const xs = [corners[0], corners[2], corners[4], corners[6]]
        const ys = [corners[1], corners[3], corners[5], corners[7]]

        const minX = Math.min(...xs)
        const minY = Math.min(...ys)
        const maxX = Math.max(...xs)
        const maxY = Math.max(...ys)

        return {
          x: Math.round(minX * scaleX),
          y: Math.round(minY * scaleY),
          width: Math.round((maxX - minX) * scaleX),
          height: Math.round((maxY - minY) * scaleY)
        }
      })
    }

    /**
     * 从后端获取关键帧和矩形区域。
     * 注意：
     * 必须先显示图片并等待图片加载完成，再把后端原始坐标转换为前端显示坐标。
     */
    const fetchFrameAndRegions = async () => {
      try {
        regions.value = []
        selectedIndex.value = null

        // 第1步：让后端提取关键帧
        const statusRes = await axios.get('http://127.0.0.1:8001/extract_key_frame')
        if (statusRes.data.special_frame_extraction_status !== 'success') {
          throw new Error('后端关键帧提取失败')
        }

        // 第2步：让后端自动生成矩形信息
        const initRes = await axios.get('http://127.0.0.1:8001/auto_rectangle')
        if (initRes.data.rectangle_extraction_status !== 'success') {
          throw new Error('后端板书区域自动识别失败')
        }

        console.log('自动矩形检测结果:', initRes.data)

        // 第3步：获取矩形坐标和关键帧图片
        const [verticesRes, frameRes] = await Promise.all([
          axios.get('http://127.0.0.1:8001/user_get_rectangles'),
          axios.get('http://127.0.0.1:8001/user_get_special_frame', {
            responseType: 'blob'
          })
        ])

        console.log('后端返回的原始矩形坐标:', verticesRes.data)

        // 第4步：显示图像
        const blob = new Blob([frameRes.data], { type: 'image/jpeg' })

        if (frameImgUrl.value) {
          URL.revokeObjectURL(frameImgUrl.value)
        }

        frameImgUrl.value = URL.createObjectURL(blob)

        // 第5步：等待图片加载完成，获取图片原始尺寸和显示尺寸
        await waitImageLoaded()

        // 第6步：把后端原始图片坐标转换为前端显示坐标
        regions.value = convertOriginalRegionsToDisplay(verticesRes.data.regions || [])

        console.log('转换后的前端显示区域:', regions.value)

        await nextTick()

        setTimeout(() => {
          initInteractions()
        }, 100)

      } catch (err) {
        console.error('数据加载失败:', err)
      }
    }

    const initInteractions = () => {
      if (!imgContainer.value) {
        return
      }

      const img = imgContainer.value.querySelector('img')

      if (img) {
        displayWidth.value = img.offsetWidth
        displayHeight.value = img.offsetHeight
        originalWidth.value = img.naturalWidth
        originalHeight.value = img.naturalHeight

        console.log('initInteractions 图片原始尺寸:', originalWidth.value, originalHeight.value)
        console.log('initInteractions 图片显示尺寸:', displayWidth.value, displayHeight.value)
      }

      // 避免重复绑定 interact
      interact('.region').unset()

      interact('.region')
        .draggable({
          modifiers: [
            interact.modifiers.restrict({
              restriction: 'parent',
              endOnly: true
            })
          ],
          inertia: true
        })
        .resizable({
          edges: { left: true, right: true, bottom: true, top: true },
          modifiers: [
            interact.modifiers.restrictSize({
              min: { width: 20, height: 20 },
              max: {
                width: displayWidth.value || 9999,
                height: displayHeight.value || 9999
              }
            }),
            interact.modifiers.restrictEdges({
              outer: 'parent',
              endOnly: true
            })
          ],
          inertia: true
        })
        .on('dragmove', event => {
          const idx = Number(event.target.getAttribute('data-index'))

          if (Number.isNaN(idx) || !regions.value[idx]) {
            return
          }

          regions.value[idx].x += event.dx
          regions.value[idx].y += event.dy

          regions.value[idx].x = Math.max(
            0,
            Math.min(
              regions.value[idx].x,
              displayWidth.value - regions.value[idx].width
            )
          )

          regions.value[idx].y = Math.max(
            0,
            Math.min(
              regions.value[idx].y,
              displayHeight.value - regions.value[idx].height
            )
          )
        })
        .on('resizemove', event => {
          const idx = Number(event.target.getAttribute('data-index'))

          if (Number.isNaN(idx) || !regions.value[idx]) {
            return
          }

          const delta = event.deltaRect

          let newX = regions.value[idx].x + delta.left
          let newY = regions.value[idx].y + delta.top
          let newWidth = Math.max(20, event.rect.width)
          let newHeight = Math.max(20, event.rect.height)

          // 限制宽高不要超过显示图片范围
          newWidth = Math.min(newWidth, displayWidth.value)
          newHeight = Math.min(newHeight, displayHeight.value)

          newX = Math.max(0, Math.min(newX, displayWidth.value - newWidth))
          newY = Math.max(0, Math.min(newY, displayHeight.value - newHeight))

          regions.value[idx].x = newX
          regions.value[idx].y = newY
          regions.value[idx].width = newWidth
          regions.value[idx].height = newHeight
        })
    }

    const selectRegion = idx => {
      selectedIndex.value = idx
    }

    const addRegion = () => {
      // 如果图片已经加载，就放在图片中间附近
      const defaultWidth = Math.min(200, displayWidth.value || 200)
      const defaultHeight = Math.min(120, displayHeight.value || 120)

      const x = displayWidth.value
        ? Math.max(0, Math.round((displayWidth.value - defaultWidth) / 2))
        : 20

      const y = displayHeight.value
        ? Math.max(0, Math.round((displayHeight.value - defaultHeight) / 2))
        : 20

      regions.value.push({
        x,
        y,
        width: defaultWidth,
        height: defaultHeight
      })

      nextTick(() => {
        initInteractions()
      })
    }

    const deleteRegion = () => {
      if (selectedIndex.value !== null) {
        regions.value.splice(selectedIndex.value, 1)
        selectedIndex.value = null

        nextTick(() => {
          initInteractions()
        })
      }
    }

    const onPrev = () => {
      router.back()
    }

    const onNext = async () => {
      globalStore.setAdvanced(form.value.fixed)

      if (form.value.fixed) {
        if (
          !originalWidth.value ||
          !originalHeight.value ||
          !displayWidth.value ||
          !displayHeight.value
        ) {
          try {
            await waitImageLoaded()
          } catch (err) {
            console.error('提交前获取图片尺寸失败:', err)
            return
          }
        }

        // 前端显示坐标 -> 后端原始图片坐标
        const scaleX = originalWidth.value / displayWidth.value
        const scaleY = originalHeight.value / displayHeight.value

        console.log('显示坐标 -> 原图坐标 scaleX:', scaleX, 'scaleY:', scaleY)

        const payload = {
          rectangles: regions.value.map(r => [
            [
              Math.round(r.x * scaleX),
              Math.round(r.y * scaleY)
            ],
            [
              Math.round((r.x + r.width) * scaleX),
              Math.round(r.y * scaleY)
            ],
            [
              Math.round((r.x + r.width) * scaleX),
              Math.round((r.y + r.height) * scaleY)
            ],
            [
              Math.round(r.x * scaleX),
              Math.round((r.y + r.height) * scaleY)
            ]
          ])
        }

        console.log('提交给后端的原图坐标:', payload)

        try {
          await axios.post('http://127.0.0.1:8001/user_change_rectangles', payload)
        } catch (err) {
          console.error('提交区域失败:', err)
        }
      }

      router.push('/information')
    }

    const handleResize = async () => {
      if (!form.value.fixed || !frameImgUrl.value) {
        return
      }

      // 页面尺寸变化时，简单处理：重新拉取后端矩形并转换。
      // 这样可以避免窗口大小变化后坐标错位。
      await fetchFrameAndRegions()
    }

    onMounted(() => {
      loadVideo()
      window.addEventListener('resize', handleResize)
    })

    onBeforeUnmount(() => {
      window.removeEventListener('resize', handleResize)
      interact('.region').unset()

      if (frameImgUrl.value) {
        URL.revokeObjectURL(frameImgUrl.value)
      }
    })

    return {
      form,
      frameImgUrl,
      regions,
      selectedIndex,
      videoUrl,
      videoPlayer,
      videoDuration,
      imgContainer,
      formatDuration,
      onVideoLoaded,
      toggleFixed,
      selectRegion,
      addRegion,
      deleteRegion,
      onPrev,
      onNext
    }
  }
}
</script>

<style scoped>
.branch-container {
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

.branch-content {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 30px;
  max-width: 1600px;
  width: 100%;
  position: relative;
  z-index: 1;
}

/* 左侧主内容区域 */
.main-section {
  display: flex;
  align-items: center;
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

/* 切换区域 */
.form-section {
  margin-bottom: 40px;
}

.toggle-section {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.toggle-label {
  margin-bottom: 10px;
}

.label-text {
  font-size: 1.125rem;
  font-weight: 600;
  color: #2d2d2d;
}

.toggle-buttons {
  display: flex;
  gap: 15px;
}

.toggle-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 32px;
  border-radius: 12px;
  font-size: 1.05rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #d4c8e0;
  background: #faf9fc;
  color: #5c5c5c;
}

.toggle-btn:hover {
  border-color: #5c4d82;
  background: #f0ecf7;
}

.toggle-btn.active {
  border-color: #5c4d82;
  background: #5c4d82;
  color: #ffffff;
}

.toggle-btn.active i {
  color: #ffffff;
}

.toggle-btn i {
  color: #5c4d82;
}

.description-text {
  font-size: 1rem;
  color: #888;
  text-align: center;
  margin-top: 5px;
}

/* 功能说明区域 */
.explanation-section {
  margin-bottom: 45px;
}

.explanation-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 25px;
  font-size: 1.2rem;
  font-weight: 600;
  color: #2d2d2d;
}

.explanation-header i {
  color: #5c4d82;
}

.explanation-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.explanation-card {
  background: #faf9fc;
  border-radius: 16px;
  padding: 28px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
}

.explanation-card.active {
  border-color: #5c4d82;
  background: rgba(92, 77, 130, 0.05);
}

.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20px;
  font-size: 1.5rem;
}

.fixed-icon {
  background: rgba(92, 77, 130, 0.15);
  color: #5c4d82;
}

.auto-icon {
  background: rgba(126, 184, 158, 0.2);
  color: #4a7c63;
}

.explanation-card h3 {
  font-size: 1.15rem;
  font-weight: 600;
  color: #2d2d2d;
  margin: 0 0 12px 0;
}

.explanation-card p {
  font-size: 0.95rem;
  color: #5c5c5c;
  line-height: 1.7;
  margin: 0;
}

/* 按钮区域 */
.button-section {
  display: flex;
  gap: 20px;
}

.nav-button {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 52px;
  font-size: 1.1rem;
  font-weight: 600;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.prev-btn {
  border: 2px solid #5c4d82;
  background: transparent;
  color: #5c4d82;
}

.prev-btn:hover {
  background: rgba(92, 77, 130, 0.1);
}

.next-btn {
  border: 2px solid #5c4d82;
  background: #5c4d82;
  color: #ffffff;
}

.next-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 25px rgba(92, 77, 130, 0.35);
}

/* 右侧内容区域 */
.right-section {
  display: flex;
  align-items: flex-start;
}

.annotation-card,
.video-preview-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 35px;
  box-shadow: 0 20px 60px rgba(92, 77, 130, 0.15);
  width: 100%;
}

.annotation-header,
.preview-header {
  text-align: center;
  margin-bottom: 25px;
}

.annotation-title,
.preview-title {
  font-family: 'Georgia', serif;
  font-size: 1.5rem;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #2d2d2d;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
}

.annotation-title i,
.preview-title i {
  color: #5c4d82;
}

.annotation-subtitle,
.preview-subtitle {
  font-size: 0.95rem;
  color: #888;
  margin: 0;
}

.image-container-wrapper {
  background: #e8e8e8;
  border-radius: 16px;
  padding: 20px;
  margin-bottom: 25px;
  overflow: hidden;
}

.image-container {
  position: relative;
  display: inline-block;
  line-height: 0;
}

.image-container img {
  display: block;
  width: 100%;
  height: auto;
}

.frame-img {
  display: block;
  width: 100%;
  height: auto;
}

.region {
  position: absolute;
  border: 2px solid #409eff;
  box-sizing: border-box;
}

.region:hover {
  background-color: rgba(92, 77, 130, 0.35);
}

.annotation-controls {
  margin-bottom: 25px;
}

.control-row {
  display: flex;
  gap: 12px;
}

.control-btn {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  height: 46px;
  font-size: 0.95rem;
  font-weight: 600;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s ease;
  border: 2px solid #d4c8e0;
  background: #faf9fc;
  color: #5c4d82;
}

.control-btn:hover:not(:disabled) {
  border-color: #5c4d82;
  background: #f0ecf7;
}

.control-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.delete-btn {
  border-color: #dfb5b5;
  color: #8b4a4a;
}

.delete-btn:hover:not(:disabled) {
  border-color: #8b4a4a;
  background: rgba(223, 181, 181, 0.2);
}

.annotation-help {
  background: #faf9fc;
  border-radius: 12px;
  padding: 20px;
}

.annotation-help h4 {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 1rem;
  font-weight: 600;
  color: #2d2d2d;
  margin: 0 0 15px 0;
}

.annotation-help h4 i {
  color: #5c4d82;
}

.annotation-help ul {
  list-style: none;
  padding: 0;
  margin: 0;
}

.annotation-help li {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 0;
  font-size: 0.9rem;
  color: #5c5c5c;
}

.annotation-help li i {
  color: #5c4d82;
  width: 18px;
}

/* 视频预览区域样式 */
.video-wrapper {
  background: #1a1a1a;
  border-radius: 16px;
  overflow: hidden;
  margin-bottom: 20px;
  position: relative;
  width: 100%;
  padding-bottom: 56.25%;
}

.video-wrapper video {
  display: block;
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-info {
  text-align: center;
  color: #5c5c5c;
  font-size: 0.9rem;
  margin-bottom: 25px;
}

.preview-tips {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.tip-item {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #888;
  font-size: 0.9rem;
}

.tip-item i {
  color: #7eb89e;
  font-size: 1.1rem;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: all 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 响应式设计 */
@media (max-width: 1400px) {
  .branch-content {
    grid-template-columns: 1fr 400px;
  }
}

@media (max-width: 1200px) {
  .branch-content {
    grid-template-columns: 1fr;
  }
  
  .annotation-section {
    order: 2;
  }
  
  .main-section {
    order: 1;
  }
}

@media (max-width: 768px) {
  .branch-container {
    padding: 30px 15px;
  }
  
  .content-card {
    padding: 35px 25px;
  }
  
  .page-title {
    font-size: 1.8rem;
  }
  
  .explanation-grid {
    grid-template-columns: 1fr;
  }
  
  .button-section {
    flex-direction: column;
  }
  
  .toggle-btn {
    padding: 12px 24px;
  }
  
  .annotation-card {
    padding: 25px 20px;
  }
}
</style>
