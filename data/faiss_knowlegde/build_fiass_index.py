import os
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import DirectoryLoader, TextLoader

from pathlib import Path
ROOT = Path(__file__).resolve().parent

# 1. 加载说明书文本
loader = DirectoryLoader(
    str(ROOT / "drug_manuals"),
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
save_path = str(ROOT / "faiss_store")
vectorstore.save_local(save_path)
print(f"✅ FAISS 索引已构建并保存到 {save_path}")