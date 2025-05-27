import requests, json, time, pymysql
from flask import Blueprint, request, current_app, Response, stream_with_context, jsonify
from app.graph import neo4j_conn
from app.utils import extract_entity_attributes, error_response, save_qa_record,get_history_context,build_chat_context,enhance_query_with_llm,extract_limit_from_attr
from database.mysql_client import get_db
from app.routes.auth.routes import token_required
from app.routes.qa.RAG.RAG import search_similar_knowledge, build_prompt, classify_question_with_gpt, answer_statistical_question
from openai import OpenAI
import re

qa_bp = Blueprint('qa', __name__)

@qa_bp.route('/getHistoryList', methods=['GET'])
@token_required
def getHistoryList():
    user_id = request.args.get('userId')

    # 参数校验
    if not user_id or not user_id.isdigit():
        return error_response(message="用户ID无效", http_status=400)
    
    conn = get_db()
    try:
        user_id = int(user_id)

        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT history_id, history_name FROM history_list WHERE user_id = %s order by create_time desc" ,
                (user_id,)
            )
            rows = cursor.fetchall()

            data = [
                {
                    "historyId": row["history_id"], 
                    "historyName": row["history_name"] 
                }
                for _, row in enumerate(rows)
            ]

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": data
        })

    except Exception as e:
        print(f"[ERROR] {e}")
        return error_response(message="服务器内部错误", http_status=500)
    finally:
        conn.close()

@qa_bp.route('/getHistoryInfo', methods=['GET'])
@token_required
def getHistoryInfo():
    history_id = request.args.get('historyId', type=int)

    if not history_id:
        return error_response(message="缺少参数：historyId", http_status=400)

    conn = get_db()
    try:
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            cursor.execute(
                "SELECT question, answer, reference "
                "FROM history WHERE history_id = %s "
                "ORDER BY create_time ASC", (history_id,)
            )

            results = cursor.fetchall()

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": results
        })

    except Exception as e:
        print("查询异常：", e)
        return error_response(message="服务器内部错误", http_status=500)

@qa_bp.route('/create', methods=['POST'])
@token_required
def create():
    try:
        # data = request.get_json()
        # user_id = data.get("userId")
        user_id = request.form.get("userId")
        history_name = request.form.get("historyName")
        if not user_id:
            return error_response(message="userId不能为空")

        conn = get_db()
        print("userId:", user_id) 
        print("数据库连接")
        with conn.cursor() as cursor:
            # 插入新记录
            cursor.execute(
                "INSERT INTO history_list (user_id, history_name) "
                "VALUES ( %s, %s)",
                (user_id, history_name)
            )
            conn.commit()

            new_history_id = cursor.lastrowid

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": {
                "historyId": new_history_id
            }
        })
    except Exception as e:
        return error_response(message=f'数据库操作失败：{str(e)}')
    
@qa_bp.route('/rename', methods=['PATCH'])
@token_required
def rename():
    try:
        
        history_id = request.form.get('historyId')
        new_name = request.form.get('newName')        
        
        print(history_id, new_name)
        if not history_id or not new_name:
            return error_response(message="historyId 和 newName 均不能为空")

        conn = get_db()
        with conn.cursor() as cursor:
            # 更新记录名
            cursor.execute(
                "UPDATE history_list SET history_name = %s WHERE history_id = %s",
                (new_name, history_id)
            )
            conn.commit()

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": None
        })

    except Exception as e:
        return error_response(message=f"数据库操作失败：{str(e)}")
    
@qa_bp.route('/delete', methods=['DELETE'])
@token_required
def delete_history():
    try:
        history_id = request.args.get('historyId')
        print(history_id)
        if not history_id:
            return error_response(message="historyId 参数不能为空")

        conn = get_db()
        with conn.cursor() as cursor:
            # 删除对应的历史记录
            cursor.execute(
                "DELETE FROM history_list WHERE history_id = %s",
                (history_id,)
            )
            conn.commit()

        return jsonify({
            "code": 0,
            "message": "操作成功",
            "data": None
        })

    except Exception as e:
        return error_response(message=f"数据库操作失败：{str(e)}")


