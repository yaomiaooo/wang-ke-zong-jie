import { defineStore } from 'pinia'
import axios from 'axios'

const API_BASE_URL = 'http://127.0.0.1:8001'

export const useLectureStore = defineStore('lecture', {
  state: () => ({
    lectures: [],
    categories: [],
    currentLecture: null,
    statistics: null,
    pagination: {
      page: 1,
      page_size: 10,
      total: 0,
      total_pages: 0
    },
    loading: false
  }),

  getters: {
    getLectures: (state) => state.lectures,
    getCategories: (state) => state.categories,
    getCurrentLecture: (state) => state.currentLecture,
    getStatistics: (state) => state.statistics,
    isLoading: (state) => state.loading
  },

  actions: {
    // 设置认证 header
    setAuthHeader(token) {
      if (token) {
        axios.defaults.headers.common['Authorization'] = `Token ${token}`
      }
    },

    // 获取讲义列表
    async fetchLectures(params = {}) {
      this.loading = true
      try {
        const queryParams = new URLSearchParams(params).toString()
        const response = await axios.get(`${API_BASE_URL}/lectures/?${queryParams}`)
        if (response.data.success) {
          this.lectures = response.data.lectures
          this.pagination = {
            page: response.data.page,
            page_size: response.data.page_size,
            total: response.data.total,
            total_pages: response.data.total_pages
          }
        }
        return response.data
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 获取单个讲义详情
    async fetchLecture(lectureId) {
      this.loading = true
      try {
        const response = await axios.get(`${API_BASE_URL}/lectures/${lectureId}/`)
        if (response.data.success) {
          this.currentLecture = response.data.lecture
        }
        return response.data
      } catch (error) {
        throw error
      } finally {
        this.loading = false
      }
    },

    // 创建讲义
    async createLecture(data) {
      try {
        const response = await axios.post(`${API_BASE_URL}/lectures/create/`, data)
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 更新讲义
    async updateLecture(lectureId, data) {
      try {
        const response = await axios.put(`${API_BASE_URL}/lectures/${lectureId}/update/`, data)
        if (response.data.success) {
          const index = this.lectures.findIndex(l => l.id === lectureId)
          if (index !== -1) {
            this.lectures[index] = { ...this.lectures[index], ...response.data.lecture }
          }
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 删除讲义
    async deleteLecture(lectureId) {
      try {
        const response = await axios.delete(`${API_BASE_URL}/lectures/${lectureId}/delete/`)
        if (response.data.success) {
          this.lectures = this.lectures.filter(l => l.id !== lectureId)
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 获取分类列表
    async fetchCategories() {
      try {
        const response = await axios.get(`${API_BASE_URL}/categories/`)
        if (response.data.success) {
          this.categories = response.data.categories
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 创建分类
    async createCategory(data) {
      try {
        const response = await axios.post(`${API_BASE_URL}/categories/create/`, data)
        if (response.data.success) {
          this.categories.push(response.data.category)
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 更新分类
    async updateCategory(categoryId, data) {
      try {
        const response = await axios.put(`${API_BASE_URL}/categories/${categoryId}/`, data)
        if (response.data.success) {
          const index = this.categories.findIndex(c => c.id === categoryId)
          if (index !== -1) {
            this.categories[index] = response.data.category
          }
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 删除分类
    async deleteCategory(categoryId) {
      try {
        const response = await axios.delete(`${API_BASE_URL}/categories/${categoryId}/delete/`)
        if (response.data.success) {
          this.categories = this.categories.filter(c => c.id !== categoryId)
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 获取统计数据
    async fetchStatistics() {
      try {
        const response = await axios.get(`${API_BASE_URL}/lectures/statistics/`)
        if (response.data.success) {
          this.statistics = response.data.statistics
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 存档讲义
    async archiveLecture(lectureId) {
      try {
        const response = await axios.post(`${API_BASE_URL}/lectures/${lectureId}/archive/`)
        if (response.data.success) {
          const index = this.lectures.findIndex(l => l.id === lectureId)
          if (index !== -1) {
            this.lectures[index] = { ...this.lectures[index], ...response.data.lecture }
          }
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 恢复讲义
    async restoreLecture(lectureId) {
      try {
        const response = await axios.post(`${API_BASE_URL}/lectures/${lectureId}/restore/`)
        if (response.data.success) {
          const index = this.lectures.findIndex(l => l.id === lectureId)
          if (index !== -1) {
            this.lectures[index] = { ...this.lectures[index], ...response.data.lecture }
          }
        }
        return response.data
      } catch (error) {
        throw error
      }
    },

    // 保存讲义（用于编辑内容）
    async saveLecture(lectureId, data) {
      try {
        const response = await axios.post(`${API_BASE_URL}/lectures/${lectureId}/save/`, data)
        if (response.data.success) {
          // 更新列表中的数据
          const index = this.lectures.findIndex(l => l.id === lectureId)
          if (index !== -1) {
            this.lectures[index] = { ...this.lectures[index], ...response.data.lecture }
          }
          // 更新当前讲义
          if (this.currentLecture?.id === lectureId) {
            this.currentLecture = { ...this.currentLecture, ...response.data.lecture }
          }
        }
        return response.data
      } catch (error) {
        throw error
      }
    }
  }
})
