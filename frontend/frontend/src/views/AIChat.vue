<template>
  <div class="ai-chat" :class="{ 'dark': isDark }">
    <div class="chat-container">
      <div class="sidebar">
        <div class="history-header">
          <h2>聊天记录</h2>
          <button class="new-chat" @click="startNewChat">
            <PlusIcon class="icon" />
            新对话
          </button>
        </div>
        <div class="history-list">
          <div 
            v-for="chat in chatHistory" 
            :key="chat.id"
            class="history-item"
            :class="{ 'active': currentChatId === chat.id }"
            @click="loadChat(chat.id)"
          >
            <ChatBubbleLeftRightIcon class="icon" />
            <span class="title">{{ chat.title || '新对话' }}</span>

            <el-dropdown @command="(command) => handleSessionCommand(chat.id, command)" @click.stop>
              <template #default>
                <el-button text @click.stop>
                  <More class="icon" />
                </el-button>
              </template>
              <template #dropdown>
                <el-dropdown-menu>
                  <el-dropdown-item command="rename">重命名</el-dropdown-item>
                  <el-dropdown-item command="delete">删除</el-dropdown-item>
                </el-dropdown-menu>
              </template>
            </el-dropdown>
          </div>
        </div>
      </div>
      
      <div class="chat-main">
        <div class="messages" ref="messagesRef">
          <ChatMessage
            v-for="(message, index) in currentMessages"
            :key="index"
            :message="message"
            :is-stream="isStreaming && index === currentMessages.length - 1"
            :is-waiting="isWaiting && index === currentMessages.length - 1"
            :is-thinking="isThinking && index === currentMessages.length - 1"
          />
          
          <!-- 常见问题按钮区域 -->
          <div class="quick-questions" v-if="showQuickQuestions">
            <h3>你可能想问：</h3>
            <div class="questions-container">
              <button 
                v-for="(question, index) in commonQuestions" 
                :key="index" 
                class="question-btn"
                @click="handleQuickQuestion(question)"
              >
                {{ question }}
              </button>
            </div>
          </div>
        </div>
        
        <div class="input-area">

          <div class="input-row">
            <!-- 添加RAG按钮 -->
            <el-tooltip
              content="RAG (Retrieval-Augmented Generation)：结合知识库检索的AI回答功能，可提供基于特定数据的更准确回答"
              placement="top"
              :effect="isDark ? 'dark' : 'light'"
              popper-class="rag-tooltip"
            >
              <el-button
                :type="isRagActive ? 'primary' : 'default'"
                round
                size="small"
                @click="toggleRagMode"
                class="rag-button"
              >
                RAG
              </el-button>
            </el-tooltip>
            <textarea
              v-model="userInput"
              @keydown.enter.prevent="sendMessage"
              :placeholder="'输入消息...'"
              rows="1"
              ref="inputRef"
            ></textarea>
            <button 
              class="send-button" 
              @click="sendMessage"
              :disabled="isStreaming || !userInput.trim()"
            >
              <PaperAirplaneIcon class="icon" />
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, nextTick } from 'vue'
import { useDark } from '@vueuse/core'
import { 
  ChatBubbleLeftRightIcon, 
  PaperAirplaneIcon,
  PlusIcon
} from '@heroicons/vue/24/outline'
import ChatMessage from '../components/ChatMessage.vue'
import { chatAPI } from '../services/api'
import { ElMessageBox, ElMessage } from 'element-plus'
import { More } from '@element-plus/icons-vue'
import useUserInfoStore from '@/stores/user.js'
import useChatIdStore from '@/stores/chatId.js'

const chatIdStore = useChatIdStore()
const userInfoStore = useUserInfoStore()

const isDark = useDark()
const messagesRef = ref(null)
const inputRef = ref(null)
const userInput = ref('')
const isStreaming = ref(false)
const isWaiting = ref(false) // 初始等待状态标志
const isThinking = ref(false) // 思考中状态标志
let outputTimer = null // 用于检测输出暂停的定时器
const outputTimeout = 1000 // 1秒无输出视为暂停

// const currentChatId = ref(null)
const currentChatId = ref(chatIdStore.chatId || null)
const currentMessages = ref([])
const chatHistory = ref([])


