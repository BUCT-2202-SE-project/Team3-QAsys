// 定制请求的实例

// 导入axios npm install axios
import axios from 'axios';
// 定义一个变量，记录公共的前缀，baseUrl
// const baseURL = 'http://10.12.112.166:2020';
const baseURL = '/api';
const instance = axios.create({baseURL});
// instance.defaults.withCredentials = true
import {useTokenStore} from '@/stores/token.js';
import { ElMessage } from 'element-plus';
// 添加请求拦截器
instance.interceptors.request.use(
    (config) => {
        // 请求前的回调
        // 添加token
        const tokenStore = useTokenStore();
        // 判断有没有token
        if (tokenStore.token) {
            config.headers.Authorization = tokenStore.token;
        }
        return config;
    },
    (err) => {
        // 请求失败的回调
        Promise.reject(err); // 异步的状态转化成失败的状态
    }
)

// import {useRouter} from 'vue-router';
// const router = useRouter();

import router from '@/router/index.js';

// 添加响应拦截器
instance.interceptors.response.use(
  result => {
      return result.data; // 如果请求成功，直接返回数据部分
  },
  err => {
      // 检查 err.response 是否存在
      if (err.response) {
          // 服务返回的 HTTP 错误处理
          const { status } = err.response;

          if (status === 401) {
              ElMessage.error('请先登录');
              if (router.currentRoute.value.path !== '/login') {
                  router.push('/login');
              }
          } else {
              ElMessage.error(`服务异常：${status}`);
          }
      } else {
          // 处理其他错误（网络错误等）
          console.error('Error without response:', err);
          ElMessage.error('网络异常，请稍后重试');
      }

      return Promise.reject(err); // 抛出错误供调用方捕获
  }
);


export default instance;