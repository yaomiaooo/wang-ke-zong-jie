<template>
  <div class="login-container">
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    <div class="decoration decoration-3"></div>
    
    <div class="login-content">
      <div class="welcome-section">
        <div class="brand-badge">
          <span class="brand-text">网课总结</span>
        </div>
        <h1 class="welcome-title">
          Turn your lectures
          <br>
          <span class="highlight">into insights.</span>
        </h1>
        <p class="welcome-subtitle">
          智能识别网课内容，自动生成结构化笔记。
          让学习更高效，让知识更清晰。
        </p>
        <div class="feature-tags">
          <span class="tag tag-purple">🎬 视频分析</span>
          <span class="tag tag-green">📝 智能笔记</span>
          <span class="tag tag-salmon">🎯 要点提取</span>
        </div>
      </div>
      
      <div class="login-card">
        <div class="card-header">
          <h2>欢迎回来</h2>
          <p>登录继续使用</p>
        </div>
        
        <form @submit.prevent="handleLogin" class="login-form">
          <div class="form-group">
            <label>用户名</label>
            <input
              v-model="username"
              type="text"
              class="input-warm"
              placeholder="请输入用户名"
            />
          </div>
          
          <div class="form-group">
            <label>密码</label>
            <input
              v-model="password"
              type="password"
              class="input-warm"
              placeholder="请输入密码"
            />
          </div>
          
          <button
            type="submit"
            class="btn-warm submit-btn"
            :disabled="loading"
          >
            {{ loading ? '登录中...' : '登录' }}
          </button>
        </form>
        
        <div class="form-footer">
          <p>还没有账号？</p>
          <button class="link-btn" @click="router.push('/register')">
            立即注册 →
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { ElMessage } from 'element-plus'

export default {
  name: 'Login',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const username = ref('')
    const password = ref('')
    const loading = ref(false)

    const handleLogin = async () => {
      if (!username.value || !password.value) {
        ElMessage.error('请填写用户名和密码')
        return
      }
      
      loading.value = true
      try {
        await authStore.login(username.value, password.value)
        ElMessage.success('登录成功！')
        router.push('/')
      } catch (err) {
        let errorMessage = '登录失败'
        if (err.response?.data) {
          errorMessage = err.response.data.message || '用户名或密码错误'
        }
        ElMessage.error(errorMessage)
      } finally {
        loading.value = false
      }
    }

    return {
      username,
      password,
      loading,
      handleLogin,
      router
    }
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, #c4b5e0 0%, #e8e8e8 100%);
}

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
  background: #9b8fc2;
  bottom: -50px;
  right: -50px;
}

.decoration-3 {
  width: 200px;
  height: 200px;
  background: #7eb89f;
  top: 50%;
  right: 10%;
}

.login-content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 60px;
  max-width: 1100px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.welcome-section {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.brand-badge {
  display: inline-block;
  background: #ffffff;
  padding: 12px 24px;
  border-radius: 50px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  margin-bottom: 40px;
  width: fit-content;
}

.brand-text {
  font-weight: 700;
  font-size: 1.125rem;
  color: #5c4d82;
}

.welcome-title {
  font-family: 'Georgia', serif;
  font-size: 3.5rem;
  font-weight: 700;
  line-height: 1.1;
  margin: 0 0 24px 0;
  color: #2d2d2d;
}

.highlight {
  color: #5c4d82;
}

.welcome-subtitle {
  font-size: 1.125rem;
  color: #5c5c5c;
  line-height: 1.7;
  margin: 0 0 40px 0;
}

.feature-tags {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.tag {
  padding: 10px 20px;
  border-radius: 50px;
  font-size: 0.875rem;
  font-weight: 600;
}

.tag-purple {
  background: #9b8fc2;
  color: #ffffff;
}

.tag-green {
  background: #7eb89f;
  color: #ffffff;
}

.tag-salmon {
  background: #e8a87c;
  color: #ffffff;
}

.login-card {
  background: #ffffff;
  border-radius: 24px;
  padding: 48px;
  box-shadow: 0 12px 40px rgba(0, 0, 0, 0.15);
}

.card-header {
  text-align: center;
  margin-bottom: 40px;
}

.card-header h2 {
  font-family: 'Georgia', serif;
  font-size: 2rem;
  margin: 0 0 8px 0;
  color: #2d2d2d;
}

.card-header p {
  color: #5c5c5c;
  margin: 0;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 24px;
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

.submit-btn {
  width: 100%;
  margin-top: 16px;
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

.submit-btn:hover:not(:disabled) {
  background: #4a3d6e;
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(92, 77, 130, 0.3);
}

.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.form-footer {
  text-align: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #e8e0d0;
}

.form-footer p {
  margin: 0 0 8px 0;
  color: #5c5c5c;
}

.link-btn {
  background: none;
  border: none;
  color: #5c4d82;
  font-weight: 700;
  font-size: 1rem;
  cursor: pointer;
  transition: color 0.3s ease;
}

.link-btn:hover {
  color: #4a3d6e;
}

@media (max-width: 900px) {
  .login-content {
    grid-template-columns: 1fr;
    gap: 40px;
  }
  
  .welcome-section {
    text-align: center;
  }
  
  .brand-badge {
    margin: 0 auto 32px;
  }
  
  .welcome-title {
    font-size: 2.5rem;
  }
  
  .feature-tags {
    justify-content: center;
  }
  
  .decoration {
    display: none;
  }
}

@media (max-width: 480px) {
  .login-card {
    padding: 32px 24px;
  }
  
  .welcome-title {
    font-size: 2rem;
  }
}
</style>