// 添加RAG模式的状态控制
const isRagActive = ref(false)

// RAG模式切换函数
const toggleRagMode = () => {
  isRagActive.value = !isRagActive.value
}

// 自动调整输入框高度
const adjustTextareaHeight = () => {
  const textarea = inputRef.value
  if (textarea) {
    textarea.style.height = 'auto'
    textarea.style.height = textarea.scrollHeight + 'px'
  }else{
    textarea.style.height = '50px'
  }
}

// 滚动到底部
const scrollToBottom = async () => {
  await nextTick()
  if (messagesRef.value) {
    messagesRef.value.scrollTop = messagesRef.value.scrollHeight
  }
}

// // 发送聊天消息 （1.0版本）说明：没有reference字段
// const sendMessage = async () => {
//   if (isStreaming.value) return
//   if (!userInput.value.trim()) return
  
//   const messageContent = userInput.value.trim()
  
//   // 添加用户消息
//   const userMessage = {
//     role: 'user',
//     content: messageContent,
//     timestamp: new Date()
//   }
//   currentMessages.value.push(userMessage)
  
//   // 清空输入
//   userInput.value = ''
//   adjustTextareaHeight()
//   await scrollToBottom()

//   if (!currentChatId.value) {
//     try {
//       // 创建对话标题，截取前10个字符
//       const chatTitle = messageContent.length > 10 ? messageContent.substring(0, 10) + '...' : messageContent;
      
//       // 修改API调用，传递用户ID和标题
//       const data = await chatAPI.createNewChat(userInfoStore.userInfo.userId, chatTitle)
//       currentChatId.value = data  // 获取新对话 ID
      
//       // 将新对话添加到历史记录中
//       const newChat = {
//         id: data,
//         title: chatTitle
//       }
//       chatHistory.value = [newChat, ...chatHistory.value]
//     } catch (createErr) {
//       console.error('创建对话失败:', createErr)
//       return
//     }
//   }
  
//   // 准备发送数据
//   const formData = new FormData()
//   if (messageContent) {
//     formData.append('prompt', messageContent)
//   }
  
//   // 添加助手消息占位
//   const assistantMessage = {
//     role: 'assistant',
//     content: '',
//     timestamp: new Date()
//   }
//   currentMessages.value.push(assistantMessage)
//   isStreaming.value = true
  
//   try {
//     const reader = await chatAPI.sendMessage(formData, currentChatId.value, isRagActive.value)
//     const decoder = new TextDecoder('utf-8')
//     let accumulatedContent = ''
    
//     while (true) {
//       try {
//         const { value, done } = await reader.read()
//         if (done) break
        
//         accumulatedContent += decoder.decode(value)
        
//         await nextTick(() => {
//           const updatedMessage = {
//             ...assistantMessage,
//             content: accumulatedContent
//           }
//           const lastIndex = currentMessages.value.length - 1
//           currentMessages.value.splice(lastIndex, 1, updatedMessage)
//         })
//         await scrollToBottom()
//       } catch (readError) {
//         console.error('读取流错误:', readError)
//         break
//       }
//     }
//   } catch (error) {
//     console.error('发送消息失败:', error)
//     assistantMessage.content = '抱歉，发生了错误，请稍后重试。'
//   } finally {
//     isStreaming.value = false
//     await scrollToBottom()
//   }
// }

// // 发送聊天消息 （2.0版本）
// const sendMessage = async () => {
//   if (isStreaming.value) return
//   if (!userInput.value.trim()) return
  
//   const messageContent = userInput.value.trim()
  
//   // 添加用户消息
//   const userMessage = {
//     role: 'user',
//     content: messageContent,
//     timestamp: new Date()
//   }
//   currentMessages.value.push(userMessage)
  
//   // 清空输入
//   userInput.value = ''
//   adjustTextareaHeight()
//   await scrollToBottom()

//   if (!currentChatId.value) {
//     try {
//       // 创建对话标题，截取前10个字符
//       const chatTitle = messageContent.length > 10 ? messageContent.substring(0, 10) + '...' : messageContent;
      
