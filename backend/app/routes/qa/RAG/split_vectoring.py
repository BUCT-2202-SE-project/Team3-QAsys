import pandas as pd
from sentence_transformers import SentenceTransformer
import pickle

collection = pd.read_csv('triple/collection.csv',encoding = 'gbk')
relation1 = pd.read_csv('triple/relation1.csv',encoding = 'gbk')
relation2 = pd.read_csv('triple/relation2.csv',encoding = 'gbk')
relation3 = pd.read_csv('triple/relation3.csv',encoding = 'gbk')
# print(relation2.columns)
print("读取文件成功")

obj_map = collection.set_index("Object ID")[["Title","descripe","Object URL"]].to_dict(orient="index")

triples = []

# relation1: Museum -> Predicate -> Object
for _,row in relation1.iterrows():
    obj_id = row["Object ID"]
    obj_info = obj_map.get(obj_id,{})
    tail = obj_info.get("Title",obj_id)
    tail_desc = obj_info.get("descripe","")
    tail_url = obj_info.get("Object URL","")
    triple_text = f"{row['Museum']},{row['Predicate']}{tail}{tail_desc}{tail_url}"
    triples.append((row['Museum'],row['Predicate'],tail,triple_text))
    
# relation2: Object -> Predicate -> Period
for _,row in relation2.iterrows():
    obj_info = obj_map.get(row["Object ID"], {})
    head = obj_info.get("Title", row["Object ID"])
    head_desc = obj_info.get("descripe", "")
    head_url = obj_info.get("Object URL","")
    triple_text = f"{head} {row['Predicate']} {row['Period']}. {head_desc}{head_url}"
    triples.append((head, row['Predicate'], row['Period'], triple_text))

# relation3: Object -> Predicate -> Artist
for _, row in relation3.iterrows():
    obj_info = obj_map.get(row["Object ID"], {})
    head = obj_info.get("Title", row["Object ID"])
    head_desc = obj_info.get("descripe", "")
    head_url = obj_info.get("Object URL","")
    triple_text = f"{head} {row['Predicate']} {row['Artist']}. {head_desc}{head_url}"
    triples.append((head, row['Predicate'], row['Artist'], triple_text))
    
print("三元组构建成功")

model = SentenceTransformer('all-MiniLM-L6-v2')
texts = [t[3] for t in triples]
embeddings = model.encode(texts,show_progress_bar=True)

print("成功向量化")
with open("triple_museum.pkl", "wb") as f:
    pickle.dump((embeddings, triples), f)
    
print("保存成功")