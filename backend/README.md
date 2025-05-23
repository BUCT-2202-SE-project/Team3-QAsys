# MuseLink-千鉴 知识问答子系统 - 后端

## 项目简介

本项目是海外藏中国文物知识管理与服务平台的知识问答子系统后端部分，基于Python和Flask框架开发，通过接入大语言模型API实现对文物知识的智能问答功能。系统采用RAG技术，结合知识图谱和向量数据库，提供高质量文物知识问答服务。

## 环境要求

- Python 3.8+
- pip (Python包管理工具)
- MySQL 5.7+ (用于存储对话历史和用户信息)
- Neo4j (用于存储知识图谱)
- Milvus 2.0+ (向量数据库，用于语义搜索)

## 安装依赖

1. 克隆仓库到本地

```bash
git clone https://github.com/BUCT-2202-SE-project/Team3-QAsys.git
cd Team3-QAsys/backend
```

2. 创建并激活虚拟环境(可选但推荐)

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/MacOS
python3 -m venv venv
source venv/bin/activate
```

3. 安装依赖包

```bash
pip install -r requirements.txt
```

主要依赖包括：
- Flask==2.2.3
- Flask-Cors==3.0.10
- Flask-SQLAlchemy==3.0.3
- PyMySQL==1.0.3
- requests==2.28.2
- python-dotenv==1.0.0
- openai==1.3.0
- sentence-transformers==2.2.2
- pymilvus==2.2.8
- py2neo==2021.2.3
- pandas==1.5.3

## 配置说明

1. 创建 `.env` 文件，配置以下环境变量：

```
# 服务器配置
FLASK_APP=app.py
FLASK_ENV=development
PORT=5000

# 数据库配置
DB_USERNAME=your_db_username
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=3306
DB_NAME=qasys

# Neo4j配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=password

# Milvus配置
MILVUS_HOST=localhost
MILVUS_PORT=19530

# 大模型API配置
API_KEY=your_api_key
```

## 向量数据库配置

项目使用Milvus作为向量数据库，用于存储和检索文物知识的语义表示。

1. 安装Milvus (使用Docker)

```bash
# 拉取Milvus镜像
docker pull milvusdb/milvus:v2.2.8

# 启动Milvus服务
docker run -d --name milvus_cpu -p 19530:19530 -p 19121:19121 -v /your/data/path:/var/lib/milvus milvusdb/milvus:v2.2.8
```

2. 初始化向量数据库

```bash
# 在backend/app/routes/qa/RAG目录下执行
python split_vectoring.py
python db_insert.py
```
split_vectoring.py 将数据进行向量化处理，保存成一个pkl文件
db_insert.py 这将处理三元组数据，使用SentenceTransformer模型生成向量表示，并存储到Milvus中。



## 结构化存储数据，用于统计类问题的回答
运行structure.py 文件，可以得到一个有着所有三元组对应的json文件，用于统计类问题直接读取


## 运行方法

1. 启动服务器

```bash
# 开发环境
flask run

# 或指定主机和端口
flask run --host=0.0.0.0 --port=5000

# 生产环境
gunicorn -w 4 -b 0.0.0.0:5000 app:app
```

2. 服务器默认运行在 http://localhost:5000

## 目录结构

```
backend/
├── app/                        # 应用主目录
│   ├── __init__.py             # 应用初始化
│   ├── graph/                  # 知识图谱模块
│   │   └── neo4j_conn.py       # Neo4j连接
│   ├── routes/                 # 路由模块
│   │   ├── __init__.py
│   │   ├── auth/               # 认证相关
│   │   │   └── routes.py       # 登录、注册等
│   │   └── qa/                 # 问答相关
│   │       ├── routes.py       # 问答接口
│   │       └── RAG/            # 检索增强生成
│   │           ├── RAG.py      # RAG核心实现
│   │           ├── db_insert.py        # 向量数据库插入
│   │           ├── split_vectoring.py  # 文本分割与向量化
│   │           ├── structure.py        # 结构化数据处理
│   │           └── structured_index.json # 结构化索引
│   └── utils/                  # 工具函数
│       └── helpers.py          # 辅助函数
├── database/                   # 数据库相关
│   └── mysql_client.py         # MySQL连接
├── app.py                      # 应用入口
├── config.py                   # 配置文件
├── QAsystem.postman_collection.json # API测试集合
└── requirements.txt            # 依赖清单
```

## API接口说明

系统提供以下主要API接口：

### 认证接口
- `/auth/register` - 用户注册
- `/auth/login` - 用户登录
- `/auth/getUserInfo` - 获取用户信息

### 问答接口
- `/qa/chat` - 问答核心接口，支持RAG和普通问答模式
- `/qa/getHistoryList` - 获取对话历史列表
- `/qa/getHistoryInfo` - 获取指定对话的详细内容
- `/qa/create` - 创建新对话
- `/qa/rename` - 重命名对话
- `/qa/delete` - 删除对话

## RAG实现细节

系统使用检索增强生成(RAG)技术提升问答质量：

1. **知识库构建**：
   - 使用SentenceTransformer模型将文物知识转为向量表示
   - 将向量存储在Milvus数据库中，实现语义搜索
   - 维护文物与博物馆、作者、年代等关系的三元组知识

2. **知识检索**：
   - 对用户问题进行向量化
   - 从Milvus中检索相似度最高的知识片段
   - 对于特定类型问题，直接查询Neo4j知识图谱

3. **问答生成**：
   - 结合检索到的知识，构建提示词发送给大语言模型
   - 在对话历史的基础上，生成连贯且专业的回答


