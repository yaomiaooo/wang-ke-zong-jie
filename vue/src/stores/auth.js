import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8001'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    token: localStorage.getItem('token') || '',
    user: JSON.parse(localStorage.getItem('user') || 'null'),
    isAuthenticated: !!localStorage.getItem('token')
  }),

  getters: {
    getToken: (state) => state.token,
    getUser: (state) => state.user,
    isLoggedIn: (state) => state.isAuthenticated
  },

  actions: {
    // 设置 axios 默认 headers
    setAuthHeader() {
      if (this.token) {
        axios.defaults.headers.common['Authorization'] = `Token ${this.token}`
      } else {
        delete axios.defaults.headers.common['Authorization']
      }
    },

    // 用户注册
    async register(username, email, password, confirmPassword) {
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/register/`, {
          username,
          email,
          password,
          confirm_password: confirmPassword
        })

        if (response.data.success) {
          this.setAuth(response.data.token, response.data.user)
          return response.data
        }
      } catch (error) {
        throw error
      }
    },

    // 用户登录
    async login(username, password) {
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/login/`, {
          username,
          password
        })

        if (response.data.success) {
          this.setAuth(response.data.token, response.data.user)
          return response.data
        }
      } catch (error) {
        throw error
      }
    },

    // 用户登出
    async logout() {
      try {
        if (this.token) {
          await axios.post(`${API_BASE_URL}/auth/logout/`)
        }
      } catch (error) {
        console.error('登出请求失败:', error)
      } finally {
        this.clearAuth()
      }
    },

    // 设置认证信息
    setAuth(token, user) {
      this.token = token
      this.user = user
      this.isAuthenticated = true
      localStorage.setItem('token', token)
      localStorage.setItem('user', JSON.stringify(user))
      this.setAuthHeader()
    },

    // 清除认证信息
    clearAuth() {
      this.token = ''
      this.user = null
      this.isAuthenticated = false
      localStorage.removeItem('token')
      localStorage.removeItem('user')
      delete axios.defaults.headers.common['Authorization']
    },

    // 获取用户信息
    async fetchUserInfo() {
      try {
        this.setAuthHeader()
        const response = await axios.get(`${API_BASE_URL}/auth/user_info/`)
        if (response.data.success) {
          this.user = response.data.user
          localStorage.setItem('user', JSON.stringify(this.user))
        }
        return response.data
      } catch (error) {
        if (error.response?.status === 401) {
          this.clearAuth()
        }
        throw error
      }
    },

    // 更新用户资料
    async updateProfile(data) {
      try {
        this.setAuthHeader()
        const response = await axios.post(`${API_BASE_URL}/auth/update_profile/`, data)
        if (response.data.success) {
          this.user = response.data.user
          localStorage.setItem('user', JSON.stringify(this.user))
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 初始化认证状态
    initAuth() {
      if (this.token) {
        this.setAuthHeader()
      }
    }
  }
})
