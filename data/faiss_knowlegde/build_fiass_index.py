import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

# 确保目标目录存在，如果不存在则创建一个
if not os.path.exists("./drug_manuals"):
    os.makedirs("./drug_manuals")
    # 创建一个示例文本文件，以便代码可以运行
    with open("./drug_manuals/sample_drug.txt", "w", encoding="utf-8") as f:
        f.write("这是布洛芬缓释胶囊的说明书。主要成分为布洛芬。适用于缓解轻至中度疼痛，如头痛、关节痛、偏头痛、牙痛、肌肉痛、神经痛、痛经。也用于普通感冒或流行性感冒引起的发热。")
    print("ℹ️  示例目录和文件已创建。")


# 1. 加载说明书文本
loader = DirectoryLoader(
    "./drug_manuals/",
    glob="*.txt",             # 你可以换成 pdf/csv loader
    loader_cls=TextLoader,
    loader_kwargs={'encoding': 'utf-8'} # 明确指定编码，避免在不同系统上出现问题
)
documents = loader.load()
print(f"📄 已加载 {len(documents)} 份说明书")

# 2. 切分文本（保证 chunk 大小适合 embedding）
text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
docs = text_splitter.split_documents(documents)
print(f"✂️ 已切分成 {len(docs)} 个文本片段")

# 3. 加载本地 Embedding 模型
embedding_model = "sentence-transformers/all-MiniLM-L6-v2"  # 轻量级本地模型
embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model,
    model_kwargs={"device": "cpu"},  # 如果有 GPU 可改成 "cuda"
    encode_kwargs={"normalize_embeddings": True}
)

# 4. 向量化并存入 FAISS
vectorstore = FAISS.from_documents(docs, embeddings)

# 5. 保存到本地
save_path = "./faiss_store"
vectorstore.save_local(save_path)
print(f"✅ FAISS 索引已构建并保存到 {save_path}")