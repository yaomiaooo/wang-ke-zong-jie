<template>
  <div class="lecture-list">
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    <div class="decoration decoration-3"></div>
    
    <div class="container">
      <div class="header-section">
        <div class="brand-badge">
          <span class="brand-icon">📚</span>
          <span class="brand-text">我的讲义</span>
        </div>
        <div class="header-actions">
          <button class="add-btn" @click="showCategoryDialog = true">
            <i class="el-icon-folder-add"></i>
            管理分类
          </button>
        </div>
      </div>

      <div class="filter-section">
        <div class="filter-tabs">
          <button 
            class="filter-tab" 
            :class="{ active: filters.status === '' }"
            @click="setStatusFilter('')"
          >
            全部
          </button>
          <button 
            class="filter-tab" 
            :class="{ active: filters.status === 'completed' }"
            @click="setStatusFilter('completed')"
          >
            已完成
          </button>
          <button 
            class="filter-tab" 
            :class="{ active: filters.status === 'processing' }"
            @click="setStatusFilter('processing')"
          >
            处理中
          </button>
          <button 
            class="filter-tab" 
            :class="{ active: filters.status === 'archived' }"
            @click="setStatusFilter('archived')"
          >
            已存档
          </button>
        </div>
        
        <div class="filter-row">
          <div class="search-wrapper">
            <i class="el-icon-search"></i>
            <input
              v-model="filters.search"
              type="text"
              class="search-input"
              placeholder="搜索讲义标题..."
              @input="handleSearch"
            />
          </div>

          <select v-model="filters.category_id" class="filter-select" @change="loadLectures">
            <option value="">全部分类</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <div class="loading-spinner"></div>
        <span>加载中...</span>
      </div>

      <div v-else-if="lectures.length === 0" class="empty-state">
        <div class="empty-icon">
          <i class="el-icon-folder-opened"></i>
        </div>
        <h3>暂无讲义</h3>
        <p>上传视频开始创建您的第一份讲义吧</p>
        <button class="start-btn" @click="router.push('/')">
          上传视频
        </button>
      </div>

      <div v-else class="lectures-grid">
        <div v-for="lecture in lectures" :key="lecture.id" class="lecture-card">
          <div class="lecture-header">
            <span
              class="status-badge"
              :class="'status-' + lecture.status"
            >
              {{ getStatusText(lecture.status) }}
            </span>
            <span v-if="lecture.category" class="category-tag" :style="{ backgroundColor: lecture.category.color }">
              {{ lecture.category.name }}
            </span>
          </div>

          <h3 class="lecture-title">{{ lecture.title }}</h3>
          <p class="lecture-subject" v-if="lecture.subject">科目: {{ lecture.subject }}</p>
          <p class="lecture-preview">{{ lecture.summary_preview }}</p>

          <div class="lecture-tags" v-if="lecture.tags?.length">
            <span v-for="tag in lecture.tags.slice(0, 3)" :key="tag" class="tag">
              {{ tag }}
            </span>
            <span v-if="lecture.tags.length > 3" class="tag more">
              +{{ lecture.tags.length - 3 }}
            </span>
          </div>

          <div class="lecture-footer">
            <span class="lecture-date">{{ formatDate(lecture.created_at) }}</span>
            <div class="lecture-actions">
              <button
                v-if="lecture.status === 'completed'"
                class="action-btn view-btn"
                @click="viewLecture(lecture)"
              >
                查看
              </button>
              <button
                class="action-btn edit-btn"
                @click="openEditDialog(lecture)"
              >
                编辑
              </button>
              <button
                v-if="lecture.has_pdf"
                class="action-btn download-btn"
                @click="downloadPdf(lecture)"
              >
                下载PDF
              </button>
              <button
                v-if="lecture.status !== 'archived'"
                class="action-btn archive-btn"
                @click="confirmArchive(lecture)"
              >
                存档
              </button>
              <button
                v-if="lecture.status === 'archived'"
                class="action-btn restore-btn"
                @click="confirmRestore(lecture)"
              >
                恢复
              </button>
              <button
                class="action-btn delete-btn"
                @click="confirmDelete(lecture)"
              >
                删除
              </button>
            </div>
          </div>
        </div>
      </div>

      <div v-if="pagination.total_pages > 1" class="pagination">
        <button
          class="page-btn"
          :disabled="pagination.page === 1"
          @click="changePage(pagination.page - 1)"
        >
          上一页
        </button>
        <span class="page-info">
          第 {{ pagination.page }} / {{ pagination.total_pages }} 页
        </span>
        <button
          class="page-btn"
          :disabled="pagination.page === pagination.total_pages"
          @click="changePage(pagination.page + 1)"
        >
          下一页
        </button>
      </div>

      <!-- 分类管理对话框 -->
      <el-dialog
        v-model="showCategoryDialog"
        title="分类管理"
        width="500px"
        class="category-dialog"
        :close-on-click-modal="false"
      >
        <div class="add-category">
          <input
            v-model="newCategory.name"
            type="text"
            placeholder="新分类名称"
            class="input-warm"
          />
          <input
            v-model="newCategory.color"
            type="color"
            class="color-picker"
          />
          <button class="btn-primary" @click="handleAddCategory">
            添加
          </button>
        </div>

        <div class="category-list">
          <div v-for="cat in categories" :key="cat.id" class="category-item">
            <span class="category-color" :style="{ backgroundColor: cat.color }"></span>
            <span class="category-name">{{ cat.name }}</span>
            <span class="category-count">({{ cat.lecture_count }})</span>
            <div class="category-actions">
              <button class="icon-btn edit-btn" @click="editCategory(cat)">
                <i class="el-icon-edit"></i>
              </button>
              <button class="icon-btn delete-btn" @click="confirmDeleteCategory(cat)">
                <i class="el-icon-delete"></i>
              </button>
            </div>
          </div>
        </div>
      </el-dialog>

      <!-- 编辑讲义对话框 -->
      <el-dialog
        v-model="showEditDialog"
        title="编辑讲义"
        width="600px"
        class="edit-dialog"
        :close-on-click-modal="false"
      >
        <form @submit.prevent="handleUpdateLecture" class="edit-form">
          <div class="form-group">
            <label>讲义标题</label>
            <input
              v-model="editForm.title"
              type="text"
              class="input-warm"
              placeholder="请输入讲义标题"
            />
          </div>
          
          <div class="form-group">
            <label>科目</label>
            <input
              v-model="editForm.subject"
              type="text"
              class="input-warm"
              placeholder="请输入科目"
            />
          </div>
          
          <div class="form-group">
            <label>分类</label>
            <select v-model="editForm.category_id" class="input-warm">
              <option value="">无分类</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
          
          <div class="form-group">
            <label>标签（用逗号分隔）</label>
            <input
              v-model="editForm.tags_input"
              type="text"
              class="input-warm"
              placeholder="如: 数学, 公式, 重点"
            />
          </div>
          
          <div class="dialog-footer">
            <button type="button" class="btn-secondary" @click="showEditDialog = false">
              取消
            </button>
            <button type="submit" class="btn-primary" :disabled="saving">
              {{ saving ? '保存中...' : '保存' }}
            </button>
          </div>
        </form>
      </el-dialog>

      <!-- 讲义详情对话框 -->
      <el-dialog
        v-model="showLectureDialog"
        :title="currentLecture?.title"
        width="800px"
        class="lecture-dialog"
        :close-on-click-modal="false"
      >
        <div class="lecture-content">
          <div v-html="renderedContent"></div>
        </div>
      </el-dialog>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useLectureStore } from '@/stores/lecture'
