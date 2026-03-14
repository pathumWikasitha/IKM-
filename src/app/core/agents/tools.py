"""Tools available to agents in the multi-agent RAG system."""

from langchain_core.tools import tool

from app.core.retrieval.vector_store import retrieve
from app.core.retrieval.serialization import serialize_chunks


@tool
def retrieval_tool(query: str):
    """Search the vector database for relevant document chunks.

    This tool retrieves the top 4 most relevant chunks from the Pinecone
    vector store based on the query. The chunks are formatted with page
    numbers and indices for easy reference.

    Args:
        query: The search query string to find relevant document chunks.

    Returns:
        Tuple of (serialized_content, artifact) where:
        - serialized_content: A formatted string containing the retrieved chunks
          with metadata. Format: "Chunk 1 (page=X): ...\n\nChunk 2 (page=Y): ..."
        - artifact: List of Document objects with full metadata for reference
    """
    # Retrieve documents from vector store
    docs = retrieve(query, k=4)

    # Serialize chunks into formatted string (content)
    context = serialize_chunks(docs)

    # Return just the formatted content string instead of a tuple.
    # This prevents the LangGraph tools node from crashing when trying to parse the output.
    return context