//       // 修改API调用，传递用户ID和标题
//       const data = await chatAPI.createNewChat(userInfoStore.userInfo.userId, chatTitle)
//       currentChatId.value = data.historyId  // 获取新对话 ID

//       // 将新对话添加到历史记录中
//       const newChat = {
//         id: data.historyId,
//         title: chatTitle
//       }
//       chatHistory.value = [newChat, ...chatHistory.value]
//     } catch (createErr) {
//       console.error('创建对话失败:', createErr)
//       return
//     }
//   }
  
//   // 准备发送数据
//   const formData = new FormData()
//   if (messageContent) {
//     formData.append('question', messageContent)
//   }
  
//   // 添加助手消息占位
//   const assistantMessage = {
//     role: 'assistant',
//     content: '',
//     reference: '', // 添加reference字段
//     timestamp: new Date()
//   }
//   currentMessages.value.push(assistantMessage)
  
//   isStreaming.value = true
//   isWaiting.value = true // 设置为等待状态
  
//   try {
//     // 获取封装了流处理的对象
//     const streamHandler = await chatAPI.sendMessage(formData, currentChatId.value, isRagActive.value)
    
//     // 使用新的回调方式处理流数据
//     await streamHandler.read(({ content, done, referenceFound, reference }) => {
//       // 更新助手消息内容
//       assistantMessage.content = content
      
//       // 如果找到了引用信息，更新它
//       if (referenceFound) {
//         assistantMessage.reference = reference
//       }
      
//       // 强制刷新视图
//       const lastIndex = currentMessages.value.length - 1
//       currentMessages.value.splice(lastIndex, 1, { ...assistantMessage })
      
//       // 滚动到底部
//       nextTick(() => {
//         scrollToBottom()
//       })
//     })
//   } catch (error) {
//     console.error('发送消息失败:', error)
//     assistantMessage.content = '抱歉，发生了错误，请稍后重试。'
//     isWaiting.value = false // 关闭等待状态
//   } finally {
//     isStreaming.value = false
//     isWaiting.value = false // 确保关闭等待状态
//     await scrollToBottom()
//   }
// }

