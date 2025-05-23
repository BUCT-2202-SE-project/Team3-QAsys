import re

def extract_entity_attribute(question):
    pattern1 = re.compile(r'(.*)的(.*)是(什么|啥|怎么回事)[？?]')
    pattern2 = re.compile(r'(.*)是什么[？?]')
    
    m1 = pattern1.match(question)
    if m1:
        entity = m1.group(1).strip()
        attribute = m1.group(2).strip()
        return entity, attribute
    
    m2 = pattern2.match(question)
    if m2:
        entity = m2.group(1).strip()
        attribute = '介绍'  # 或者你自己定义默认属性
        return entity, attribute
    
    return None, None

# 测试
print(extract_entity_attribute("故宫的建造时间是什么？"))  # ('故宫', '建造时间')
print(extract_entity_attribute("故宫是什么？"))          # ('故宫', '介绍')
