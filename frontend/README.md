# MuseLink-千鉴 知识问答子系统 - 前端

## 项目简介

本项目是海外藏中国文物知识管理与服务平台的知识问答子系统前端部分，基于Vue3框架开发，为用户提供友好的交互界面，支持文物知识问答、历史对话管理等功能。

## 技术栈

- Vue3 框架
- Vue Router 路由管理
- Pinia 状态管理
- Axios HTTP客户端
- Element Plus UI组件库
- Marked.js Markdown解析
- Highlight.js 代码高亮

## 环境要求

- Node.js 16.0+
- npm 8.0+ 或 yarn 1.22+

## 安装依赖

1. 克隆仓库到本地

```bash
git clone https://github.com/BUCT-2202-SE-project/Team3-QAsys.git
cd Team3-QAsys/frontend
```

2. 安装依赖包

```bash
# 使用npm
npm install

# 或使用yarn
yarn install
```



## 运行方法

1. 开发环境运行

```bash
# 使用npm
npm run dev

# 或使用yarn
yarn dev
```

2. 生产环境构建

```bash
# 使用npm
npm run build

# 或使用yarn
yarn build
```

3. 预览生产构建

```bash
# 使用npm
npm run preview

# 或使用yarn
yarn preview
```

## 目录结构

```
frontend/
├── node_modules/       # 依赖包
├── public/             # 静态资源
│   ├── favicon.ico     # 网站图标
│   └── index.html      # HTML入口文件
├── src/                # 源代码
│   ├── services/       # API接口
│   │   ├── api.js      # 其他相关API
│   │   └── user.js     # 用户相关API
│   ├── assets/         # 资源文件
│   │   ├── css/        # CSS样式
│   │   └── img/        # 图片资源
│   ├── components/     # 公共组件
│   │   └── ChatMessage.vue  # 聊天窗口组件
│   ├── router/         # 路由
│   │   └── index.js    # 路由配置
│   ├── store/          # 状态管理
│   │   ├── chatId.js   # chatId状态管理
│   │   ├── token.js    # token管理
│   │   └── user.js     # 用户状态管理
│   ├── utils/          # 工具函数
│   │   └── request.js  # 请求封装
│   ├── views/          # 页面视图
│   │   ├── AIChat.vue  # 聊天页面
│   │   ├── Login.vue   # 登录页面
│   │   └── Home.vue    # home页面
│   ├── App.vue         # 根组件
│   └── main.js         # 入口文件
├── .env                # 环境变量
├── .env.development    # 开发环境变量
├── .env.production     # 生产环境变量
├── babel.config.js     # Babel配置
├── package-lock.json   # 依赖锁定
├── package.json        # 项目配置
├── README.md           # 项目说明
└── vue.config.js       # Vue配置
```

## 功能介绍

### 用户认证
- 用户注册
- 用户登录
- 个人信息查看

### 知识问答
- 文物知识问答交互界面
- 实时流式回复
- 支持Markdown格式的回答渲染
- 问答上下文记忆

### 历史对话管理
- 对话历史列表查看
- 历史对话内容查看
- 创建新对话
- 重命名对话
- 删除对话

### 界面特色
- 响应式设计，适配多种设备
- 暗色/亮色主题切换
- 对话引用展示
- 文物知识卡片展示

## 与后端通信

前端通过RESTful API与后端通信，主要包括以下接口：

### 认证接口
- `/auth/register` - 用户注册
- `/auth/login` - 用户登录
- `/auth/getUserInfo` - 获取用户信息

### 问答接口
- `/qa/chat` - 问答核心接口
- `/qa/getHistoryList` - 获取对话历史列表
- `/qa/getHistoryInfo` - 获取指定对话的详细内容
- `/qa/create` - 创建新对话
- `/qa/rename` - 重命名对话
- `/qa/delete` - 删除对话

## 主要依赖包

```json
{
  "dependencies": {
    "axios": "^1.3.5",
    "element-plus": "^2.3.4",
    "highlight.js": "^11.7.0", 
    "marked": "^4.3.0",
    "pinia": "^2.0.34",
    "vue": "^3.2.47",
    "vue-router": "^4.1.6"
  },
  "devDependencies": {
    "@vitejs/plugin-vue": "^4.1.0",
    "sass": "^1.62.0",
    "vite": "^4.2.1"
  }
}
```

