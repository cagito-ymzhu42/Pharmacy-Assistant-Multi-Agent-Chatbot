import os
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.graphs import Neo4jGraph

# --- LLM 初始化 ---
llm = ChatOpenAI(
    model="deepseek-chat",
    openai_api_base="https://api.deepseek.com",
    openai_api_key="sk-d372c135e16a4a3ea52ee95cb9d7e29f", # 替换为您的密钥或从环境变量读取
    temperature=0
)

# --- 嵌入模型和向量数据库初始化 ---
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(model_name=embedding_model_name)

vectorstore = None
try:
    vectorstore_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'faiss_knowlegde', 'faiss_store')
    vectorstore = FAISS.load_local(vectorstore_path, embeddings, allow_dangerous_deserialization=True)
    print("✅ 向量数据库 (FAISS) 初始化成功。")
except Exception as e:
    print(f"❌ 初始化向量化知识库失败: {e}")
    print("   请确保FAISS索引存在于 'data/faiss_knowlegde/faiss_store' 路径下。")


# --- 知识图谱初始化 ---
graph = None
try:
    graph = Neo4jGraph(
        url="neo4j://127.0.0.1:7687", # 替换为您的Neo4j地址
        username="neo4j",
        password="medicine4demo" # 替换为您的Neo4j密码
    )
    # 检查连接
    graph.query("RETURN 1")
    print("✅ 知识图谱 (Neo4j) 初始化成功。")
except Exception as e:
    print(f"❌ 初始化知识图谱失败: {e}")
    print("   请确保Neo4j服务正在运行，并且URL、用户名和密码正确。")

# --- 检查所有模块是否加载成功 ---
def check_modules_loaded():
    if not vectorstore or not graph:
        print("\n错误：核心模块（向量数据库或知识图谱）未能加载，程序无法继续。")
        return False
    return True