<template>
  <div class="home" :class="{ 'dark': isDark }">
    <div class="container">
      <h1 class="title">快来开启与千鉴的对话吧✨</h1>
      <div class="cards-grid">
        <router-link 
          v-for="app in aiApps" 
          :key="app.id"
          :to="app.route"
          class="card"
        >
          <div class="card-content">
            <component :is="app.icon" class="icon" />
            <h2>{{ app.title }}</h2>
            <p>{{ app.description }}</p>
          </div>
        </router-link>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useDark } from '@vueuse/core'
import { 
  ChatBubbleLeftRightIcon,
  HeartIcon,
  UserGroupIcon,
  DocumentTextIcon
} from '@heroicons/vue/24/outline'

const isDark = useDark()

const aiApps = ref([
  {
    id: 1,
    title: '知识问答',
    description: '博物馆问答助手',
    route: '/ai-chat',
    icon: ChatBubbleLeftRightIcon
  },
  // {
  //   id: 2,
  //   title: '闲聊',
  //   description: '来和我聊天吧！',
  //   route: '/chat-assistant',
  //   icon: DocumentTextIcon,
  //   iconClass: 'heart-icon'
  // },
])


</script>

<style scoped lang="scss">
.home {
  min-height: 100vh;
  padding: 2rem;
  background: var(--bg-color);
  transition: background-color 0.3s;

  .container {
    max-width: 1600px;
    margin: 0 auto;
    padding: 0 2rem;
  }

  .title {
    text-align: center;
    font-size: 2.5rem;
    margin-bottom: 3rem;
    background: linear-gradient(45deg, #007CF0, #00DFD8);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: fadeIn 1s ease-out;
  }

  .cards-grid {
    display: grid;
    grid-template-columns: repeat(1, 1fr);
    gap: 2rem;
    justify-items: center;
    padding: 1rem;

    @media (min-width: 768px) {
      grid-template-columns: repeat(1, 1fr); 
    }
    
    // @media (min-width: 1200px) {
    //   grid-template-columns: repeat(4, 1fr); 
    // }
  }

  .card {
    position: relative;
    width: 100%;
    max-width: 320px;
    background: rgba(255, 255, 255, 0.8);
    backdrop-filter: blur(10px);
    border-radius: 20px;
    padding: 2rem;
    text-decoration: none;
    color: inherit;
    transition: all 0.3s ease;
    border: 1px solid rgba(255, 255, 255, 0.1);
    overflow: hidden;

    .dark & {
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid rgba(255, 255, 255, 0.05);
    }

    &:hover {
      transform: translateY(-5px);
      box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
      
      .dark & {
        box-shadow: 0 10px 20px rgba(0, 0, 0, 0.3);
      }
    }

    .card-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .icon {
      width: 48px;
      height: 48px;
      margin-bottom: 1rem;
      color: #007CF0;

      &.heart-icon {
        color: #ff4d4f;
        animation: pulse 1.5s ease-in-out infinite;
      }
    }

    h2 {
      font-size: 1.5rem;
      margin-bottom: 0.5rem;
    }

    p {
      color: #666;
      font-size: 1rem;

      .dark & {
        color: #999;
      }
    }
  }

  &.dark {
    background: #1a1a1a;
    
    .card {
      background: rgba(255, 255, 255, 0.05);
      
      p {
        color: #999;
      }
    }
  }
}

@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.1);
  }
  100% {
    transform: scale(1);
  }
}

@media (max-width: 768px) {
  .home {
    padding: 1rem;
    
    .container {
      padding: 0 1rem;
    }
    
    .title {
      font-size: 2rem;
    }

    .card {
      max-width: 100%;
    }
  }
}
</style> 