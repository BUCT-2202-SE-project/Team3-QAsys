from flask import Flask, request, jsonify, Response
import json
from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer
from openai import OpenAI
import threading
import queue
import time
from app.routes.qa.RAG.Statistics import classify_question_with_gpt,answer_statistical_question

app = Flask(__name__)

# 初始化模型与数据库连接
embed_model = SentenceTransformer("all-MiniLM-L6-v2")

connections.connect(
    host="127.0.0.1",
    port=19530,
    alias='default',
    db_name='default'
)
collection = Collection("museum_kg")

client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="", 
)

# 向量检索
def search_similar_knowledge(query):


    query_vec = embed_model.encode([query])
    collection.load()
    search_result = collection.search(
        data=query_vec,
        anns_field="embedding",
        param={"metric_type": "L2", "params": {"nprobe": 10}},
        limit=10,
        output_fields=["triple_text"]
    )
    results = []
    for hit in search_result[0]:
        results.append(hit.entity.get("triple_text")+"\n")
    return list(set(results))

def build_prompt(knowledge, question, chat_context=None):
    """
    构建包含知识库内容和对话历史的提示
    """
    # 构建基础提示
    base_prompt = f"""请基于以下参考信息回答用户的问题。
如果参考信息不足以回答问题，请基于你自己的知识进行回答，但明确指出这部分是你自己的理解。

参考信息:
{json.dumps(knowledge, ensure_ascii=False)}

"""
    
    # 如果有对话历史，添加到提示中
    if chat_context and len(chat_context) > 0:
        # 提取最近的3轮对话
        recent_context = chat_context[-min(6, len(chat_context)):]
        context_text = "\n".join([
            f"{'用户' if msg['role']=='user' else 'AI'}: {msg['content']}"
            for msg in recent_context
        ])
        
        base_prompt += f"""
对话历史:
{context_text}

请考虑上述对话历史，理解用户的指代关系和潜在意图。
"""
    
    # 添加当前问题
    base_prompt += f"""
用户当前问题: {question}

请提供信息丰富、结构清晰的回答，使用中文和markdown格式。回答应保持与对话历史的连贯性。
"""
    
    return base_prompt
# Stream 输出函数（生成器）
def generate_streaming_response(prompt):
    response = client.chat.completions.create(
        model="deepseek-r1",
        messages=[
            {"role": "system", "content": "你是一个很厉害的博物馆ai助手噢,依据给出的参考使用中文进行完整回答"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        stream=True
    )
    for chunk in response:
        if chunk.choices[0].delta.content:
            yield f"data: {chunk.choices[0].delta.content}\n\n"
        time.sleep(0.01)
    yield "data: [DONE]\n\n"

