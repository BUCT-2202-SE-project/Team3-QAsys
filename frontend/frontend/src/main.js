import { createApp } from 'vue'
import router from './router'
import App from './App.vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import { createPinia } from 'pinia'
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate'

const app = createApp(App)
const pinia = createPinia()
// const persist = createPersistedState();

pinia.use(piniaPluginPersistedstate)  // 使用官方插件
app.use(pinia)
app.use(router)
app.use(ElementPlus);
app.mount('#app')