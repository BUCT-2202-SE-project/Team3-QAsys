import requests, json, re
from flask import jsonify, current_app
from database.mysql_client import get_db
import pymysql
from openai import OpenAI
def extract_entity_attributes(question):
    pattern1 = re.compile(r'(.*?)(的)?(.+?)(和|与|、)(.+?)是(什么|啥|怎么回事)?[？?]?')
    pattern2 = re.compile(r'^(?:请)?介绍(?:一下)?(?:一下)?(.*?)的(.*?)(?:吧|呗)?[.。]?$')
    # pattern2_1 = re.compile(r'^(?:请问)?(.+?)的(.+?)(?:是|有)?(?:什么|谁|哪个|多少|怎么样|如何)?[？?。.]?$')
    pattern2_1 = re.compile(r'^(?:请问)?(.+?)的(.+?)(?:是|有|在)?(?:什么|谁|哪个|哪里|何处|什么地方|多少|怎么样|如何)?[？?。.]?$')
    pattern3 = re.compile(r'^(.*?)(?:是否(?:为|是|来自))(.+?)[？?]?$')
    pattern4 = re.compile(r'^(.*?)是(?:那个|哪个|什么|啥)(.*?)[？?]?$')
    pattern5 = re.compile(r'^(.*?)是(?:什么|哪个|那个|啥)(.+?)的[？?]?$')

    match1 = pattern1.match(question)
    match2 = pattern2.match(question)
    match2_1 = pattern2_1.match(question)
    match3 = pattern3.match(question)
    match4 = pattern4.match(question) 
    match5 = pattern5.match(question)


    if match1:
        entity = match1.group(1).strip()
        attributes = [match1.group(3).strip(), match1.group(5).strip()]
        print('use pattern1')
        return {"entity": entity, "attributes": attributes}

    if match2:
        entity = match2.group(1).strip()
        attr_string = match2.group(2).strip()
        attributes = re.split(r'[和、,，与]', attr_string)
        attributes = [a.strip() for a in attributes if a.strip()]
        print('use pattern2')
        return {"entity": entity, "attributes": attributes}

    if match2_1:
        entity = match2_1.group(1).strip()
        attr_string = match2_1.group(2).strip()
        attributes = re.split(r'[和、,，与]', attr_string)
        attributes = [a.strip() for a in attributes if a.strip()]
        print('use pattern2_1')
        return {"entity": entity, "attributes": attributes}        
    
    if match3:
        entity = match3.group(1).strip()
        attr_value = match3.group(2).strip()

        # 清洗冗余修饰，如“所作”、“作品”、“藏品”等，按需可增强
        attr_value = re.sub(r'(所作|作品|藏品)?$', '', attr_value).strip()
        print('use pattern3')
        return {"entity": entity, "attributes": [attr_value], "question_type": "yes_no"}    

    if match4:
        entity = match4.group(1).strip()
        attr = match4.group(2).strip()
        print('use pattern4')
        return {"entity": entity, "attributes": [attr]}

    if match5:
        entity = match5.group(1).strip()
        attr = match5.group(2).strip()
        print('use pattern5')
        return {"entity": entity, "attributes": [attr]}

    return None # 不使用api兜底提取

    print('use api')
    # 正则没匹配上，就调用外部API抽取
    api_key = current_app.config['API_KEY']
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    prompt = f"""
        你是一个信息抽取助手，请从用户问题中提取出“实体名称”和“属性列表”。

        要求：
        - 实体名称必须从原问题中抽取，不得修改、翻译或简化；
        - 属性列表为数组格式，支持多个属性，且顺序与问题中出现顺序一致；
        - 支持以下属性名：作者、年代、特点、描述；
        - 对常见的同义表达进行归一化，例如：
        - 年份、创作年代 → 年代
        - 谁写的、写的人、作者是谁 → 作者
        - 特色、描写 → 特点 或 描述（根据语义）
        - 返回格式严格为 JSON 对象，属性名与字符串都使用双引号；
        - 示例输出格式为：{{"entity": "清明上河图", "attributes": ["年代", "作者"]}}；
        - 请注意，输出格式中的 attributes 要有 s；
        - 不要输出除 JSON 外的任何内容。

        现在请处理以下问题：{question}
    """

    data = {
        "model": "deepseek/deepseek-r1:free",
        "messages": [{
            "role": "user",
            "content": prompt
        }]
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data))
        response.raise_for_status()
        text = response.json()["choices"][0]["message"]["content"]
        text = re.sub(r"^```json|```$", "", text.strip()).strip()
        print(text)
        return json.loads(text)
    except Exception as e:
        print(f"LLM 解析失败: {e}")
        return None

