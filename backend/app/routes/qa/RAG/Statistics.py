import json
from openai import OpenAI
from rapidfuzz import process
from pypinyin import lazy_pinyin
import re

# 读取结构化索引
with open("app/routes/qa/RAG/structured_index.json", "r", encoding="utf-8") as f:
    index = json.load(f)

# 初始化 OpenAI 客户端
client = OpenAI(
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
    api_key="", 
)

def get_best_match(name, entity_list):
    def to_pinyin(text):
        return ''.join(lazy_pinyin(text))

    input_pinyin = to_pinyin(name)
    pinyin_list = [to_pinyin(entity) for entity in entity_list]
    matches = process.extract(input_pinyin, pinyin_list, limit=1)

    if matches and matches[0][1] > 80:
        matched_pinyin = matches[0][0]
        for i, py in enumerate(pinyin_list):
            if py == matched_pinyin:
                return entity_list[i]
    return None


def classify_question_with_gpt(question):
    prompt = f"""
你是一个问答系统中的问题分类模块，负责识别用户问题的类型和相关实体。请根据以下问题提取出：
1. 问题类型（从以下列表中选择一个）：
- 博物馆数量
- 每个博物馆藏品数
- 艺术家数量
- 艺术家作品数
- 历史时期数量
- 藏品总数
- 未知
2. 实体名（如艺术家或博物馆名称，若无请返回 null）

问题：{question}

输出格式：
{{"type": "问题类型", "entity": "实体名或 null"}}

注意：请直接返回JSON格式，不要使用Markdown代码块格式。
"""

    res = client.chat.completions.create(
        model="deepseek-r1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )
    print(res.choices[0].message.content)
    return json.loads(res.choices[0].message.content)


def get_structured_answer(qtype, entity):
    object_info = index.get("object_info", {})
    
    if qtype == "博物馆数量":
        museum_info = []
        for museum, obj_ids in index['museum_to_objects'].items():
            examples = []
            for oid in obj_ids[:3]:
                obj = object_info.get(oid, {})
                title = obj.get("Title", oid)
                desc = obj.get("descripe", "")
                examples.append(f"{title}（{desc[:20]}...）")
            example_text = "，".join(examples)
            museum_info.append(f"- {museum}：{len(obj_ids)} 件藏品，示例包括：{example_text}")
        info = "\n".join(museum_info)
        return f"数据库中共包含 {len(index['museum_to_objects'])} 个博物馆。\n{info}"

    elif qtype == "每个博物馆藏品数":
        lines = []
        for museum, obj_ids in index["museum_to_objects"].items():
            examples = []
            for oid in obj_ids[:3]:
                obj = object_info.get(oid, {})
                title = obj.get("Title", oid)
                desc = obj.get("descripe", "")
                examples.append(f"{title}（{desc[:20]}...）")
            example_text = "，".join(examples)
            lines.append(f"{museum}：{len(obj_ids)} 件，示例：{example_text}")
        return "各博物馆藏品数量如下：\n" + "\n".join(lines)

    elif qtype == "艺术家数量":
        artist_info = []
        for artist, obj_ids in list(index['artist_to_objects'].items())[:3]:
            examples = []
            for oid in obj_ids[:3]:
                obj = object_info.get(oid, {})
                title = obj.get("Title", oid)
                desc = obj.get("descripe", "")
                examples.append(f"{title}（{desc[:20]}...）")
            example_text = "，".join(examples)
            artist_info.append(f"- {artist}：{len(obj_ids)} 件作品，示例：{example_text}")
        summary = f"数据库中共涉及 {len(index['artist_to_objects'])} 位艺术家。\n以下是其中三位的示例：\n" + "\n".join(artist_info)
        return summary

    elif qtype == "艺术家作品数":
        all_artists = list(index['artist_to_objects'].keys())
        corrected_name = get_best_match(entity, all_artists)
        if corrected_name:
            obj_ids = index['artist_to_objects'][corrected_name]
            examples = []
            for oid in obj_ids[:3]:
                obj = object_info.get(oid, {})
                title = obj.get("Title", oid)
                desc = obj.get("descripe", "")
                museum = None
                # 反查所属博物馆
                for m, objs in index['museum_to_objects'].items():
                    if oid in objs:
                        museum = m
                        break
                source = f"（藏于{museum}）" if museum else ""
                examples.append(f"{title}（{desc[:20]}...）{source}")
            example_text = "，".join(examples)
            return f"艺术家 {corrected_name} 的作品共计 {len(obj_ids)} 件。示例如下：{example_text}"
        else:
            return f"未找到艺术家 {entity} 的作品信息。"

    elif qtype == "历史时期数量":
        period_info = []
        for period, obj_ids in list(index['period_to_objects'].items())[:3]:
            examples = []
            for oid in obj_ids[:3]:
                obj = object_info.get(oid, {})
                title = obj.get("Title", oid)
                desc = obj.get("descripe", "")
                museum = None
                for m, objs in index['museum_to_objects'].items():
                    if oid in objs:
                        museum = m
                        break
                source = f"（藏于{museum}）" if museum else ""
                examples.append(f"{title}（{desc[:20]}...）{source}")
            example_text = "，".join(examples)
            period_info.append(f"- {period}：{len(obj_ids)} 件藏品，示例：{example_text}")
        return f"数据库中共涉及 {len(index['period_to_objects'])} 个历史时期。\n以下是部分时期的示例：\n" + "\n".join(period_info)

    elif qtype == "藏品总数":
        total = len(index['object_info'])
        examples = []
        for i, (oid, obj) in enumerate(object_info.items()):
            if i >= 3:
                break
            title = obj.get("Title", oid)
            desc = obj.get("descripe", "")
            museum = None
            for m, objs in index['museum_to_objects'].items():
                if oid in objs:
                    museum = m
                    break
            source = f"（藏于{museum}）" if museum else ""
            examples.append(f"{title}（{desc[:20]}...）{source}")
        example_text = "，".join(examples)
        return f"数据库共收录 {total} 件藏品。以下是部分示例：{example_text}"

    else:
        return "暂无法识别该问题类型。"

def rewrite_with_gpt(structured_answer, original_question):
    prompt = f"""
你是一个博物馆藏品问答系统，请根据用户提问和结构化答案，生成自然、详细、有逻辑层次的中文回答。

要求：
1. 首句直接明确回答用户的问题。
2. 若有列出示例，请补充解释每个示例（例如：说明作品、所属博物馆、历史时期等）。
3. 回答要简洁但不失信息量，避免机械列举。
4. 保持正式而友好的语气。有时可以保持有趣
5. 给用户提供情绪价值，让用户觉得提出的问题是有价值的

用户提问：{original_question}
结构化答案：{structured_answer}

请生成最终回答：
"""

    res = client.chat.completions.create(
        model="deepseek-r1",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.4
    )
    return res.choices[0].message.content.strip()

def answer_statistical_question(query):
    classification = classify_question_with_gpt(query)
 
    qtype = classification["type"]
    entity = classification["entity"]
    
    print(f"问题分类成功!为{qtype}类型问题")

    structured_answer = get_structured_answer(qtype, entity)
    print("结构化搜索完成")
    
    final_answer = rewrite_with_gpt(structured_answer, query)
    return final_answer


# query = "皮张元有多少件作品？"
# print(answer_statistical_question(query))
if __name__ == "__main__":
    query2 = "大都会博物馆中有多少藏品？"
    print(answer_statistical_question(query2))