import { ElMessage, ElMessageBox } from 'element-plus'
import MarkdownIt from 'markdown-it'

export default {
  name: 'LectureList',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const lectureStore = useLectureStore()

    const lectures = ref([])
    const categories = ref([])
    const loading = ref(false)
    const saving = ref(false)
    const showCategoryDialog = ref(false)
    const showLectureDialog = ref(false)
    const showEditDialog = ref(false)
    const currentLecture = ref(null)

    const filters = ref({
      search: '',
      category_id: '',
      status: ''
    })

    const pagination = ref({
      page: 1,
      page_size: 10,
      total: 0,
      total_pages: 0
    })

    const newCategory = ref({
      name: '',
      color: '#5c4d82'
    })

    const editForm = ref({
      id: null,
      title: '',
      subject: '',
      category_id: '',
      tags_input: ''
    })

    const md = new MarkdownIt({ html: true })

    const renderedContent = computed(() => {
      if (!currentLecture.value?.summary_file) return ''
      return md.render(currentLecture.value.summary_file)
    })

    const setStatusFilter = (status) => {
      filters.value.status = status
      loadLectures(1)
    }

    const loadLectures = async (page = 1) => {
      loading.value = true
      try {
        lectureStore.setAuthHeader(authStore.token)
        const params = {
          page,
          ...filters.value
        }
        Object.keys(params).forEach(key => {
          if (!params[key]) delete params[key]
        })

        const res = await lectureStore.fetchLectures(params)
        if (res.success) {
          lectures.value = res.lectures
          pagination.value = {
            page: res.page,
            page_size: res.page_size,
            total: res.total,
            total_pages: res.total_pages
          }
        }
      } catch (err) {
        console.error('加载讲义失败:', err)
        if (err.response?.status === 401) {
          router.push('/login')
        }
      } finally {
        loading.value = false
      }
    }

    const loadCategories = async () => {
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

    const handleSearch = () => {
      clearTimeout(window.searchTimer)
      window.searchTimer = setTimeout(() => {
        loadLectures(1)
      }, 500)
    }

    const changePage = (page) => {
      loadLectures(page)
    }

    const getStatusText = (status) => {
      const map = {
        completed: '已完成',
        processing: '处理中',
        failed: '失败',
        archived: '已存档'
      }
      return map[status] || status
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }

    const viewLecture = async (lecture) => {
      try {
        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.fetchLecture(lecture.id)
        if (res.success) {
          currentLecture.value = res.lecture
          showLectureDialog.value = true
        }
      } catch (err) {
        ElMessage.error('加载讲义详情失败')
      }
    }

    const openEditDialog = (lecture) => {
      editForm.value = {
        id: lecture.id,
        title: lecture.title,
        subject: lecture.subject || '',
        category_id: lecture.category?.id || '',
        tags_input: lecture.tags?.join(', ') || ''
      }
      showEditDialog.value = true
    }

    const handleUpdateLecture = async () => {
      if (!editForm.value.title.trim()) {
        ElMessage.warning('请输入讲义标题')
        return
      }

      saving.value = true
      try {
        lectureStore.setAuthHeader(authStore.token)
        const data = {
          title: editForm.value.title,
          subject: editForm.value.subject,
          category_id: editForm.value.category_id || null
        }
        
        if (editForm.value.tags_input) {
          data.tags = editForm.value.tags_input.split(',').map(t => t.trim()).filter(t => t)
        }

        const res = await lectureStore.updateLecture(editForm.value.id, data)
        if (res.success) {
          ElMessage.success('讲义更新成功')
          showEditDialog.value = false
          loadLectures(pagination.value.page)
        }
      } catch (err) {
        ElMessage.error('更新讲义失败')
      } finally {
        saving.value = false
      }
    }

    const downloadPdf = (lecture) => {
      window.open(`http://127.0.0.1:8001/generate_pdf?lecture_id=${lecture.id}`, '_blank')
    }

    const confirmArchive = async (lecture) => {
      try {
        await ElMessageBox.confirm(
          `确定要将讲义"${lecture.title}"存档吗？存档后可在"已存档"标签页中查看。`,
          '存档确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )

        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.archiveLecture(lecture.id)
        if (res.success) {
          ElMessage.success('讲义已存档')
          loadLectures(pagination.value.page)
        }
      } catch (err) {
        if (err !== 'cancel') {
          ElMessage.error('存档失败')
        }
      }
    }

    const confirmRestore = async (lecture) => {
      try {
        await ElMessageBox.confirm(
          `确定要恢复讲义"${lecture.title}"吗？恢复后可正常访问。`,
          '恢复确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'info'
          }
        )

        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.restoreLecture(lecture.id)
        if (res.success) {
          ElMessage.success('讲义已恢复')
          loadLectures(pagination.value.page)
        }
      } catch (err) {
        if (err !== 'cancel') {
          ElMessage.error('恢复失败')
        }
      }
    }

    const confirmDelete = async (lecture) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除讲义"${lecture.title}"吗？此操作不可恢复。`,
          '删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.deleteLecture(lecture.id)
        if (res.success) {
          ElMessage.success('删除成功')
          loadLectures(pagination.value.page)
        }
      } catch (err) {
        if (err !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    const handleAddCategory = async () => {
      if (!newCategory.value.name.trim()) {
        ElMessage.warning('请输入分类名称')
        return
      }

      try {
        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.createCategory(newCategory.value)
        if (res.success) {
          ElMessage.success('分类创建成功')
          newCategory.value = { name: '', color: '#5c4d82' }
          loadCategories()
        }
      } catch (err) {
        ElMessage.error('创建分类失败')
      }
    }

    const editCategory = async (category) => {
      const { value: newName } = await ElMessageBox.prompt('请输入新的分类名称', '编辑分类', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputValue: category.name
      })

      if (newName) {
        try {
          lectureStore.setAuthHeader(authStore.token)
          const res = await lectureStore.updateCategory(category.id, { name: newName })
          if (res.success) {
            ElMessage.success('分类更新成功')
            loadCategories()
          }
        } catch (err) {
          ElMessage.error('更新分类失败')
        }
      }
    }

    const confirmDeleteCategory = async (category) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除分类"${category.name}"吗？该操作不会删除分类下的讲义。`,
          '删除确认',
          {
            confirmButtonText: '确定',
            cancelButtonText: '取消',
            type: 'warning'
          }
        )

        lectureStore.setAuthHeader(authStore.token)
        const res = await lectureStore.deleteCategory(category.id)
        if (res.success) {
          ElMessage.success('分类删除成功')
          loadCategories()
        }
      } catch (err) {
        if (err !== 'cancel') {
          ElMessage.error('删除失败')
        }
      }
    }

    onMounted(() => {
      if (!authStore.isAuthenticated) {
        router.push('/login')
        return
      }
      loadLectures()
      loadCategories()
    })

    return {
      lectures,
      categories,
      loading,
      saving,
      showCategoryDialog,
      showLectureDialog,
      showEditDialog,
      currentLecture,
      filters,
      pagination,
      newCategory,
      editForm,
      renderedContent,
      loadLectures,
      handleSearch,
      changePage,
      setStatusFilter,
      getStatusText,
      formatDate,
      viewLecture,
      openEditDialog,
      handleUpdateLecture,
      downloadPdf,
      confirmArchive,
      confirmRestore,
      confirmDelete,
      handleAddCategory,
      editCategory,
      confirmDeleteCategory,
      router
    }
  }
}
</script>

