from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection
import pickle

with open("triple_museum.pkl", "rb") as f:
    embeddings, triples = pickle.load(f)
    
    
connections.connect(
    host="127.0.0.1",  # 连接服务端地址，
    port=19530,        # 连接端口，milvus默认监听19530
    alias='default',   # 连接的别名，如果不设置，默认为default，
    db_name='default'  # 连接的数据库，默认是default
)

res = connections.has_connection("default")
print(res)

collection_name = "museum_kg"
collection = Collection(name=collection_name)

# 删除集合
collection.drop()
print("deleted")
# 字段定义
fields = [
    FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
    FieldSchema(name="head", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="relation", dtype=DataType.VARCHAR, max_length=500),
    FieldSchema(name="tail", dtype=DataType.VARCHAR, max_length=1000),
    FieldSchema(name="triple_text", dtype=DataType.VARCHAR, max_length=5000),
    FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=384)
]

#表结构
schema = CollectionSchema(fields, description="Museum object triplets")
collection = Collection("museum_kg", schema)


# 构造插入数据
heads = [t[0] for t in triples]
relations = [t[1] for t in triples]
tails = [t[2] for t in triples]
texts = [t[3] for t in triples]

# 分段，不然太大了装不下
for i in range(0,len(triples),500):
    heads_split = heads[i:i+500]
    relations_split = relations[i:i+500]
    tails_split = tails[i:i+500]
    texts_split = texts[i:i+500]
    embeddings_split = embeddings[i:i+500]
    
    insert_data = [heads_split, relations_split, tails_split, texts_split, list(embeddings_split)]
    collection.insert(insert_data)
collection.flush()


collection.create_index(
    field_name="embedding",
    index_params={"index_type": "IVF_FLAT", "metric_type": "L2", "params": {"nlist": 128}}
)
# collection.load()


print("数据插入成功")