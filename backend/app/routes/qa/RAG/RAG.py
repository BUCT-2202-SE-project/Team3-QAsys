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



# # 构造 Prompt
# def build_prompt(knowledge_texts, query,*chat_context):
#     context = "\n".join(knowledge_texts)
#     return f"""请根据以下知识回答问题：

# {context}

# 问题：{query}
# 答：
# """

# def build_prompt(knowledge_texts, query, *chat_context):
#     # 处理知识库内容
#     context = "\n".join(knowledge_texts)
    
#     # 处理聊天上下文
#     chat_history_text = ""
    
#     # 检查是否有聊天上下文且非空
#     if chat_context:
#         history = []
#         for message in chat_context:
#             if message:  # 确保消息不为None
#                 if isinstance(message, dict):
#                     if 'role' in message and 'content' in message:
#                         role = "用户" if message['role'].lower() == "user" else "助手"
#                         history.append(f"{role}: {message['content']}")
#                     elif 'query' in message and 'answer' in message:
#                         history.append(f"用户: {message['query']}")
#                         history.append(f"助手: {message['answer']}")
#                 elif isinstance(message, (list, tuple)) and message:
#                     # 递归处理嵌套的对话历史
#                     for item in message:
#                         if item and isinstance(item, dict):
#                             if 'role' in item and 'content' in item:
#                                 role = "用户" if item['role'].lower() == "user" else "助手"
#                                 history.append(f"{role}: {item['content']}")
#                             elif 'query' in item and 'answer' in item:
#                                 history.append(f"用户: {item['query']}")
#                                 history.append(f"助手: {item['answer']}")
        
#         if history:
#             chat_history_text = "历史对话:\n" + "\n".join(history) + "\n\n"
    
#     # 构建最终的prompt
#     prompt = f"""请根据以下知识{'和历史对话' if chat_history_text else ''}回答问题：

# {context}

# """
    
#     if chat_history_text:
#         prompt += chat_history_text
    
#     prompt += f"""问题：{query}
# 答：
# """
    
#     return prompt
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

# Flask 路由：返回知识 + 流式回答
@app.route('/ask', methods=['POST'])
def ask_question():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400

    classification = classify_question_with_gpt(query)
    qtype = classification["type"]
    
    # 如果不是未知类型，使用统计类问题处理流程
    if qtype != "未知":
        print(f"处理统计类问题：{qtype}")
        answer = answer_statistical_question(query)
        return jsonify({
            "query": query,
            "answer": answer,
            "question_type": qtype

        })
        
    else :
        print("处理知识库检索问题")    
    knowledge = search_similar_knowledge(query)
    prompt = build_prompt(knowledge, query)

    def stream_with_reference():
        # 先返回知识引用
        yield f"event: reference\ndata: {json.dumps(knowledge, ensure_ascii=False)}\n\n"
        # 然后开始流式回答
        for chunk in generate_streaming_response(prompt):
            yield f"event: message\n{chunk}"

    return Response(stream_with_reference(), mimetype='text/event-stream')

@app.route('/ask_once', methods=['POST'])
def ask_question_once():
    data = request.get_json()
    query = data.get("query", "")
    if not query:
        return jsonify({"error": "Missing 'query' field"}), 400
    classification = classify_question_with_gpt(query)
    qtype = classification["type"]
    
    # 如果不是未知类型，使用统计类问题处理流程
    if qtype != "未知":
        print(f"处理统计类问题：{qtype}")
        answer = answer_statistical_question(query)
        return jsonify({
            "query": query,
            "answer": answer,
            "question_type": qtype
        })
    # 如果是未知类型，使用向量检索+大模型回答
    else:
        print("处理知识库检索问题")        
        
    knowledge = search_similar_knowledge(query)
    print(knowledge[:5])
    print("数据库搜索成功")
    prompt = build_prompt(knowledge, query)
    print("prompt构建成功")
    answer = ""

    # 非流式调用大模型
    response = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "system", "content": 
                "你是一个很厉害的博物馆ai助手噢,依据给出的参考整合成完整的语句之后,使用中文和markdown格式进行完整回答。如果没有找到参考，就使用大模型自己回答"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5,
        stream=False
    )
    answer = response.choices[0].message.content

    return jsonify({
        "query": query,
        "reference": knowledge,
        "answer": answer
    })



# 运行应用
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
