<template>
  <div class="personal-center">
    <div class="container">
      <div class="header-section">
        <h1 class="page-title">
          <i class="el-icon-user"></i>
          个人中心
        </h1>
        <button class="logout-btn" @click="handleLogout">
          <i class="el-icon-switch-button"></i>
          退出登录
        </button>
      </div>

      <div class="content-grid">
        <div class="profile-card">
          <div class="profile-header">
            <div class="avatar-section">
              <div class="avatar" :style="{ backgroundColor: '#5c4d82' }">
                {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
              </div>
              <div class="user-info">
                <h2>{{ user?.username }}</h2>
                <p>{{ user?.email }}</p>
                <span class="join-date">注册于 {{ formatDate(user?.created_at) }}</span>
              </div>
            </div>
          </div>

          <div class="profile-body">
            <h3>编辑个人资料</h3>
            <form @submit.prevent="handleUpdateProfile">
              <div class="form-group">
                <label>邮箱</label>
                <input
                  v-model="form.email"
                  type="email"
                  class="input-field"
                  placeholder="请输入邮箱"
                />
              </div>

              <div class="form-group">
                <label>手机号</label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="input-field"
                  placeholder="请输入手机号"
                />
              </div>

              <div class="form-group">
                <label>个人简介</label>
                <textarea
                  v-model="form.bio"
                  class="input-field textarea"
                  placeholder="请输入个人简介"
                  rows="4"
                ></textarea>
              </div>

              <button type="submit" class="save-btn" :disabled="saving">
                {{ saving ? '保存中...' : '保存修改' }}
              </button>
            </form>
          </div>
        </div>

        <div class="statistics-card">
          <h3>
            <i class="el-icon-data-analysis"></i>
            数据统计
          </h3>
          <div class="stats-grid">
            <div class="stat-item">
              <div class="stat-icon" style="background: #5c4d82;">
                <i class="el-icon-document"></i>
              </div>
              <div class="stat-info">
                <span class="stat-number">{{ statistics?.total_lectures || 0 }}</span>
                <span class="stat-label">总讲义数</span>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: #7eb89f;">
                <i class="el-icon-circle-check"></i>
              </div>
              <div class="stat-info">
                <span class="stat-number">{{ statistics?.completed_lectures || 0 }}</span>
                <span class="stat-label">已完成</span>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: #e8a87c;">
                <i class="el-icon-loading"></i>
              </div>
              <div class="stat-info">
                <span class="stat-number">{{ statistics?.processing_lectures || 0 }}</span>
                <span class="stat-label">处理中</span>
              </div>
            </div>

            <div class="stat-item">
              <div class="stat-icon" style="background: #9b8fc2;">
                <i class="el-icon-folder-opened"></i>
              </div>
              <div class="stat-info">
                <span class="stat-number">{{ statistics?.total_categories || 0 }}</span>
                <span class="stat-label">分类数</span>
              </div>
            </div>
          </div>

          <div class="top-tags" v-if="statistics?.top_tags?.length">
            <h4>热门标签</h4>
            <div class="tags-list">
              <span
                v-for="tag in statistics.top_tags"
                :key="tag.tag"
                class="tag-item"
              >
                {{ tag.tag }} ({{ tag.count }})
              </span>
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
import { useAuthStore } from '@/stores/auth'
import { useLectureStore } from '@/stores/lecture'
import { ElMessage } from 'element-plus'

export default {
  name: 'PersonalCenter',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()
    const lectureStore = useLectureStore()

    const user = ref(null)
    const statistics = ref(null)
    const form = ref({
      email: '',
      phone: '',
      bio: ''
    })
    const saving = ref(false)

    const loadData = async () => {
      try {
        // 获取用户信息
        const userRes = await authStore.fetchUserInfo()
        if (userRes.success) {
          user.value = userRes.user
          form.value = {
            email: userRes.user.email,
            phone: userRes.user.phone || '',
            bio: userRes.user.bio || ''
          }
        }

        // 获取统计数据
        lectureStore.setAuthHeader(authStore.token)
        const statsRes = await lectureStore.fetchStatistics()
        if (statsRes.success) {
          statistics.value = statsRes.statistics
        }
      } catch (err) {
        console.error('加载数据失败:', err)
        if (err.response?.status === 401) {
          router.push('/login')
        }
      }
    }

    const handleUpdateProfile = async () => {
      saving.value = true
      try {
        await authStore.updateProfile(form.value)
        ElMessage.success('资料更新成功')
        await loadData()
      } catch (err) {
        ElMessage.error('更新失败: ' + (err.response?.data?.message || '请稍后重试'))
      } finally {
        saving.value = false
      }
    }

    const handleLogout = async () => {
      try {
        await authStore.logout()
        ElMessage.success('已退出登录')
        router.push('/login')
      } catch (err) {
        router.push('/login')
      }
    }

    const formatDate = (dateStr) => {
      if (!dateStr) return ''
      const date = new Date(dateStr)
      return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
    }

    onMounted(() => {
      if (!authStore.isAuthenticated) {
        router.push('/login')
        return
      }
      loadData()
    })

    return {
      user,
      statistics,
      form,
      saving,
      handleUpdateProfile,
      handleLogout,
      formatDate
    }
  }
}
</script>