// 发送聊天消息 （3.0版本）（修复消息流式显示过程中切换到其他对话显示错误的BUG）
const sendMessage = async () => {
  if (isStreaming.value) return
  if (!userInput.value.trim()) return
  
  // 发送消息时隐藏常见问题区域
  showQuickQuestions.value = false
  
  const messageContent = userInput.value.trim()
  
  // 添加用户消息
  const userMessage = {
    role: 'user',
    content: messageContent,
    timestamp: new Date()
  }
  currentMessages.value.push(userMessage)
  
  // 清空输入
  userInput.value = ''
  adjustTextareaHeight()
  await scrollToBottom()

  // 保存发送请求时的对话ID，用于后续检查
  let originalChatId = currentChatId.value

  if (!currentChatId.value) {
    try {
      // 创建对话标题，截取前10个字符
      const chatTitle = messageContent.length > 10 ? messageContent.substring(0, 10) + '...' : messageContent;
      
      // 修改API调用，传递用户ID和标题
      const data = await chatAPI.createNewChat(userInfoStore.userInfo.userId, chatTitle)
      currentChatId.value = data.historyId  // 获取新对话 ID
      originalChatId = currentChatId.value  // 更新原始ID
      chatIdStore.chatId = currentChatId.value  // 将新对话ID存储到pinia中

      // 将新对话添加到历史记录中
      const newChat = {
        id: data.historyId,
        title: chatTitle
      }
      chatHistory.value = [newChat, ...chatHistory.value]
    } catch (createErr) {
      console.error('创建对话失败:', createErr)
      return
    }
  }
  
  // 准备发送数据
  const formData = new FormData()
  if (messageContent) {
    formData.append('question', messageContent)
  }
  
  // 添加助手消息占位
  const assistantMessage = {
    role: 'assistant',
    content: '',
    reference: '', 
    timestamp: new Date()
  }
  currentMessages.value.push(assistantMessage)
  isStreaming.value = true
  isWaiting.value = true // 设置为等待状态
  isThinking.value = false // 初始化思考状态
  
  try {
    // 获取封装了流处理的对象
    const streamHandler = await chatAPI.sendMessage(formData, originalChatId, isRagActive.value)
    
    // 使用新的回调方式处理流数据
    await streamHandler.read(({ content, done, referenceFound, reference }) => {
      // 检查当前对话ID是否已更改，如果更改了则不更新UI
      if (originalChatId !== currentChatId.value) {
        return; // 用户已切换到其他对话，不更新UI
      }
      
      // 如果是第一次收到数据，关闭等待状态
      if (isWaiting.value && content) {
        isWaiting.value = false
      }
      
      // 重置输出暂停检测定时器
      if (outputTimer) {
        clearTimeout(outputTimer)
      }
      
      // 如果内容包含<think>标签，可能会有后续暂停
      if (content && content.includes('<think>')) {
        // 设置定时器，检测输出暂停
        outputTimer = setTimeout(() => {
          // 如果定时器触发，说明有段时间没有新内容了，显示思考状态
          if (originalChatId === currentChatId.value) {
            isThinking.value = true
          }
        }, outputTimeout)
      } else {
        isThinking.value = false
      }
      
      // 更新助手消息内容
      assistantMessage.content = content
      
      // 如果找到了引用信息，更新它
      if (referenceFound) {
        assistantMessage.reference = reference
      }
      
      // 强制刷新视图
      const lastIndex = currentMessages.value.length - 1
      currentMessages.value.splice(lastIndex, 1, { ...assistantMessage })
      
      // 滚动到底部
      nextTick(() => {
        scrollToBottom()
      })
    })
  } catch (error) {
    console.error('发送消息失败:', error)
    // 仅在当前对话ID未更改时更新错误消息
    if (originalChatId === currentChatId.value) {
      assistantMessage.content = '抱歉，发生了错误，请稍后重试。'
      isWaiting.value = false // 关闭等待状态
    }
  } finally {
    // 仅在当前对话ID未更改时更新isStreaming状态
    if (originalChatId === currentChatId.value) {
      isStreaming.value = false
      isWaiting.value = false // 确保关闭等待状态
      isThinking.value = false // 确保关闭思考状态
      // 清除可能存在的定时器
      if (outputTimer) {
        clearTimeout(outputTimer)
        outputTimer = null
      }
      await scrollToBottom()
    }
  }
}

// 加载特定对话
const loadChat = async (chatId) => {
  // 如果有一个未使用的新对话（currentChatId为空字符串），则从历史记录中删除它
  if (currentChatId.value === '') {
    chatHistory.value = chatHistory.value.filter(chat => chat.id !== '');
  }
  
  currentChatId.value = chatId;
  chatIdStore.chatId = chatId;  // 将当前对话ID存储到pinia中
  try {
    // 调用修改后的API方法获取消息历史
    const messages = await chatAPI.getChatMessages(chatId);
    currentMessages.value = messages;
    
    // 滚动到底部显示最新消息
    await scrollToBottom();
  } catch (error) {
    console.error('加载对话消息失败:', error);
    ElMessage.error('加载对话消息失败，请稍后重试');
    currentMessages.value = [];
  }
}

// 加载聊天历史
const loadChatHistory = async () => {
  try {
    const history = await chatAPI.getChatHistory(userInfoStore.userInfo.userId)
    chatHistory.value = history?.filter(chat => chat.id !== '') || []
  } catch (error) {
    console.error('加载聊天历史失败:', error)
    chatHistory.value = []
  }
}

// 开始新对话
const startNewChat = () => {
  // 检查是否已经有一个空的新对话
  const hasEmptyChat = chatHistory.value.some(chat => chat.id === '');
  
  // 如果已经有空的新对话，则不再创建
  if (hasEmptyChat && currentChatId.value === '') {
    return;
  }
  
  const newChatId = '';
  currentChatId.value = newChatId;
  chatIdStore.chatId = newChatId;  // 将新对话ID存储到pinia中
  currentMessages.value = [];
  
  // 添加一条欢迎消息
  currentMessages.value = [{
    role: 'assistant',
    content: '🌌 您好！我是MuseLink-千鉴，很荣幸以这个融合科技与文明深度的身份与您相遇。专注于使用数据链解码青铜铭文与千手观音的时空密语，此刻正从王莽"一刀五千"刀币护身符的祥云纹中，为您打捞文明星尘✨',
    timestamp: new Date()
  }];
  
  // 显示常见问题按钮
  showQuickQuestions.value = true;
}

