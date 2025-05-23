import json
from pymilvus import Collection, connections
from sentence_transformers import SentenceTransformer
from openai import OpenAI

# 初始化向量模型和向量数据库连接
embed_model = SentenceTransformer("all-MiniLM-L6-v2")
connections.connect(
    host="127.0.0.1",  # 连接服务端地址，
    port=19530,        # 连接端口，milvus默认监听19530
    alias='default',   # 连接的别名，如果不设置，默认为default，
    db_name='default'  # 连接的数据库，默认是default
)
collection = Collection("museum_kg")  # 替换为你的向量库名称

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key="",
)

# Step 1：使用大模型提取三元组
def extract_triplets_by_llm(text):
    prompt = f"""请从下面的句子中提取所有主谓宾三元组。

    仅输出合法 JSON 数组（不要包含任何 Markdown 标记如```json）：

    句子：{text}

    输出格式：
    [
        {{"subject": "xxx", "predicate": "yyy", "object": "zzz"}}
    ]
    """
    response = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "system", "content": "你是一个中文信息抽取专家，擅长三元组抽取。"},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3
    )
    try:
        content = response.choices[0].message.content
        triplets = json.loads(content)
        return [(t["subject"], t["predicate"], t["object"]) for t in triplets]
    except Exception as e:
        print("三元组解析失败：", e)
        print("返回内容：", response.choices[0].message.content)
        return []

# Step 2：三元组向量检索
def search_similar_knowledge(triplets):
    results = []
    for h, r, t in triplets:
        query_text = f"{h} {r} {t}"
        query_vec = embed_model.encode([query_text])
        collection.load()
        search_result = collection.search(
            data=query_vec,
            anns_field="embedding",
            param={"metric_type": "L2", "params": {"nprobe": 10}},
            limit = 10,
            output_fields=["triple_text"]
        )
        for hit in search_result[0]:
            results.append(hit.entity.get("triple_text"))
    return list(set(results))

# Step 3：构造 Prompt 输入 LLM
def build_prompt(knowledge_texts, query):
    context = "\n".join(knowledge_texts)
    return f"""请根据以下知识回答问题：

        {context}

        问题：{query}
        答：
        """

# Step 4：调用大模型作答
def ask_llm(prompt):
    response = client.chat.completions.create(
        model="deepseek/deepseek-r1:free",
        messages=[
            {"role": "system", "content": "你是一个很厉害的博物馆ai助手噢,依据给出的参考进行完整回答"},
            {"role": "user", "content": prompt}
        ],
        temperature=0.5
    )
    return response.choices[0].message.content

# 主函数流程
def process_query(query):
    print("原始问题：", query)
    triplets = extract_triplets_by_llm(query)
    print("提取的三元组候选：", triplets)

    knowledge = search_similar_knowledge(triplets)
    print("召回的知识：", knowledge)

    prompt = build_prompt(knowledge, query)
    print("\n构造的Prompt:\n", prompt)

    answer = ask_llm(prompt)
    print("\n大模型回答：", answer)
    return answer

# 示例调用
if __name__ == "__main__":
    user_query = input("你有什么问题吗？我是一个很厉害的博物馆ai助手噢\n")
    process_query(user_query)