<style scoped>
.personal-center {
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
  margin-bottom: 40px;
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

.logout-btn {
  padding: 12px 24px;
  background: #ffffff;
  border: 2px solid #5c4d82;
  border-radius: 12px;
  color: #5c4d82;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  gap: 8px;
}

.logout-btn:hover {
  background: #5c4d82;
  color: #ffffff;
}

.content-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 30px;
}

.profile-card,
.statistics-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 40px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.1);
}

.profile-header {
  margin-bottom: 30px;
  padding-bottom: 30px;
  border-bottom: 2px solid #f0f0f0;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;
}

.avatar {
  width: 100px;
  height: 100px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 2.5rem;
  font-weight: 700;
}

.user-info h2 {
  margin: 0 0 8px 0;
  font-size: 1.5rem;
  color: #2d2d2d;
}

.user-info p {
  margin: 0 0 8px 0;
  color: #5c5c5c;
}

.join-date {
  font-size: 0.875rem;
  color: #9b8fc2;
}

.profile-body h3 {
  margin: 0 0 24px 0;
  font-size: 1.25rem;
  color: #2d2d2d;
}

.form-group {
  margin-bottom: 20px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
  color: #2d2d2d;
}

.input-field {
  width: 100%;
  padding: 14px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  box-sizing: border-box;
}

.input-field:focus {
  outline: none;
  border-color: #5c4d82;
  box-shadow: 0 0 0 4px rgba(92, 77, 130, 0.1);
}

.textarea {
  resize: vertical;
}

.save-btn {
  width: 100%;
  padding: 14px;
  background: #5c4d82;
  color: #ffffff;
  border: none;
  border-radius: 12px;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.save-btn:hover:not(:disabled) {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.save-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.statistics-card h3 {
  margin: 0 0 24px 0;
  font-size: 1.25rem;
  color: #2d2d2d;
  display: flex;
  align-items: center;
  gap: 10px;
}

.statistics-card h3 i {
  color: #5c4d82;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20px;
  margin-bottom: 30px;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px;
  background: #f8f8f8;
  border-radius: 16px;
}

.stat-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 1.5rem;
}

.stat-info {
  display: flex;
  flex-direction: column;
}

.stat-number {
  font-size: 1.75rem;
  font-weight: 700;
  color: #2d2d2d;
}

.stat-label {
  font-size: 0.875rem;
  color: #5c5c5c;
}

.top-tags h4 {
  margin: 0 0 16px 0;
  font-size: 1rem;
  color: #2d2d2d;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
}

.tag-item {
  padding: 8px 16px;
  background: #f0f0f0;
  border-radius: 20px;
  font-size: 0.875rem;
  color: #5c5c5c;
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .profile-card,
  .statistics-card {
    padding: 24px;
  }

  .avatar-section {
    flex-direction: column;
    text-align: center;
  }

  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