<style scoped>
.lecture-list {
  min-height: 100vh;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #f5f0e8 0%, #e8e0f0 100%);
}

.decoration {
  position: absolute;
  border-radius: 100%;
  opacity: 0.4;
}

.decoration-1 {
  width: 500px;
  height: 500px;
  background: #5c4d82;
  top: -150px;
  left: -150px;
}

.decoration-2 {
  width: 400px;
  height: 400px;
  background: #9b8dc7;
  bottom: -100px;
  right: -100px;
}

.decoration-3 {
  width: 250px;
  height: 250px;
  background: #7eb89e;
  top: 40%;
  right: 5%;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
  position: relative;
  z-index: 1;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
  background: #ffffff;
  padding: 24px 32px;
  border-radius: 20px;
  box-shadow: 0 8px 30px rgba(92, 77, 130, 0.12);
}

.brand-badge {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  background: rgba(92, 77, 130, 0.1);
  padding: 14px 28px;
  border-radius: 50px;
}

.brand-icon {
  font-size: 1.3rem;
}

.brand-text {
  font-weight: 700;
  font-size: 1.1rem;
  color: #5c4d82;
}

.header-actions {
  display: flex;
  gap: 12px;
}

.add-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.add-btn:hover {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.filter-section {
  margin-bottom: 30px;
}

.filter-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
  background: #ffffff;
  padding: 12px 20px;
  border-radius: 16px;
  box-shadow: 0 4px 15px rgba(92, 77, 130, 0.08);
}

