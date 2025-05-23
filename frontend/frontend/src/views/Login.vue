<script setup>
import { User, Lock, Phone, Postcard , Message} from '@element-plus/icons-vue'
import { ref, computed } from 'vue'
import { ElMessage } from 'element-plus'
import { useDark } from '@vueuse/core'

// 控制注册与登录表单的显示， 默认显示注册
const isRegister = ref(false)

// 获取当前主题
const isDark = useDark()

// 定义数据模型
const userRegisterData = ref({
    username: '',
    email: '',
    password: '',
    repassword: ''
})

// 校验密码的函数
const checkRePassword = (rule, value, callback) => {
    if (value === '') {
        callback(new Error('请再次确认密码'))
    } else if (value !== userRegisterData.value.password) {
        callback(new Error('两次输入密码不一致'))
    } else {
        callback()
    }
}

// 定义表单校验规则
const rules = {
    username: [
        { required: true, message: '请输入用户名', trigger: 'blur' },
        { min: 3, max: 16, message: '长度在 3 到 16 个字符', trigger: 'blur' }
    ],
    email: [
        { required: true, message: '请输入邮箱', trigger: 'blur' },
        { type: 'email', message: '邮箱格式不正确', trigger: 'blur' }
    ],
    password: [
        { required: true, message: '请输入密码', trigger: 'blur' },
        { min: 5, max: 16, message: '长度在 5 到 16 个字符', trigger: 'blur' }
    ],
    repassword: [
        {validator: checkRePassword, trigger: 'blur'},
        { required: true, message: '请再次确认密码', trigger: 'blur' }
    ]
}

// 注册全局校验
const formRefRegister = ref(null);

const handleRegister = () => {
    formRefRegister.value.validate((valid) => {
        if (valid) {
            register(); // 调用注册函数
        } else {
            console.log('请完善表单信息');
            return false;
        }
    });
};

// 调用后台接口完成注册
import { userRegisterService, userLoginService } from '@/services/user.js'
const register = async () => {
    let result = await userRegisterService(userRegisterData.value);
    if (result.code === 0) {
        ElMessage.success('注册成功');
        // 保存用户名以便登录
        const username = userRegisterData.value.username;
        // 清空表单
        clearRegisterData();
        // 设置用户名（使注册用户无需重新输入用户名）
        userRegisterData.value.username = username;
        // 切换到登录页面
        isRegister.value = false;
    } else {
        ElMessage.error('注册失败，请检查信息是否正确');
    }
}

// 登录全局校验
const formRefLogin = ref(null);

const handleLogin = () => {
    formRefLogin.value.validate((valid) => {
        if (valid) {
            login(); // 调用登录函数
        } else {
            console.log('表单校验失败');
            return false;
        }
    });
};

import { userInfoService } from '@/services/user.js'
import useUserInfoStore from '@/stores/user'
const userInfoStore = useUserInfoStore()
// 调用函数，获取用户详细信息
const getUserInfo = async () => {
    // 调用接口
    let result = await userInfoService();
    // 数据存储到pinia中
    userInfoStore.setUserInfo(result.data);
};

// 绑定数据，复用注册表单的数据模型
// 表单数据校验
// 登录函数
import {useTokenStore} from '@/stores/token.js'
import { useRouter } from 'vue-router'
const router = useRouter();
const tokenStore = useTokenStore();
const login = async () => {
    // try {
        let result = await userLoginService(userRegisterData.value);
        if (result.code === 0) {
            ElMessage.success('登录成功');
            // 将token存储到pinia
            tokenStore.setToken(result.data);
            getUserInfo();
            router.push('/home'); // 跳转到首页    
        } else {
            ElMessage.error('用户名或密码错误');
        }
    // } catch (error) {
    //     ElMessage.error(`网络问题，响应码: ${error.response.status}`);
    // }
}

// 定义函数，清空数据模型的数据
const clearRegisterData = () => {
    userRegisterData.value = {
        username: '',
        email: '',
        password: '',
        repassword: ''
    }
}

</script>