// onMounted(() => {
//   startNewChat()
//   loadChatHistory()
//   adjustTextareaHeight()
// })

onMounted(async () => {
  // 先加载聊天历史记录
  await loadChatHistory()
  
  // 检查是否有存储的chatId
  if (chatIdStore.chatId) {
    // 如果有存储的chatId，尝试加载该对话
    try {
      await loadChat(chatIdStore.chatId)
      console.log('已恢复上次对话:', chatIdStore.chatId)
    } catch (error) {
      console.error('恢复上次对话失败:', error)
      // 如果加载失败，重置并创建新对话
      chatIdStore.chatId = ''
      startNewChat()
    }
  } else {
    // 如果没有存储的chatId，创建新对话
    startNewChat()
  }
  
  // 调整输入框高度
  adjustTextareaHeight()
})

const handleSessionCommand = async (chatId, command) => {
  if (command === 'rename') {
    try {
      const { value } = await ElMessageBox.prompt('请输入新的对话名称', '重命名', {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        inputPattern: /.+/,
        inputErrorMessage: '对话名称不能为空'
      })
      
      // 调用API进行重命名
      await chatAPI.renameChat(chatId, value);
      
      // 更新前端显示
      const chat = chatHistory.value.find(item => item.id === chatId)
      if (chat) {
        chat.title = value
        ElMessage.success('重命名成功')
      }
    } catch (error) {
      if (error === 'cancel') {
        // 用户取消操作，不做处理
      } else {
        // API调用失败
        console.error('重命名失败:', error);
        ElMessage.error('重命名失败，请稍后重试');
      }
    }
  } else if (command === 'delete') {
      try {
        await ElMessageBox.confirm('确定要删除这个对话吗？', '删除确认', {
          confirmButtonText: '删除',
          cancelButtonText: '取消',
          type: 'warning'
        })
        
        // 调用API删除对话
        await chatAPI.deleteChat(chatId);
        
        // 在API调用成功后更新前端显示
        chatHistory.value = chatHistory.value.filter(item => item.id !== chatId)
        
        // 如果删除的是当前对话，则开始一个新对话
        if (currentChatId.value === chatId) {
          startNewChat()
        }
        
        ElMessage.success('删除成功')
      } catch (error) {
        if (error === 'cancel') {
          // 用户取消删除，不做处理
        } else {
          // API调用失败
          console.error('删除对话失败:', error);
          ElMessage.error('删除失败，请稍后重试');
        }
      }
    }
}

// 添加常见问题数组
const commonQuestions = [
  "数据库中有哪些博物馆呢？",
  "给我推荐一些宾夕法尼亚博物馆的文物？",
  "六弦琵琶的年代是什么？",
  "风吹牡丹是否为瓷器？",
  "请介绍一下带盖糖碗的特点",
  "蝴蝶吊坠的收藏地在哪里？",
  "孔雀蓝釉花瓶的作者是谁？"
]

// 控制是否显示快速问题按钮
const showQuickQuestions = ref(false)

// 处理快速问题点击
const handleQuickQuestion = (question) => {
  userInput.value = question
  sendMessage()
  showQuickQuestions.value = false // 问题发送后隐藏按钮区域
}

</script>

