import {defineStore} from 'pinia';
import {ref} from 'vue';

const useChatIdStore = defineStore('ChatId', () => {
    // 定义状态相关的内容

    const chatId = ref('');

    const setChatId = (newChatId) => {
        chatId.value = newChatId;
    }

    const removeChatId = () => {
        chatId.value = '';
    }

    return {
        chatId,
        setChatId,
        removeChatId
    }

},{persist:true})

export default useChatIdStore;