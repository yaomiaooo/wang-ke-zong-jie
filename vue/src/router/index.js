import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import Branch from '../views/Branch.vue'
import Annotation from '../views/Annotation.vue'
import Generating from '../views/Generating.vue'
import Result from '../views/Result.vue'
import Information from '../views/Information.vue'

const routes = [
  { path: '/', component: Home },
  { path: '/branch', component: Branch },
  { path: '/annotation', component: Annotation },
  { path: '/generating', component: Generating },
  { path: '/result', component: Result },
  { path: '/information', component: Information}
]

const router = createRouter({
  history: createWebHistory(), 
  routes,
})

export default router