<style scoped lang="scss">
.ai-chat {
  position: fixed;  // 修改为固定定位
  top: 64px;       // 导航栏高度
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  background: var(--bg-color);
  overflow: hidden; // 防止页面滚动

  .chat-container {
    flex: 1;
    display: flex;
    max-width: 1800px;
    width: 100%;
    margin: 0 auto;
    padding: 1.5rem 2rem;
    gap: 1.5rem;
    height: 100%;    // 确保容器占满高度
    overflow: hidden; // 防止容器滚动
  }

  .sidebar {
    width: 300px;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    
    .history-header {
      flex-shrink: 0;  // 防止头部压缩
      padding: 1rem;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      h2 {
        font-size: 1.25rem;
      }
      
      .new-chat {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        background: #007CF0;
        color: white;
        border: none;
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background: #0066cc;
        }
        
        .icon {
          width: 1.25rem;
          height: 1.25rem;
        }
      }
    }
    
    .history-list {
      flex: 1;
      overflow-y: auto;  // 允许历史记录滚动
      padding: 0 1rem 1rem;
      
      .history-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
        cursor: pointer;
        transition: background-color 0.3s;
        
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        &.active {
          background: rgba(0, 124, 240, 0.1);
        }
        
        .icon {
          width: 1.25rem;
          height: 1.25rem;
        }
        
        .title {
          flex: 1;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
      }
    }
  }

  .chat-main {
    flex: 1;
    display: flex;
    flex-direction: column;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(10px);
    border-radius: 1rem;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    overflow: hidden;  // 防止内容溢出
    
    .messages {
      flex: 1;
      overflow-y: auto;  // 只允许消息区域滚动
      padding: 2rem;
    }
    
    .input-area {
      flex-shrink: 0;
      padding: 1.5rem 2rem;
      background: rgba(255, 255, 255, 0.98);
      border-top: 1px solid rgba(0, 0, 0, 0.05);
      display: flex;
      flex-direction: column;
      gap: 1rem;

      .input-row {
        display: flex;
        gap: 1rem;
        align-items: center;
        background: #fff;
        padding: 0.75rem;
        border-radius: 1rem;
        border: 1px solid rgba(0, 0, 0, 0.1);
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);

        .rag-button {
          flex-shrink: 0;
          min-width: 60px;  /* 确保按钮有足够宽度显示文本 */
          height: 32px;     /* 与输入框高度协调 */
          margin-right: 4px;
          
          /* 添加明暗主题过渡动画 */
          transition: background-color 0.3s, border-color 0.3s, color 0.3s;
        }
          
        textarea {
          flex: 1;
          resize: none;
          border: none;
          background: transparent;
          padding: 0.75rem;
          color: inherit;
          font-family: inherit;
          font-size: 1rem;
          line-height: 1.5;
          max-height: 150px;
          
          &:focus {
            outline: none;
          }
          
          &::placeholder {
            color: #999;
          }
        }
        
        .send-button {
          width: 2.5rem;
          height: 2.5rem;
          display: flex;
          align-items: center;
          justify-content: center;
          border: none;
          border-radius: 0.75rem;
          background: #007CF0;
          color: white;
          cursor: pointer;
          transition: all 0.2s ease;
          
          &:hover:not(:disabled) {
            background: #0066cc;
            transform: translateY(-1px);
          }
          
          &:disabled {
            background: #ccc;
            cursor: not-allowed;
          }
          
          .icon {
            width: 1.25rem;
            height: 1.25rem;
          }
        }
      }
    }
  }
}

