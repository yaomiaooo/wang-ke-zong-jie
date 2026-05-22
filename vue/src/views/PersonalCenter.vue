<template>
  <div class="personal-center">
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    <div class="decoration decoration-3"></div>
    
    <div class="container">
      <div class="header-section">
        <div class="brand-badge">
          <span class="brand-icon">👤</span>
          <span class="brand-text">个人中心</span>
        </div>
        <button class="logout-btn" @click="handleLogout">
          <i class="el-icon-switch-button"></i>
          退出登录
        </button>
      </div>

      <div class="content-grid">
        <div class="profile-card">
          <div class="card-header">
            <h2>个人资料</h2>
            <p>管理您的账户信息</p>
          </div>
          
          <div class="avatar-section">
            <div class="avatar" :style="{ backgroundColor: '#5c4d82' }">
              {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
            </div>
            <div class="user-info">
              <h3>{{ user?.username }}</h3>
              <p>{{ user?.email }}</p>
              <span class="join-date">注册于 {{ formatDate(user?.created_at) }}</span>
            </div>
          </div>

          <div class="profile-body">
            <form @submit.prevent="handleUpdateProfile">
              <div class="form-group">
                <label>邮箱</label>
                <input
                  v-model="form.email"
                  type="email"
                  class="input-warm"
                  placeholder="请输入邮箱"
                />
              </div>

              <div class="form-group">
                <label>手机号</label>
                <input
                  v-model="form.phone"
                  type="tel"
                  class="input-warm"
                  placeholder="请输入手机号"
                />
              </div>

              <div class="form-group">
                <label>个人简介</label>
                <textarea
                  v-model="form.bio"
                  class="input-warm textarea"
                  placeholder="请输入个人简介"
                  rows="4"
                ></textarea>
              </div>

              <button type="submit" class="btn-dark submit-btn" :disabled="saving">
                {{ saving ? '保存中...' : '保存修改' }}
              </button>
            </form>
          </div>
        </div>

        <div class="statistics-card">
          <div class="card-header">
            <h2>数据统计</h2>
            <p>查看您的学习数据</p>
          </div>
          
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
  position: relative;
  overflow: hidden;
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
  margin-bottom: 40px;
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

.logout-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 24px;
  background: #ffffff;
  border: 2px solid #5c4d82;
  border-radius: 12px;
  color: #5c4d82;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s ease;
}

.logout-btn:hover {
  background: #5c4d82;
  color: #ffffff;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
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
  box-shadow: 0 12px 40px rgba(92, 77, 130, 0.12);
}

.card-header {
  text-align: center;
  margin-bottom: 32px;
  padding-bottom: 24px;
  border-bottom: 2px solid #f0f0f0;
}

.card-header h2 {
  font-family: 'Georgia', serif;
  font-size: 1.75rem;
  margin: 0 0 8px 0;
  color: #2d2d2d;
}

.card-header p {
  color: #888;
  margin: 0;
  font-size: 1rem;
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 32px;
  padding: 24px;
  background: linear-gradient(135deg, #faf9fc 0%, #f5f0fa 100%);
  border-radius: 16px;
}

.avatar {
  width: 90px;
  height: 90px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 2.2rem;
  font-weight: 700;
  flex-shrink: 0;
}

.user-info h3 {
  margin: 0 0 8px 0;
  font-size: 1.4rem;
  color: #2d2d2d;
  font-family: 'Georgia', serif;
}

.user-info p {
  margin: 0 0 8px 0;
  color: #5c5c5c;
  font-size: 1rem;
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
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 20px;
}

.form-group label {
  font-weight: 600;
  font-size: 0.875rem;
  color: #2d2d2d;
}

.input-warm {
  padding: 14px 18px;
  border: 2px solid #e8e8e8;
  border-radius: 12px;
  font-size: 1rem;
  transition: all 0.3s ease;
  background: #fafafa;
}

.input-warm:focus {
  outline: none;
  border-color: #5c4d82;
  background: #ffffff;
  box-shadow: 0 0 0 4px rgba(92, 77, 130, 0.1);
}

.textarea {
  resize: vertical;
  min-height: 100px;
}

.btn-dark {
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

.submit-btn {
  margin-top: 8px;
}

.btn-dark:hover:not(:disabled) {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.btn-dark:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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
  padding: 24px;
  background: linear-gradient(135deg, #faf9fc 0%, #f5f0fa 100%);
  border-radius: 16px;
  transition: all 0.3s ease;
}

.stat-item:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 25px rgba(92, 77, 130, 0.15);
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

.top-tags {
  padding-top: 24px;
  border-top: 2px solid #f0f0f0;
}

.top-tags h4 {
  margin: 0 0 16px 0;
  font-size: 1rem;
  color: #2d2d2d;
  text-align: center;
}

.tags-list {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  justify-content: center;
}

.tag-item {
  padding: 8px 18px;
  background: rgba(92, 77, 130, 0.1);
  border-radius: 20px;
  font-size: 0.875rem;
  color: #5c4d82;
  font-weight: 500;
}

@media (max-width: 900px) {
  .content-grid {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 600px) {
  .personal-center {
    padding: 30px 15px;
  }
  
  .profile-card,
  .statistics-card {
    padding: 28px 24px;
  }
  
  .avatar-section {
    flex-direction: column;
    text-align: center;
  }
  
  .header-section {
    flex-direction: column;
    gap: 20px;
    text-align: center;
  }
  
  .stats-grid {
    grid-template-columns: 1fr;
  }
}
</style>