.filter-tab {
  padding: 10px 22px;
  border: 2px solid transparent;
  border-radius: 10px;
  background: transparent;
  color: #5c5c5c;
  font-weight: 600;
  font-size: 0.95rem;
  cursor: pointer;
  transition: all 0.3s ease;
}

.filter-tab:hover {
  color: #5c4d82;
  background: rgba(92, 77, 130, 0.08);
}

.filter-tab.active {
  background: #5c4d82;
  color: #ffffff;
  border-color: #5c4d82;
}

.filter-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.search-wrapper {
  flex: 1;
  min-width: 250px;
  position: relative;
}

.search-wrapper i {
  position: absolute;
  left: 18px;
  top: 50%;
  transform: translateY(-50%);
  color: #9b8fc2;
  font-size: 1.1rem;
}

.search-input {
  width: 100%;
  padding: 14px 18px 14px 48px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  background: #ffffff;
  transition: all 0.3s;
  box-sizing: border-box;
}

.search-input:focus {
  outline: none;
  border-color: #5c4d82;
  box-shadow: 0 0 0 4px rgba(92, 77, 130, 0.1);
}

.filter-select {
  padding: 14px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  background: #ffffff;
  min-width: 150px;
  cursor: pointer;
  transition: all 0.3s;
}

.filter-select:focus {
  outline: none;
  border-color: #5c4d82;
}