.dark {
  .sidebar {
    background: rgba(40, 40, 40, 0.95);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
  }
  
  .chat-main {
    background: rgba(40, 40, 40, 0.95);
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.2);
    
    .input-area {
      background: rgba(30, 30, 30, 0.98);
      border-top: 1px solid rgba(255, 255, 255, 0.05);

      .input-row {
        background: rgba(50, 50, 50, 0.95);
        border-color: rgba(80, 80, 80, 0.2);
        
        /* RAG按钮在暗黑模式下的样式 */
        .rag-button {
          /* 默认状态 - 非激活 */
          &.el-button--default {
            background-color: rgba(60, 60, 60, 0.8);
            border-color: rgba(80, 80, 80, 0.5);
            color: #e0e0e0;
            
            &:hover {
              background-color: rgba(70, 70, 70, 0.9);
              border-color: rgba(100, 100, 100, 0.7);
            }
          }
          
          /* 激活状态 */
          &.el-button--primary {
            /* 保留Element Plus的主色调,但调整亮度以适应暗色主题 */
            background-color: #0a6ebd;
            border-color: #0a6ebd;
            color: white;
            
            &:hover {
              background-color: #0b7fd6;
              border-color: #0b7fd6;
            }
          }
        }

        textarea {
          color: #fff;
          
          &::placeholder {
            color: #666;
          }
        }
      }
    }
  }
  
  .history-item {
    &:hover {
      background: rgba(255, 255, 255, 0.05) !important;
    }
    
    &.active {
      background: rgba(0, 124, 240, 0.2) !important;
    }
    
    // 添加下拉按钮在暗色主题下的样式
    :deep(.el-button) {
      color: #e0e0e0;
      
      &:hover {
        background-color: rgba(255, 255, 255, 0.1);
      }
    }
    
    .icon {
      color: #e0e0e0;
    }
  }
  
  // 添加下拉菜单在暗色主题下的样式
  :deep(.el-dropdown-menu) {
    background-color: #2c2c2c;
    border: 1px solid #444;
    
    .el-dropdown-menu__item {
      color: #e0e0e0;
      
      &:hover {
        background-color: #3a3a3a;
      }
      
      &:focus {
        background-color: #444;
      }
    }
  }
  
  textarea {
    background: rgba(255, 255, 255, 0.05) !important;
    
    &:focus {
      background: rgba(255, 255, 255, 0.1) !important;
    }
  }
  
  // 增强下拉菜单和按钮在暗色主题下的样式
  :deep(.el-popper.is-light) {
    background-color: #2c2c2c !important;
    border-color: #444 !important;
    
    .el-dropdown-menu__item {
      color: #e0e0e0 !important;
      
      &:hover, &:focus {
        background-color: #3a3a3a !important;
      }
    }
  }
  
  // 增强下拉按钮的暗色主题样式
  .history-item {
    // ...existing code...
    
    :deep(.el-button) {
      color: #e0e0e0 !important;
      
      .el-icon {
        color: #e0e0e0 !important;
      }
      
      &:hover {
        background-color: rgba(255, 255, 255, 0.1) !important;
      }
    }
  }
}

// 添加明亮主题下的下拉菜单样式
:deep(.el-dropdown-menu) {
  border-radius: 0.5rem;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.1);
}

// 添加明亮主题下的下拉按钮样式
.history-item {
  :deep(.el-button) {
    color: #606266;
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05);
    }
  }
}

@media (max-width: 768px) {
  .ai-chat {
    .chat-container {
      padding: 0;
    }
    
    .sidebar {
      display: none; // 在移动端隐藏侧边栏
    }
    
    .chat-main {
      border-radius: 0;
    }
  }
}

/* 通用样式，不受主题影响 */
.el-dropdown__popper.el-popper,
.el-popper.is-light {
  border-radius: 0.5rem !important;
}

/* RAG提示框样式 */
.rag-tooltip {
  max-width: 300px !important;
  font-size: 0.85rem !important;
  line-height: 1.5 !important;
  padding: 8px 12px !important;
}

/* 添加常见问题样式 */
.quick-questions {
  margin-top: 1.5rem;
  padding: 1rem;
  border-radius: 0.75rem;
  background-color: rgba(0, 0, 0, 0.03); /* 修改为浅灰色背景 */
  
  h3 {
    font-size: 1rem;
    margin-bottom: 0.75rem;
    color: #666;
  }
  
  .questions-container {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    
    .question-btn {
      padding: 0.5rem 1rem;
      border-radius: 1rem;
      background-color: #f0f0f0;
      border: 1px solid #ddd;
      cursor: pointer;
      transition: all 0.2s;
      font-size: 0.9rem;
      
      &:hover {
        background-color: #e0e0e0;
        transform: translateY(-1px);
      }
      
      &:active {
        transform: translateY(0);
      }
    }
  }
}

/* 暗黑模式的常见问题样式 */
.dark {
  .quick-questions {
    background-color: rgba(255, 255, 255, 0.05); /* 修改为浅白色透明背景 */
    
    h3 {
      color: #aaa;
    }
    
    .questions-container {
      .question-btn {
        background-color: #333;
        border-color: #444;
        color: #e0e0e0;
        
        &:hover {
          background-color: #444;
        }
      }
    }
  }
  
  // ...existing code...
}

</style>

