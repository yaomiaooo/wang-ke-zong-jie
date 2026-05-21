<template>
  <div class="lecture-list">
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">
          <i class="el-icon-folder-opened"></i>
          我的讲义
        </h1>
        <button class="add-btn" @click="showCategoryDialog = true">
          <i class="el-icon-folder-add"></i>
          管理分类
        </button>
      </div>

      <div class="filter-section">
        <div class="filter-row">
          <input
            v-model="filters.search"
            type="text"
            class="search-input"
            placeholder="搜索讲义标题..."
            @input="handleSearch"
          />

          <select v-model="filters.category_id" class="filter-select" @change="loadLectures">
            <option value="">全部分类</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>

          <select v-model="filters.status" class="filter-select" @change="loadLectures">
            <option value="">全部状态</option>
            <option value="completed">已完成</option>
            <option value="processing">处理中</option>
            <option value="failed">处理失败</option>
          </select>
        </div>
      </div>

      <div v-if="loading" class="loading">
        <i class="el-icon-loading"></i> 加载中...
      </div>

      <div v-else-if="lectures.length === 0" class="empty-state">
        <i class="el-icon-folder-delete"></i>
        <p>暂无讲义</p>
        <p class="hint">上传视频开始创建您的第一份讲义吧</p>
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
                v-if="lecture.has_pdf"
                class="action-btn download-btn"
                @click="downloadPdf(lecture)"
              >
                下载PDF
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
      <div v-if="showCategoryDialog" class="dialog-overlay" @click.self="showCategoryDialog = false">
        <div class="dialog">
          <div class="dialog-header">
            <h3>分类管理</h3>
            <button class="close-btn" @click="showCategoryDialog = false">
              <i class="el-icon-close"></i>
            </button>
          </div>

          <div class="dialog-body">
            <div class="add-category">
              <input
                v-model="newCategory.name"
                type="text"
                placeholder="新分类名称"
                class="input-field"
              />
              <input
                v-model="newCategory.color"
                type="color"
                class="color-picker"
              />
              <button class="add-category-btn" @click="handleAddCategory">
                添加
              </button>
            </div>

            <div class="category-list">
              <div v-for="cat in categories" :key="cat.id" class="category-item">
                <span class="category-color" :style="{ backgroundColor: cat.color }"></span>
                <span class="category-name">{{ cat.name }}</span>
                <span class="category-count">({{ cat.lecture_count }})</span>
                <div class="category-actions">
                  <button class="edit-btn" @click="editCategory(cat)">
                    <i class="el-icon-edit"></i>
                  </button>
                  <button class="delete-btn" @click="confirmDeleteCategory(cat)">
                    <i class="el-icon-delete"></i>
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 讲义详情对话框 -->
      <div v-if="showLectureDialog" class="dialog-overlay" @click.self="showLectureDialog = false">
        <div class="dialog lecture-dialog">
          <div class="dialog-header">
            <h3>{{ currentLecture?.title }}</h3>
            <button class="close-btn" @click="showLectureDialog = false">
              <i class="el-icon-close"></i>
            </button>
          </div>

          <div class="dialog-body lecture-content">
            <div v-html="renderedContent"></div>
          </div>
        </div>
      </div>
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
    const showCategoryDialog = ref(false)
    const showLectureDialog = ref(false)
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

    const md = new MarkdownIt({ html: true })

    const renderedContent = computed(() => {
      if (!currentLecture.value?.summary_file) return ''
      return md.render(currentLecture.value.summary_file)
    })

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
        failed: '失败'
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

    const downloadPdf = (lecture) => {
      window.open(`http://127.0.0.1:8001/generate_pdf?lecture_id=${lecture.id}`, '_blank')
    }

    const confirmDelete = async (lecture) => {
      try {
        await ElMessageBox.confirm(
          `确定要删除讲义"${lecture.title}"吗？`,
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
      showCategoryDialog,
      showLectureDialog,
      currentLecture,
      filters,
      pagination,
      newCategory,
      renderedContent,
      loadLectures,
      handleSearch,
      changePage,
      getStatusText,
      formatDate,
      viewLecture,
      downloadPdf,
      confirmDelete,
      handleAddCategory,
      editCategory,
      confirmDeleteCategory
    }
  }
}
</script>

<style scoped>
.lecture-list {
  min-height: 100vh;
  background: linear-gradient(135deg, #c4b5e0 0%, #e8e8e8 100%);
  padding: 40px 20px;
}

.container {
  max-width: 1200px;
  margin: 0 auto;
}

.header-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 30px;
}

.page-title {
  font-size: 2.2rem;
  font-weight: 600;
  color: #2d2d2d;
  display: flex;
  align-items: center;
  gap: 15px;
}