@qa_bp.route('/chat', methods=['POST'])
@token_required
def chat():
    start_time = time.time()
    thoughts = []

    # 记录思考的辅助函数
    def thinking(message):
        print(f"[思考] {message}")  # 仍然输出到控制台
        thoughts.append(message)

    question = request.form.get('question')
    history_id = request.args.get('historyId') 
    rag_flag = request.args.get('rag')
    rag = (rag_flag or request.args.get('rag', 'true')).lower() == 'true'

    thinking(f"问题: {question}")
    thinking(f"rag_flag: {rag_flag}, 最终 rag: {rag}")
    
    if not question:
        def error_stream():
            yield "错误：问题不能为空"
        return Response(error_stream(), mimetype='text/plain')

    history_context = get_history_context(history_id, max_count=5) if history_id else []
    thinking(f"获取历史上下文: {len(history_context)} 条记录")
    chat_context = build_chat_context(history_context, question)

    # 实体属性提取预处理
    result = extract_entity_attributes(question)
    thinking(f"实体属性提取结果: {result}")
    
    entity_found = False
    if result and result.get("entity") and result.get("attributes"):
        entity = result['entity']
        attributes = result['attributes']
        thinking(f"识别实体: {entity}, 属性: {attributes}")
        entity_found = True
        

        # 提前构建 Cypher 语句
        cyphers = []
        db_query_start = time.time()
        for attr in attributes:
                

            
            
            if attr in ['描述', '特点']:
                attr = '特点'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}'
                    RETURN a.descripe AS answer
                """
            elif attr in ['作者', '年代']:
                cypher = f"""
                    MATCH (a)-[r:{attr}]->(b)
                    WHERE a.title = '{entity}'
                    RETURN 
                    CASE 
                        WHEN type(r) = '作者' THEN b.name
                        WHEN type(r) = '年代' THEN b.period
                    END AS answer
                """
            elif attr in ['收藏地', '存放博物馆', '存放地']:
                cypher = f"""
                    MATCH (museum)-[:包含]->(artifact)
                    WHERE artifact.title = '{entity}'
                    RETURN museum.name AS answer
                """
            elif attr in ['url', 'URL']:
                attr = 'url'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}'
                    RETURN a.url AS answer
                """
            elif re.match(r'^(\d+|[一二三四五六七八九十百千万几一些若干多])+(件|个)?(文物|藏品)$', attr):
                num = extract_limit_from_attr(attr)
                cypher = f"""
                    MATCH (museum:Museum)-[:包含]->(artifact)
                    WHERE museum.name = '{entity}'
                    RETURN artifact.title AS answer
                    LIMIT {num}
                """
            else:
                cypher = ""

            cyphers.append((attr, cypher.strip()))
            # thinking(f"构建Cypher - {attr}: {cypher}")

    @stream_with_context
    def generate():
        # 先输出所有思考过程，确保完整输出
        thoughts_text = "\n".join(thoughts)
        yield f"<think>{thoughts_text}</think>\n"
        thoughts.clear()
            
        def fallback_with_llm():
            """仅使用 LLM 简要回答"""
            try:
                thinking("正在调用大模型实现")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()
                
                
                # 构建包含历史对话的消息
                messages = []
                if chat_context:
                    messages.append({"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。请记住用户的对话历史并保持连贯性。依据给出的参考整合成完整的语句之后,使用中文进行完整回答，可以保持幽默诙谐"})
                    for msg in chat_context:
                        messages.append({
                            "role": "user" if msg["role"]=="user" else "assistant", 
                            "content": msg["content"]
                        })
                else:
                    messages.append({"role": "user", "content": "请简要的回复：" + question})
                
                client = OpenAI(
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    api_key = ""
                )
                
                # 使用客户端调用API
                response = client.chat.completions.create(
                    model="deepseek-r1",
                    messages=messages if chat_context else [{"role": "user", "content": "请简要的回复：" + question}],
                    temperature=0.5,
                    stream=True
                )

                reference = "回答由AI生成，考虑了对话历史" if chat_context and history_context else "回答由AI生成，请注意甄别"
                accumulated_answer = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_answer += content
                        yield content
                        time.sleep(0.01)
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, accumulated_answer, reference)
            except requests.RequestException as e:
                error_msg = f"API请求失败: {str(e)}"
                yield error_msg
                yield f"\n<!-- REFERENCE_DATA:请求失败 -->"
                save_qa_record(history_id, question, error_msg, "API请求异常")

        def fallback_with_rag():
            """RAG增强流程"""
            try:
                thinking("RAG增强")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()
                classification = classify_question_with_gpt(question)
                qtype = classification["type"]
                
                if qtype != "未知":
                    thinking(f"处理统计类问题：{qtype}")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()                    
                    answer = answer_statistical_question(question)
                    thinking(f"结构化搜索完成")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()                       
                    yield answer
                    yield f"\n<!-- REFERENCE_DATA:统计类问题 ({qtype}) -->"
                    save_qa_record(history_id, question, answer, f"统计类问题 ({qtype})")
                    return


                thinking("处理知识库检索问题")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()   
                # 考虑历史上下文进行知识库检索
                enriched_query = question
                if chat_context:
                    thinking("使用大模型增强查询...")
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()   
                    enriched_query = enhance_query_with_llm(question, chat_context)
                    thinking(f"增强后的查询: {enriched_query}")  
                    thoughts_text = "\n".join(thoughts)
                    yield f"<think>{thoughts_text}</think>\n"
                    thoughts.clear()   
                        
                knowledge = search_similar_knowledge(enriched_query)
                thinking(f"检索到 {len(knowledge)} 条相关知识")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()                   
                prompt = build_prompt(knowledge, question, chat_context if chat_context else None)
                
                client = OpenAI(
                    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
                    api_key="",
                )
                
                thinking("调用LLM API")
                thoughts_text = "\n".join(thoughts)
                yield f"<think>{thoughts_text}</think>\n"
                thoughts.clear()   
                
                response = client.chat.completions.create(
                    model="deepseek-r1",
                    messages=[
                        {"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。依据给出的参考整合成完整的语句之后,使用中文进行完整回答。如果没有找到参考，就使用大模型自己回答"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.5,
                    stream=True
                )

                # 构建消息，包含历史对话
                messages = [
                    {"role": "system", "content": "你是MuseLink-千鉴。你的核心职责是连接古今、解码文明，为用户提供专业而富有诗意的文物知识与解读。依据给出的参考和对话历史，使用中文进行完整回答。保持回答的连贯性。"}
                ]
                
                # 添加历史消息
                if chat_context:
                    for msg in chat_context:
                        messages.append({
                            "role": "user" if msg["role"]=="user" else "assistant",
                            "content": msg["content"]
                        })
                
                # 添加当前提示
                messages.append({"role": "user", "content": prompt})

                accumulated_answer = ""
                for chunk in response:
                    if chunk.choices[0].delta.content:
                        content = chunk.choices[0].delta.content
                        accumulated_answer += content
                        yield content
                        time.sleep(0.01)

                reference = "向量检索：" + json.dumps(knowledge, ensure_ascii=False)
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, accumulated_answer, reference)

            except Exception as e:
                print(f"RAG fallback 失败: {e}")
                yield from fallback_with_llm()

        # ------------------ 主逻辑：处理回答 ------------------ #
        if not entity_found:
            thinking("未识别出有效实体属性")
            thoughts_text = "\n".join(thoughts)
            yield f"<think>{thoughts_text}</think>\n"
            thoughts.clear()   
            yield from (fallback_with_rag() if rag else fallback_with_llm())
            return

        answers_map = {}
        records_found = True
        for attr, cypher in cyphers:
            if not records_found:
                break
            try:
                records = neo4j_conn.query(cypher)
                print(cypher)
                if records:
                    all_answers = [r['answer'] for r in records if r.get('answer')]
                    if all_answers:
                        answers_map[attr] = all_answers if len(all_answers) > 1 else all_answers[0]
                    else:
                        records_found = False
                else:
                    records_found = False
            except Exception as e:
                records_found = False
                answers_map[attr] = f"{attr}查询失败：{str(e)}"

        db_query_end = time.time()
        print(f"数据库查询耗时: {db_query_end - db_query_start:.4f} 秒")

        if result.get("question_type") == "yes_no":
            if len(attributes) != 1:
                yield "无法处理多个是否判断。"
                return

            attr = attributes[0]
            match_found = False
            reference = ""
            attr_type = None  # 用于标记当前属性类型

            # 判断是否为描述性关键词（如“瓷”）
            if re.search(r'[瓷陶玉铜金银青铜桶盆凳碗椅桌]', attr):
                attr_type = '描述'
                cypher = f"""
                    MATCH (a)
                    WHERE a.title = '{entity}' AND a.descripe CONTAINS '{attr}'
                    RETURN a.descripe AS answer
                """
                reference = f"[描述匹配] {cypher}"
            # 判断是否为作者（中文人名或明确提出“李白”“张大千”等）
            elif re.match(r'^[\u4e00-\u9fa5]{2,4}$', attr):
                attr_type = '作者'
                cypher = f"""
                    MATCH (a)-[:作者]->(b)
                    WHERE a.title = '{entity}' AND b.name = '{attr}'
                    RETURN b.name AS answer
                """
                reference = f"[作者匹配] {cypher}"
            # 判断是否为年代（年份或朝代）
            elif re.match(r'^(公元前)?\d{1,4}年$|^\d{4}$|.*朝$', attr):
                attr_type = '年代'
                cypher = f"""
                    MATCH (a)-[:年代]->(b)
                    WHERE a.title = '{entity}' AND b.period = '{attr}'
                    RETURN b.period AS answer
                """
                reference = f"[年代匹配] {cypher}"
            # 判断是否为收藏地
            else:
                attr_type = '收藏地'
                cypher = f"""
                    MATCH (museum)-[:包含]->(artifact)
                    WHERE artifact.title = '{entity}' AND museum.name = '{attr}'
                    RETURN museum.name AS answer
                """
                reference = f"[收藏地匹配] {cypher}"

            try:
                print("[YES_NO] Cypher:", cypher)
                records = neo4j_conn.query(cypher.strip())
                if records:
                    for record in records:
                        if any(v for v in record.values() if attr in str(v)):
                            match_found = True
                            break

                if attr_type in ['作者', '年代']:
                    if match_found:
                        final_answer = f"是的，{entity}是{attr}所作。"
                    else:
                        final_answer = f"不是，{entity}不是{attr}所作。"
                elif attr_type == '收藏地':
                    if match_found:
                        final_answer = f"是的，{entity}收藏于{attr}。"
                    else:
                        final_answer = f"不是，{entity}不收藏于{attr}。"
                else:
                    # 描述和年代默认普通陈述
                    if match_found:
                        final_answer = f"是的，{entity}是{attr}。"
                    else:
                        final_answer = f"不是，{entity}不是{attr}。"

                yield final_answer
                yield f"\n<!-- REFERENCE_DATA:{reference} -->"
                save_qa_record(history_id, question, final_answer, reference)
                return
            except Exception as e:
                yield f"{attr}的判断查询失败：{str(e)}"
                return
            
   

        if records_found:
            response_segments = []
            for attr, answer in answers_map.items():
                if isinstance(answer, list):  # 多条记录（如多个文物）
                    response_segments.append(f"{attr}包括：{'、'.join(answer)}")
                else:  # 单条记录
                    response_segments.append(f"{attr}是{answer}")
            final_answer = f"{entity}的" + "，".join(response_segments) + "。"

            reference = "从Neo4j数据库获取:\n" + "\n".join(c for _, c in cyphers)
            yield final_answer
            yield f"\n<!-- REFERENCE_DATA:{reference} -->"
            save_qa_record(history_id, question, final_answer, reference)
        else:
            yield from (fallback_with_rag() if rag else fallback_with_llm())

        end_time = time.time()
        print(f"总耗时: {end_time - start_time:.2f}s")

    return Response(generate(), mimetype='text/plain')
