
from openai import OpenAI


def setup_llm():
    """设置 GPT-3.5 语言模型"""
    # 确保设置了 OpenAI API 密钥
    client = OpenAI(api_key=, base_url="https://api.chatanywhere.tech")

    response = client.chat.completions.create(
        model="gpt-3.5-turbo",
        messages=[
            {"role": "system", "content": "You are a helpful assistant"},
        ],
        stream=False
    )

    return response
