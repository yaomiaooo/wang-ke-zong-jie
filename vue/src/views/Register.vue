<template>
  <div class="register-container">
    <div class="decoration decoration-1"></div>
    <div class="decoration decoration-2"></div>
    
    <div class="register-content">
      <div class="brand-section">
        <div class="brand-card">
          <h1 class="brand-title">网课总结</h1>
          <p class="brand-slogan">智能让学习更简单</p>
        </div>
      </div>
      
      <div class="register-card">
        <div class="card-header">
          <h2>创建账号</h2>
          <p>加入我们，开始智能学习之旅</p>
        </div>
        
        <form @submit.prevent="handleRegister" class="register-form">
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
            <label>邮箱</label>
            <input
              v-model="email"
              type="email"
              class="input-warm"
              placeholder="请输入邮箱地址"
            />
          </div>
          
          <div class="form-group">
            <label>密码</label>
            <input
              v-model="password"
              type="password"
              class="input-warm"
              placeholder="请设置密码（至少8位）"
            />
          </div>
          
          <div class="form-group">
            <label>确认密码</label>
            <input
              v-model="confirmPassword"
              type="password"
              class="input-warm"
              placeholder="请再次输入密码"
            />
          </div>
          
          <button
            type="submit"
            class="btn-dark submit-btn"
            :disabled="loading"
          >
            {{ loading ? '注册中...' : '创建账号' }}
          </button>
        </form>
        
        <div class="form-footer">
          <p>已有账号？</p>
          <button class="link-btn" @click="router.push('/login')">
            立即登录 →
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
  name: 'Register',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const username = ref('')
    const email = ref('')
    const password = ref('')
    const confirmPassword = ref('')
    const loading = ref(false)

    const handleRegister = async () => {
      if (!username.value || !email.value || !password.value) {
        ElMessage.error('请填写所有必填项')
        return
      }
      
      if (password.value !== confirmPassword.value) {
        ElMessage.error('两次输入的密码不一致')
        return
      }
      
      if (password.value.length < 8) {
        ElMessage.error('密码长度不能少于8位')
        return
      }
      
      loading.value = true
      try {
        await authStore.register(username.value, email.value, password.value, confirmPassword.value)
        ElMessage.success('注册成功！正在登录...')
        router.push('/')
      } catch (err) {
        let errorMessage = '注册失败'
        if (err.response?.data) {
          errorMessage = err.response.data.message || '注册失败，请稍后重试'
        }
        ElMessage.error(errorMessage)
      } finally {
        loading.value = false
      }
    }

    return {
      username,
      email,
      password,
      confirmPassword,
      loading,
      handleRegister,
      router
    }
  }
}
</script>

<style scoped>
.register-container {
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
  opacity: 0.3;
}

.decoration-1 {
  width: 500px;
  height: 500px;
  background: #7eb89f;
  top: -200px;
  right: -100px;
}

.decoration-2 {
  width: 350px;
  height: 350px;
  background: #e8a87c;
  bottom: -100px;
  left: -50px;
}

.register-content {
  display: grid;
  grid-template-columns: 450px 1fr;
  gap: 0;
  max-width: 1000px;
  width: 100%;
  position: relative;
  z-index: 1;
}

.brand-section {
  background: #ffffff;
  border-radius: 24px 0 0 24px;
  padding: 48px;
  display: flex;
  align-items: center;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
}

.brand-card {
  width: 100%;
  text-align: center;
}

.brand-title {
  font-family: 'Georgia', serif;
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0 0 8px 0;
  color: #5c4d82;
}

.brand-slogan {
  color: #5c5c5c;
  margin: 0;
  font-size: 1.125rem;
}

.register-card {
  background: #ffffff;
  border-radius: 0 24px 24px 0;
  padding: 48px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12);
  border-left: 2px solid #f0f0f0;
}

.card-header {
  text-align: left;
  margin-bottom: 40px;
}

.card-header h2 {
  font-family: 'Georgia', serif;
  font-size: 2.25rem;
  margin: 0 0 8px 0;
  color: #2d2d2d;
}

.card-header p {
  color: #5c5c5c;
  margin: 0;
}

.register-form {
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
  margin-top: 8px;
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
  .register-content {
    grid-template-columns: 1fr;
  }
  
  .brand-section {
    display: none;
  }
  
  .register-card {
    border-radius: 24px;
    border-left: none;
  }
  
  .decoration {
    display: none;
  }
}

@media (max-width: 480px) {
  .register-card {
    padding: 32px 24px;
  }
  
  .card-header h2 {
    font-size: 1.75rem;
  }
}
</style>
