"""Live workflow resources, initialized when the server loads the workflow."""
import os
from pathlib import Path
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_community.vectorstores import FAISS
from langchain_community.graphs import Neo4jGraph

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

if not os.getenv("OPENAI_API_KEY") or not os.getenv("NEO4J_PASSWORD"):
    raise RuntimeError("Set OPENAI_API_KEY and NEO4J_PASSWORD in .env for live mode.")

llm = ChatOpenAI(
    model=os.getenv("OPENAI_MODEL", "deepseek-chat"),
    base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com"),
    api_key=os.environ["OPENAI_API_KEY"],
    temperature=0,
)
embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
embeddings = HuggingFaceEmbeddings(
    model_name=embedding_model_name,
    model_kwargs={"device": "cpu"},
    encode_kwargs={"normalize_embeddings": True},
)
vectorstore = FAISS.load_local(
    str(ROOT / "data" / "faiss_knowlegde" / "faiss_store"),
    embeddings,
    allow_dangerous_deserialization=True,
)
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI", "neo4j://127.0.0.1:7687"),
    username=os.getenv("NEO4J_USER", "neo4j"),
    password=os.environ["NEO4J_PASSWORD"],
)
graph.query("RETURN 1")


def check_modules_loaded():
    return vectorstore is not None and graph is not None