<template>
    <div class="login-page" :class="{ 'dark': isDark }">
      <div class="form" :class="{ 'dark': isDark }">
        <!-- 注册表单 -->
        <el-form ref="formRefRegister" size="large" autocomplete="off" v-if="isRegister" :model="userRegisterData" :rules="rules">
          <el-form-item>
            <h1>注册</h1>
          </el-form-item>
          <el-form-item prop="username">
            <el-input :prefix-icon="User" placeholder="请输入用户名（3~16位）" v-model="userRegisterData.username"></el-input>
          </el-form-item>
          <el-form-item prop="email">
            <el-input :prefix-icon="Message" placeholder="请输入邮箱" v-model="userRegisterData.email"></el-input>
          </el-form-item>
          <el-form-item prop="password">
            <el-input :prefix-icon="Lock" type="password" placeholder="请输入密码（5~16位）" v-model="userRegisterData.password"></el-input>
          </el-form-item>
          <el-form-item prop="repassword">
            <el-input :prefix-icon="Lock" type="password" placeholder="请输入再次密码（5~16位）" v-model="userRegisterData.repassword"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button class="button" type="primary" auto-insert-space @click="handleRegister">
              注册
            </el-button>
          </el-form-item>
          <el-form-item class="flex">
            <el-link type="info" :underline="false" @click="isRegister = false;clearRegisterData()">← 返回</el-link>
          </el-form-item>
        </el-form>
  
        <!-- 登录表单 -->
        <el-form ref="formRefLogin" size="large" autocomplete="off" v-else :model="userRegisterData" :rules="rules">
          <el-form-item>
            <h1>登录</h1>
          </el-form-item>
          <el-form-item prop="username">
            <el-input :prefix-icon="User" placeholder="请输入用户名" v-model="userRegisterData.username"></el-input>
          </el-form-item>
          <el-form-item prop="password">
            <el-input name="password" :prefix-icon="Lock" type="password" placeholder="请输入密码" v-model="userRegisterData.password"></el-input>
          </el-form-item>
          <el-form-item>
            <el-button class="button" type="primary" auto-insert-space @click="handleLogin">登录</el-button>
          </el-form-item>
          <el-form-item class="flex">
            <el-link type="info" :underline="false" @click="isRegister = true;clearRegisterData()">注册 →</el-link>
          </el-form-item>
        </el-form>
      </div>
    </div>
  </template>
  

<style lang="scss" scoped>
/* 样式 */
.login-page {
  height: 90vh;
  background-color: var(--bg-color);
  display: flex;
  justify-content: center;
  align-items: center;

  &.dark {
    .form {
      background: rgba(40, 40, 40, 0.7);
      box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
    }
  }
}

.form {
  width: 400px; 
  display: flex;
  flex-direction: column;
  justify-content: center;
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  padding: 2rem;
  border-radius: 8px;
  box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);

  .title {
    margin: 0 auto;
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--text-color);
  }

  .button {
    width: 100%;
    background: linear-gradient(45deg, #007CF0, #00DFD8);
    color: #fff;
    border: none;
    transition: background 0.3s;

    &:hover {
      background: linear-gradient(45deg, #005BB5, #00AFA0);
    }
  }

  .flex {
    width: 100%;
    display: flex;
    justify-content: space-between;
    margin-top: 1rem;

    .el-link {
      color: var(--text-color);
      font-weight: bold;
      transition: transform 0.2s ease, background-color 0.2s ease; /* 添加平滑的放大和背景色过渡效果 */

      &:hover {
        transform: scale(1.1); /* 鼠标悬浮时放大 */
        background-color: transparent; /* 鼠标悬浮时背景色透明 */
      }
    }
  }

  /* 明亮主题下的Form组件样式调整 */
  :deep(.el-input) {
    --el-input-bg-color: rgba(255, 255, 255, 0.8);
    --el-input-text-color: #333;
    --el-input-border-color: #dcdfe6;
    --el-input-hover-border-color: #c0c4cc;
    --el-input-focus-border-color: #409eff;

    .el-input__wrapper {
      background-color: var(--el-input-bg-color);
      box-shadow: 0 0 0 1px var(--el-input-border-color) inset;

      &:hover {
        box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset;
      }

      &.is-focus {
        box-shadow: 0 0 0 1px var(--el-input-focus-border-color) inset;
      }
    }

    input {
      color: var(--el-input-text-color);

      &::placeholder {
        color: #999;
      }
    }

    .el-input__prefix {
      color: #606266;
    }
  }

  /* 暗色主题下的样式覆盖 */
  &.dark {
    :deep(.el-input) {
      --el-input-bg-color: rgba(30, 30, 30, 0.8);
      --el-input-text-color: #e0e0e0;
      --el-input-border-color: #4c4c4c;
      --el-input-hover-border-color: #6a6a6a;
      --el-input-focus-border-color: #409eff;

      .el-input__wrapper {
        background-color: var(--el-input-bg-color);
        box-shadow: 0 0 0 1px var(--el-input-border-color) inset;

        &:hover {
          box-shadow: 0 0 0 1px var(--el-input-hover-border-color) inset;
        }
      }

      input {
        color: var(--el-input-text-color);

        &::placeholder {
          color: #888;
        }
      }

      .el-input__prefix {
        color: #bbb;
      }
    }

    h1 {
      color: #e0e0e0;
    }
  }
}
</style>

<style lang="scss">
/* 全局样式覆盖Element Plus的表单元素样式 */
html.dark {
  .el-form-item__label {
    color: #e0e0e0 !important;
  }
  
  .el-form-item__error {
    color: #ff6b6b !important;
  }
}
</style>