.page-title i {
  color: #5c4d82;
}

.add-btn {
  padding: 12px 24px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.add-btn:hover {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.filter-section {
  margin-bottom: 30px;
}

.filter-row {
  display: flex;
  gap: 15px;
  flex-wrap: wrap;
}

.search-input,
.filter-select {
  padding: 12px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  background: #ffffff;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.filter-select {
  min-width: 150px;
}

.loading,
.empty-state {
  text-align: center;
  padding: 60px;
  color: #5c5c5c;
  font-size: 1.1rem;
}

.empty-state i {
  font-size: 4rem;
  color: #9b8fc2;
  margin-bottom: 20px;
}

.empty-state .hint {
  font-size: 0.9rem;
  color: #9b8fc2;
}

.lectures-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 25px;
}

.lecture-card {
  background: #ffffff;
  border-radius: 20px;
  padding: 25px;
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08);
  transition: all 0.3s ease;
}

.lecture-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 12px 35px rgba(0, 0, 0, 0.12);
}

.lecture-header {
  display: flex;
  gap: 10px;
  margin-bottom: 15px;
}

.status-badge {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  font-weight: 600;
}

.status-completed {
  background: #e8f5e9;
  color: #2e7d32;
}

.status-processing {
  background: #fff3e0;
  color: #ef6c00;
}

.status-failed {
  background: #ffebee;
  color: #c62828;
}

.category-tag {
  padding: 4px 12px;
  border-radius: 20px;
  font-size: 0.8rem;
  color: #ffffff;
}

.lecture-title {
  margin: 0 0 10px 0;
  font-size: 1.25rem;
  color: #2d2d2d;
  font-weight: 600;
}

.lecture-subject {
  margin: 0 0 10px 0;
  font-size: 0.9rem;
  color: #9b8fc2;
}

.lecture-preview {
  margin: 0 0 15px 0;
  font-size: 0.95rem;
  color: #5c5c5c;
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
  margin-bottom: 15px;
}

.tag {
  padding: 4px 10px;
  background: #f0f0f0;
  border-radius: 15px;
  font-size: 0.8rem;
  color: #5c5c5c;
}

.tag.more {
  background: #e8e8e8;
}

.lecture-footer {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding-top: 15px;
  border-top: 1px solid #f0f0f0;
}

.lecture-date {
  font-size: 0.85rem;
  color: #9b8fc2;
}

.lecture-actions {
  display: flex;
  gap: 10px;
}

.action-btn {
  padding: 6px 14px;
  border-radius: 8px;
  font-size: 0.85rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  border: none;
}

.view-btn {
  background: #5c4d82;
  color: #ffffff;
}

.download-btn {
  background: #7eb89f;
  color: #ffffff;
}

.delete-btn {
  background: #ffebee;
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
  padding: 10px 20px;
  background: #ffffff;
  border: 2px solid #5c4d82;
  border-radius: 10px;
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
  color: #5c5c5c;
}

.dialog-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.dialog {
  background: #ffffff;
  border-radius: 24px;
  width: 90%;
  max-width: 600px;
  max-height: 80vh;
  overflow: hidden;
}

.dialog.lecture-dialog {
  max-width: 900px;
}

.dialog-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 25px;
  border-bottom: 2px solid #f0f0f0;
}

.dialog-header h3 {
  margin: 0;
  font-size: 1.25rem;
  color: #2d2d2d;
}

.close-btn {
  background: none;
  border: none;
  font-size: 1.5rem;
  cursor: pointer;
  color: #5c5c5c;
}

.dialog-body {
  padding: 25px;
  max-height: calc(80vh - 100px);
  overflow-y: auto;
}

.dialog-body.lecture-content {
  padding: 30px;
}

.add-category {
  display: flex;
  gap: 10px;
  margin-bottom: 25px;
}

.add-category .input-field {
  flex: 1;
  padding: 12px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
}

.color-picker {
  width: 50px;
  height: 50px;
  border: none;
  border-radius: 12px;
  cursor: pointer;
}

.add-category-btn {
  padding: 12px 24px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-weight: 600;
  cursor: pointer;
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
  padding: 15px;
  background: #f8f8f8;
  border-radius: 12px;
}

.category-color {
  width: 20px;
  height: 20px;
  border-radius: 50%;
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

.edit-btn,
.delete-btn {
  padding: 8px;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.edit-btn {
  background: #e3f2fd;
  color: #1976d2;
}

.delete-btn {
  background: #ffebee;
  color: #c62828;
}

.edit-btn:hover,
.delete-btn:hover {
  transform: scale(1.1);
}

@media (max-width: 768px) {
  .filter-row {
    flex-direction: column;
  }

  .search-input,
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
}
</style>