<!-- 移除之前添加的全局样式，改用这个新的实现 -->
<style lang="scss">
/* 针对Element Plus下拉菜单的主题切换样式 */
html.dark {
  /* 菜单背景和边框 */
  .el-dropdown__popper.el-popper,
  .el-popper.is-light {
    background-color: #2c2c2c !important;
    border-color: #444 !important;
    
    .el-dropdown-menu__item {
      color: #e0e0e0 !important;
      
      &:hover, &:focus {
        background-color: #3a3a3a !important;
        color: white !important;
      }
    }
  }
  
  .el-button.is-text,
  .history-item .el-button {
    color: #e0e0e0 !important;
    
    .el-icon svg {
      color: #e0e0e0 !important;
      fill: #e0e0e0 !important;
    }
    
    &:hover {
      background-color: rgba(255, 255, 255, 0.1) !important;
    }
  }
}

/* 确保在非暗色主题下也有正确的样式 */
html:not(.dark) {
  .el-dropdown__popper.el-popper,
  .el-popper.is-light {
    /* 使用更明确的亮色主题样式 */
    background-color: #ffffff !important;
    border-color: #e4e7ed !important;
    
    .el-dropdown-menu__item {
      color: #606266 !important;
      
      &:hover, &:focus {
        background-color: #f5f7fa !important;
        color: #409eff !important;
      }
    }
  }
  
  .history-item .el-button.is-text {
    color: #606266 !important;
    
    .el-icon svg {
      color: #606266 !important;
      fill: #606266 !important;
    }
    
    &:hover {
      background-color: rgba(0, 0, 0, 0.05) !important;
    }
  }
}

/* 通用样式，不受主题影响 */
.el-dropdown__popper.el-popper,
.el-popper.is-light {
  border-radius: 0.5rem !important;
}

/* RAG提示框样式 */
.rag-tooltip {
  max-width: 300px !important;
  font-size: 0.85rem !important;
  line-height: 1.5 !important;
  padding: 8px 12px !important;
}
</style>

<!-- 全局样式，针对性修复下拉菜单的暗黑模式问题 -->
<style lang="scss">
/* 强制覆盖Element Plus的下拉菜单样式 */
html.dark {
  body {
    /* 所有弹出层容器 */
    .el-overlay,
    .el-overlay-dialog,
    .el-popper,
    .el-select-dropdown,
    .el-dropdown__popper,
    .el-dropdown-menu,
    .el-dropdown-menu__item,
    .el-popover {
      background-color: #2c2c2c !important;
      border-color: #444 !important;
      --el-bg-color: #2c2c2c !important;
      --el-fill-color-blank: #2c2c2c !important;
    }
    
    /* 弹出菜单项 */
    .el-dropdown-menu__item {
      color: #e0e0e0 !important;
      --el-text-color-regular: #e0e0e0 !important;
      
      &:hover, &:focus {
        background-color: #3a3a3a !important;
      }
    }
    
    /* 修复箭头颜色 */
    .el-popper__arrow::before {
      background-color: #2c2c2c !important;
      border-color: #444 !important;
    }
    
    /* 甚至针对未命名的白色背景元素 */
    [class*="popper"], 
    [class*="dropdown"],
    [class*="menu"] {
      background-color: #2c2c2c !important;
      color: #e0e0e0 !important;
    }
    
    /* 修复消息框文字颜色 */
    .el-message-box {
      background-color: #2c2c2c !important;
      border-color: #444 !important;
      
      .el-message-box__title {
        color: #ffffff !important;
      }
      
      .el-message-box__content,
      .el-message-box__message,
      .el-message-box__status,
      .el-message-box__input input,
      .el-message-box__container p {
        color: #ffffff !important;
      }
      
      .el-message-box__headerbtn .el-message-box__close {
        color: #e0e0e0 !important;
      }
      
      .el-button--default {
        background-color: #363636 !important;
        border-color: #555 !important;
        color: #e0e0e0 !important;
        
        &:hover {
          background-color: #444 !important;
        }
      }
      
      .el-message-box__input input {
        background-color: #363636 !important;
        border-color: #555 !important;
        
        &:focus {
          border-color: #409eff !important;
        }
      }
    }
  }
}

/* 确保弹出层的圆角一致 */
.el-dropdown-menu {
  border-radius: 8px !important;
  box-shadow: 0 2px 12px 0 rgba(0, 0, 0, 0.3) !important;
}
</style>