def error_response(code=1, message='error', data=None, http_status=400):
    return jsonify({
        'code': code,
        'message': message,
        'data': data
    }), http_status

def save_qa_record(history_id, question, answer, reference=None):
    """保存问答记录到history表"""
    try:
        conn = get_db()
        cursor = conn.cursor()
        
        sql = """
        INSERT INTO history (history_id, question, answer, reference)
        VALUES (%s, %s, %s, %s)
        """
        
        cursor.execute(sql, (history_id, question, answer, reference))
        conn.commit()
        cursor.close()
        print(f"问答记录已保存到历史表，history_id={history_id}")
    except Exception as e:
        print(f"保存问答记录失败: {str(e)}")
        # 不抛出异常，确保主流程不受影响
        
        
# 实现上下文的记忆功能        
def get_history_context(history_id, max_count=5):
    conn = get_db()
    with conn.cursor(pymysql.cursors.DictCursor) as cursor:
        cursor.execute(
            "SELECT question, answer FROM history WHERE history_id = %s ORDER BY create_time DESC LIMIT %s",
            (history_id, max_count)
        )
        return list(reversed(cursor.fetchall()))  # 保持顺序：先旧后新

def build_chat_context(history_context, current_question):
    messages = [
        {"role": "system", "content": "你是一个专业、知识丰富的博物馆讲解AI助手，请基于上下文连续回答问题。"}
    ]
    for qa in history_context:
        messages.append({"role": "user", "content": qa["question"]})
        messages.append({"role": "assistant", "content": qa["answer"]})
    messages.append({"role": "user", "content": current_question})
    return messages


def enhance_query_with_llm(current_question, chat_context=None, max_context_length=3):
    """
    使用大模型整合当前问题和历史对话，生成语义丰富的搜索查询
    
    Args:
        current_question: 用户当前问题
        chat_context: 历史对话上下文列表
        max_context_length: 考虑的最大历史消息数量
    
    Returns:
        enhanced_query: 经过大模型处理后的查询语句
    """
    # 如果没有上下文，直接返回原问题
    if not chat_context or len(chat_context) == 0:
        return current_question
    
    # 提取最近的几轮对话
    recent_context = chat_context[-min(max_context_length*2, len(chat_context)):]
    
    # 构建提示
    context_text = "\n".join([
        f"{'用户' if msg['role']=='user' else 'assistant'}: {msg['content']}"
        for msg in recent_context
    ])
    
    # 构建系统提示
    system_prompt = (
        "你是一个专业的对话理解助手。你的任务是分析用户的对话历史和当前问题，"
        "提取关键信息并生成一个更完整的搜索查询，用于检索相关知识。"
        "请理解指代关系，解析省略的实体，并识别上下文中的重要概念。"
        "不要添加原问题中不存在的假设内容，只基于对话历史进行合理补充。"
    )
    
    # 构建用户提示
    user_prompt = f"""
历史对话:
{context_text}

当前问题: {current_question}

请基于以上对话历史和当前问题，生成一个更完整的搜索查询，以便更好地检索相关知识。
只返回增强后的查询语句，不需要其他解释。
"""
    
    try:
        client = OpenAI(
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            api_key="sk-a83d11ac8a3d498ab7d97343273299c3",
        )
        
        response = client.chat.completions.create(
            model="deepseek-r1",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3,
            max_tokens=150
        )
        
        enhanced_query = response.choices[0].message.content.strip()
        
        # 如果返回的查询为空或异常，回退到原问题
        if not enhanced_query or len(enhanced_query) < len(current_question)/2:
            return current_question
            
        return enhanced_query
    
    except Exception as e:
        print(f"查询增强失败: {e}")
        return current_question  # 出错时回退到原始问题
    
    
def extract_limit_from_attr(attr):
    # 匹配数字优先
    match = re.match(r'^(\d+)[件个]?(文物|藏品)$', attr)
    if match:
        return int(match.group(1))
    # 匹配中文数字（你也可以自定义转换逻辑）
    zh_map = {'一': 1, '二': 2, '三': 3, '四': 4, '五': 5,
              '六': 6, '七': 7, '八': 8, '九': 9, '十': 10}
    match = re.match(r'^([一二三四五六七八九十])[件个]?(文物|藏品)$', attr)
    if match:
        return zh_map.get(match.group(1), 5)
    # 默认
    return 5