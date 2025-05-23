<script setup>
import { RouterLink, RouterView } from 'vue-router'
import { useDark, useToggle } from '@vueuse/core'
import { SunIcon, MoonIcon } from '@heroicons/vue/24/outline'
import { useRouter, onBeforeRouteLeave } from 'vue-router'
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { ElMessageBox, ElMessage } from 'element-plus'

// 导入logo图片
import logoImage from '@/assets/logo2.png'

import { useTokenStore } from '@/stores/token.js'
import useUserInfoStore from '@/stores/user.js'  
import useChatIdStore from '@/stores/chatId.js'
const tokenStore = useTokenStore()  
const userInfoStore = useUserInfoStore() 
const chatIdStore = useChatIdStore()

const isDark = useDark()
const toggleDark = useToggle(isDark)
const router = useRouter()

// 添加全局状态来跟踪当前路由
const currentRoute = ref(router.currentRoute.value.path)

// 计算属性：判断是否在登录页面
const isLoginPage = computed(() => {
  return router.currentRoute.value.path === '/login'
})

// 确保路由变化时更新currentRoute
router.afterEach((to) => {
  currentRoute.value = to.path
})

// 添加全局路由守卫
router.beforeEach((to, from, next) => {
  if (to.path === '/login') {
    next()
  } else {
    // 检查是否有 token
    if (!tokenStore.token) {
      // 如果没有 token，重定向到登录页面
      next({ path: '/login' })
    } else {
      // 如果有 token，继续导航
      next()
    }
  }
})

// 创建一个清除用户数据的函数
const clearUserData = () => {
  if (tokenStore.token) {
    tokenStore.removeToken()
    userInfoStore.removeUserInfo()
    chatIdStore.removeChatId()
    
    
  }
}

const handleLogout = () => {
  ElMessageBox.confirm(
    '确定要退出系统吗?',
    '提示',
    {
      confirmButtonText: '确定',
      cancelButtonText: '取消',
      type: 'warning',
    }
  )
    .then(() => {
      clearUserData() // 使用抽取的函数替代重复代码
      // 提示成功
      ElMessage({
        type: 'success',
        message: '已成功退出系统',
      })
      // 跳转到登录页面
      router.push('/login')
    })
    .catch(() => {
      // 取消退出
      ElMessage({
        type: 'info',
        message: '已取消退出',
      })
    })
}
</script>

<template>
  <div class="app" :class="{ 'dark': isDark }">
    <nav class="navbar">
      <router-link to="/home" class="logo">
        <img :src="logoImage" alt="Logo" class="logo-image" />
        MuseLink-千鉴
      </router-link>
      <div class="navbar-actions">
        <button @click="toggleDark()" class="theme-toggle">
          <SunIcon v-if="isDark" class="icon" />
          <MoonIcon v-else class="icon" />
        </button>
        <!-- 只有不在登录页面时才显示退出按钮 -->
        <button v-if="!isLoginPage" class="logout-btn" @click="handleLogout">
          退出
        </button>
      </div>
    </nav>
    <router-view v-slot="{ Component }">
      <transition name="fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<style lang="scss">
:root {
  --bg-color: #f5f5f5;
  --text-color: #333;
}

.dark {
  --bg-color: #1a1a1a;
  --text-color: #fff;
}

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  height: 100%;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
  color: var(--text-color);
  background: var(--bg-color);
  min-height: 100vh;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.navbar {
  display: flex;
  justify-content: flex-start;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  position: sticky;
  top: 0;
  z-index: 100;
  border-bottom: 1px solid rgba(255, 255, 255, 0.1);

  .logo {
    display: flex;
    align-items: center;
    font-size: 1.5rem;
    font-weight: bold;
    text-decoration: none;
    color: inherit;
    background: linear-gradient(45deg, #007CF0, #00DFD8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;

    .logo-image {
      height: 40px; /* 可根据需要调整大小 */
      margin-right: 8px;
      vertical-align: middle; /* 确保垂直居中 */
      display: inline-block; /* 更好的对齐控制 */
    }
  }

  .navbar-actions {
    display: flex;
    align-items: center;
    margin-left: auto;
  }

  .theme-toggle {
    background: none;
    border: none;
    cursor: pointer;
    padding: 0.5rem;
    border-radius: 50%;
    transition: background-color 0.3s;

    &:hover {
      background: rgba(255, 255, 255, 0.1);
    }

    .icon {
      width: 24px;
      height: 24px;
      color: var(--text-color);
    }
  }

  .logout-btn {
    margin-left: 2rem; // 让退出按钮更靠右
    padding: 0.5rem 1.2rem;
    border: none;
    border-radius: 0.5rem;
    background: #ff4d4f;
    color: #fff;
    font-size: 1rem;
    cursor: pointer;
    transition: background 0.2s;
    &:hover {
      background: #d9363e;
    }
  }

  .dark & {
    background: rgba(0, 0, 0, 0.2);
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  }
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

@media (max-width: 768px) {
  .navbar {
    padding: 1rem;
  }
}
</style>
