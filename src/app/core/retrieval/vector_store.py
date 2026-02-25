"""Vector store wrapper for Pinecone integration with LangChain."""

from pathlib import Path
from functools import lru_cache
from typing import List, Optional

from pinecone import Pinecone
from langchain_core.documents import Document
from langchain_pinecone import PineconeVectorStore
from langchain_openai import OpenAIEmbeddings
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter


from core.config import get_settings


@lru_cache(maxsize=1)
def _get_vector_store() -> PineconeVectorStore:
    """Create a PineconeVectorStore instance configured from settings."""
    settings = get_settings()

    pc = Pinecone(api_key=settings.pinecone_api_key)
    
    # Try to get the index, create if it doesn't exist
    try:
        index = pc.Index(settings.pinecone_index_name)
    except Exception as e:
        # Index doesn't exist, create it
        print(f"Index {settings.pinecone_index_name} not found. Creating...")
        pc.create_index(
            name=settings.pinecone_index_name,
            dimension=1536,  # text-embedding-3-small produces 1536-dimensional embeddings
            metric="cosine",
            spec={"serverless": {"cloud": "aws", "region": "us-east-1"}}
        )
        index = pc.Index(settings.pinecone_index_name)

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model_name,
        api_key=settings.openai_api_key,
    )

    return PineconeVectorStore(
        index=index,
        embedding=embeddings,
    )

def get_retriever(k: Optional[int] = None):
    """Get a Pinecone retriever instance.

    Args:
        k: Number of documents to retrieve (defaults to config value).

    Returns:
        PineconeVectorStore instance configured as a retriever.
    """
    settings = get_settings()
    if k is None:
        k = settings.retrieval_k

    vector_store = _get_vector_store()
    return vector_store.as_retriever(search_kwargs={"k": k})


def retrieve(query: str, k: Optional[int] = None) -> List[Document]:
    """Retrieve documents from Pinecone for a given query.

    Args:
        query: Search query string.
        k: Number of documents to retrieve (defaults to config value).

    Returns:
        List of Document objects with metadata (including page numbers).
    """
    retriever = get_retriever(k=k)
    return retriever.invoke(query)

def index_documents(docs: list) -> int:
    """Index a list of Document objects into the Pinecone vector store.

    Args:
        docs: Documents to embed and upsert into the vector index.

    Returns:
        The number of documents indexed.
    """
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    texts = text_splitter.split_documents(docs)

    vector_store = _get_vector_store()
    vector_store.add_documents(texts)
    return len(texts)