import pandas as pd
from collections import defaultdict

# 假设四个 DataFrame 已经加载

collection = pd.read_csv('triple/collection.csv',encoding = 'gbk')
relation1 = pd.read_csv('triple/relation1.csv',encoding = 'gbk')
relation2 = pd.read_csv('triple/relation2.csv',encoding = 'gbk')
relation3 = pd.read_csv('triple/relation3.csv',encoding = 'gbk')

# --------------------------
# 初始化结构化索引字典
# --------------------------
object_info = {}                   # Object ID -> full object info dict
museum_to_objects = defaultdict(set)  # Museum -> Object IDs
object_to_museum = {}             # Object ID -> Museum

artist_to_objects = defaultdict(set)  # Artist -> Object IDs
object_to_artist = {}             # Object ID -> Artist

period_to_objects = defaultdict(set)  # Period -> Object IDs
object_to_period = {}             # Object ID -> Period

# --------------------------
# 构建 Object Info 索引
# --------------------------
for _, row in collection.iterrows():
    obj_id = str(row["Object ID"]).strip()
    object_info[obj_id] = {
        "Title": row.get("Title", "").strip(),
        "descripe": row.get("descripe", "").strip(),
        "Object URL": row.get("Object URL", "").strip()
    }

# --------------------------
# 构建 Museum 索引
# --------------------------
for _, row in relation1.iterrows():
    obj_id = str(row["Object ID"]).strip()
    museum = str(row["Museum"]).strip()

    museum_to_objects[museum].add(obj_id)
    object_to_museum[obj_id] = museum

# --------------------------
# 构建 Period 索引
# --------------------------
for _, row in relation2.iterrows():
    obj_id = str(row["Object ID"]).strip()
    period = str(row["Period"]).strip()

    period_to_objects[period].add(obj_id)
    object_to_period[obj_id] = period

# --------------------------
# 构建 Artist 索引
# --------------------------
for _, row in relation3.iterrows():
    obj_id = str(row["Object ID"]).strip()
    artist = str(row["Artist"]).strip()

    artist_to_objects[artist].add(obj_id)
    object_to_artist[obj_id] = artist

# --------------------------
# 结构化索引字典集合
# --------------------------
structured_index = {
    "object_info": object_info,                          # Object ID -> Title, desc, URL
    "museum_to_objects": {k: list(v) for k, v in museum_to_objects.items()},
    "object_to_museum": object_to_museum,
    "artist_to_objects": {k: list(v) for k, v in artist_to_objects.items()},
    "object_to_artist": object_to_artist,
    "period_to_objects": {k: list(v) for k, v in period_to_objects.items()},
    "object_to_period": object_to_period
}

# --------------------------
# 保存为 JSON（可选）
# --------------------------
import json
with open("structured_index.json", "w", encoding="utf-8") as f:
    json.dump(structured_index, f, ensure_ascii=False, indent=2)
