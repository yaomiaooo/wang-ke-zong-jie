<template>
  <div class="navbar">
    <div class="navbar-content">
      <router-link to="/" class="navbar-brand">
        <i class="el-icon-video-camera"></i>
        <span>智能网课总结</span>
      </router-link>

      <div class="navbar-links">
        <router-link to="/" class="nav-link">
          <i class="el-icon-home"></i>
          <span>首页</span>
        </router-link>

        <router-link to="/lectures" class="nav-link" v-if="isLoggedIn">
          <i class="el-icon-folder-opened"></i>
          <span>我的讲义</span>
        </router-link>

        <router-link to="/personal-center" class="nav-link" v-if="isLoggedIn">
          <i class="el-icon-user"></i>
          <span>{{ user?.username }}</span>
        </router-link>

        <div class="auth-buttons" v-if="!isLoggedIn">
          <router-link to="/login" class="nav-link login-link">登录</router-link>
          <router-link to="/register" class="nav-link register-link">注册</router-link>
        </div>

        <button v-if="isLoggedIn" class="nav-link logout-btn" @click="handleLogout">
          <i class="el-icon-switch-button"></i>
          <span>退出</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

export default {
  name: 'Navbar',
  setup() {
    const router = useRouter()
    const authStore = useAuthStore()

    const isLoggedIn = computed(() => authStore.isAuthenticated)
    const user = computed(() => authStore.user)

    const handleLogout = async () => {
      await authStore.logout()
      router.push('/')
    }

    return {
      isLoggedIn,
      user,
      handleLogout
    }
  }
}
</script>

<style scoped>
.navbar {
  background: #ffffff;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
  position: sticky;
  top: 0;
  z-index: 1000;
}

.navbar-content {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 30px;
  height: 60px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.navbar-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  text-decoration: none;
  color: #5c4d82;
  font-size: 1.3rem;
  font-weight: 700;
}

.navbar-brand i {
  font-size: 1.5rem;
}

.navbar-links {
  display: flex;
  align-items: center;
  gap: 8px;
}

.nav-link {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  text-decoration: none;
  color: #5c4d82;
  font-weight: 500;
  font-size: 0.95rem;
  transition: all 0.3s ease;
  background: transparent;
  border: none;
  cursor: pointer;
}

.nav-link:hover {
  background: rgba(92, 77, 130, 0.1);
}

.nav-link i {
  font-size: 1.1rem;
}

.nav-link.router-link-active {
  background: rgba(92, 77, 130, 0.15);
  color: #4a3d6e;
}

.auth-buttons {
  display: flex;
  gap: 8px;
  margin-left: 8px;
}

.login-link {
  background: transparent;
  border: 2px solid #5c4d82;
}

.login-link:hover {
  background: rgba(92, 77, 130, 0.1);
}

.register-link {
  background: #5c4d82;
  color: #ffffff;
  border: 2px solid #5c4d82;
}

.register-link:hover {
  background: #4a3d6e;
}

.logout-btn {
  color: #e85c5c;
  margin-left: 8px;
}

.logout-btn:hover {
  background: rgba(232, 92, 92, 0.1);
}
</style>
