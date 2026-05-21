import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Branch from '../views/Branch.vue'
import Annotation from '../views/Annotation.vue'
import Generating from '../views/Generating.vue'
import Result from '../views/Result.vue'
import Information from '../views/Information.vue'
import Login from '../views/Login.vue'
import Register from '../views/Register.vue'
import PersonalCenter from '../views/PersonalCenter.vue'
import LectureList from '../views/LectureList.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/branch', component: Branch },
  { path: '/annotation', component: Annotation },
  { path: '/generating', component: Generating },
  { path: '/result', component: Result },
  { path: '/information', component: Information },
  { path: '/login', component: Login },
  { path: '/register', component: Register },
  { path: '/personal-center', component: PersonalCenter },
  { path: '/lectures', component: LectureList }
]

const router = createRouter({
  history: createWebHistory(), 
  routes,
})

// 路由守卫
router.beforeEach((to, from, next) => {
  const token = localStorage.getItem('token')
  
  // 需要登录的页面
  const requiresAuth = ['/personal-center', '/lectures']
  
  if (requiresAuth.includes(to.path) && !token) {
    next('/login')
  } else {
    next()
  }
})

export default router