.loading {
  text-align: center;
  padding: 80px 40px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(92, 77, 130, 0.12);
}

.loading-spinner {
  width: 48px;
  height: 48px;
  border: 4px solid #e8e8e8;
  border-top-color: #5c4d82;
  border-radius: 50%;
  margin: 0 auto 20px;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.empty-state {
  text-align: center;
  padding: 80px 40px;
  background: #ffffff;
  border-radius: 24px;
  box-shadow: 0 8px 30px rgba(92, 77, 130, 0.12);
}

.empty-icon {
  width: 100px;
  height: 100px;
  background: rgba(92, 77, 130, 0.1);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 24px;
}

.empty-icon i {
  font-size: 3rem;
  color: #5c4d82;
}

.empty-state h3 {
  margin: 0 0 12px 0;
  font-size: 1.5rem;
  color: #2d2d2d;
  font-family: 'Georgia', serif;
}

.empty-state p {
  margin: 0 0 30px 0;
  color: #888;
  font-size: 1rem;
}

.start-btn {
  padding: 14px 32px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.start-btn:hover {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.lectures-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.lecture-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 8px 25px rgba(92, 77, 130, 0.1);
  transition: all 0.3s ease;
}

.lecture-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(92, 77, 130, 0.15);
}

.lecture-header {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.status-badge {
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-completed {
  background: rgba(126, 184, 158, 0.2);
  color: #4a7c63;
}

.status-processing {
  background: rgba(235, 168, 124, 0.2);
  color: #b56b6b;
}

.status-failed {
  background: rgba(235, 150, 150, 0.2);
  color: #c62828;
}

.status-archived {
  background: rgba(155, 143, 194, 0.2);
  color: #5c4d82;
}

.category-tag {
  padding: 5px 14px;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #ffffff;
}

.lecture-title {
  margin: 0 0 10px 0;
  font-size: 1.25rem;
  color: #2d2d2d;
  font-weight: 600;
  font-family: 'Georgia', serif;
}

.lecture-subject {
  margin: 0 0 10px 0;
  font-size: 0.9rem;
  color: #9b8fc2;
}

.lecture-preview {
  margin: 0 0 16px 0;
  font-size: 0.95rem;
  color: #666;
  line-height: 1.6;
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.lecture-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 16px;
}

.tag {
  padding: 5px 12px;
  background: rgba(92, 77, 130, 0.08);
  border-radius: 15px;
  font-size: 0.8rem;
  color: #5c4d82;
}

.tag.more {
  background: #f0f0f0;
  color: #888;
}

.lecture-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

.lecture-date {
  font-size: 0.85rem;
  color: #9b8fc2;
}

.lecture-actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.action-btn {
  padding: 8px 14px;
  border-radius: 8px;
  font-size: 0.8rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.view-btn {
  background: #5c4d82;
  color: #ffffff;
}

.edit-btn {
  background: rgba(155, 143, 194, 0.2);
  color: #5c4d82;
}

.download-btn {
  background: #7eb89f;
  color: #ffffff;
}

.archive-btn {
  background: rgba(235, 168, 124, 0.2);
  color: #b56b6b;
}

.restore-btn {
  background: rgba(126, 184, 158, 0.2);
  color: #4a7c63;
}

.delete-btn {
  background: rgba(235, 150, 150, 0.2);
  color: #c62828;
}

.action-btn:hover {
  transform: translateY(-2px);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  gap: 20px;
  margin-top: 40px;
}

.page-btn {
  padding: 12px 24px;
  background: #ffffff;
  border: 2px solid #5c4d82;
  border-radius: 12px;
  color: #5c4d82;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.page-btn:hover:not(:disabled) {
  background: #5c4d82;
  color: #ffffff;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  color: #666;
  font-size: 0.95rem;
}

/* 对话框样式 */
.add-category {
  display: flex;
  gap: 12px;
  margin-bottom: 24px;
}

.input-warm {
  padding: 14px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s;
  background: #fafafa;
}

.input-warm:focus {
  outline: none;
  border-color: #5c4d82;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(92, 77, 130, 0.1);
}

.color-picker {
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
  padding: 0;
}

.btn-primary {
  padding: 12px 24px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-primary:hover:not(:disabled) {
  background: #4a3d6e;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  padding: 12px 24px;
  background: #ffffff;
  color: #5c5c5c;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
}

.btn-secondary:hover {
  border-color: #5c4d82;
  color: #5c4d82;
}

.category-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.category-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px 20px;
  background: linear-gradient(135deg, #faf9fc 0%, #f5f0fa 100%);
  border-radius: 12px;
}

.category-color {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  flex-shrink: 0;
}

.category-name {
  flex: 1;
  font-weight: 600;
  color: #2d2d2d;
}

.category-count {
  color: #9b8fc2;
  font-size: 0.9rem;
}

.category-actions {
  display: flex;
  gap: 8px;
}

.icon-btn {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.icon-btn.edit-btn {
  background: rgba(25, 118, 210, 0.1);
  color: #1976d2;
}

.icon-btn.delete-btn {
  background: rgba(198, 40, 40, 0.1);
  color: #c62828;
}

.icon-btn:hover {
  transform: scale(1.1);
}

/* 编辑对话框样式 */
.edit-form {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-group label {
  font-weight: 600;
  font-size: 0.875rem;
  color: #2d2d2d;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 12px;
}

.lecture-content {
  padding: 10px;
  max-height: 60vh;
  overflow-y: auto;
}

/* Element Plus 覆盖样式 */
:deep(.el-dialog) {
  border-radius: 20px;
}

:deep(.el-dialog__header) {
  padding: 24px 30px;
  border-bottom: 2px solid #f0f0f0;
}

:deep(.el-dialog__title) {
  font-family: 'Georgia', serif;
  font-size: 1.3rem;
  color: #2d2d2d;
}

:deep(.el-dialog__body) {
  padding: 30px;
}

@media (max-width: 768px) {
  .filter-tabs {
    flex-wrap: wrap;
  }
  
  .filter-row {
    flex-direction: column;
  }

  .search-wrapper,
  .filter-select {
    width: 100%;
  }

  .lectures-grid {
    grid-template-columns: 1fr;
  }

  .lecture-footer {
    flex-direction: column;
    gap: 15px;
  }

  .lecture-actions {
    width: 100%;
    justify-content: flex-end;
  }

  .header-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .header-actions {
    width: 100%;
    justify-content: center;
  }
  
  .add-btn {
    width: 100%;
    justify-content: center;
  }
}
</style>
