# IKMS Multi-Agent RAG

A powerful document question-answering application powered by **LangGraph**, **Pinecone**, and **OpenAI**. This application uses a multi-agent Retrieval-Augmented Generation (RAG) pipeline to analyze uploaded PDFs and provide highly accurate answers with verifiable context and query planning.

## Features

- **Multi-Agent Pipeline**: Answers are generated through a linear graph of specialized LLM agents:
  1. **Planning Agent**: Breaks down complex questions into targeted sub-queries.
  2. **Retrieval Agent**: Searches the Pinecone vector database for relevant context.
  3. **Summarization Agent**: Drafts an initial answer based on retrieved documents.
  4. **Verification Agent**: Fact-checks the draft and ensures it directly answers the user's question without hallucinations.
- **PDF Upload & Indexing**: Easily upload PDF documents. The application uses `PyMuPDF4LLM` to extract text, chunks it, embeds it via OpenAI (`text-embedding-ada-002`), and indexes it into Pinecone.
- **Query Planning Toggle**: A UI toggle allows users to easily skip the Planning agent for faster, straightforward queries.
- **Dual Frontends**:
  - A modern **Next.js** application with Shadcn UI components.
  - A lightweight **Static HTML/Vanilla JS** interface served directly by the backend.

## Tech Stack

- **Backend**: FastAPI, Uvicorn, Python 3.12
- **AI/Orchestration**: LangChain, LangGraph, OpenAI (GPT-3.5-Turbo / GPT-4o-mini)
- **Vector Database**: Pinecone
- **Frontend**: Next.js, React, Tailwind CSS, Vanilla HTML/CSS/JS

## Setup & Run Locally

### 1. Environment Variables
Create a `.env` file in the root directory for the backend API keys:
```env
OPENAI_API_KEY="your-openai-api-key"
PINECONE_API_KEY="your-pinecone-api-key"
PINECONE_INDEX_NAME="knowledge-index"
OPENAI_MODEL_NAME="gpt-4o-mini"
OPENAI_EMBEDDING_MODEL_NAME="text-embedding-ada-002"
```

Create a `.env.local` file in the `frontend` directory:
```env
NEXT_PUBLIC_API_URL="http://127.0.0.1:8000"
```

### 2. Backend Setup
Install uv (or use standard pip):
```bash
pip install uv
uv sync
```

Run the FastAPI Server:
```bash
uv run uvicorn src.app.api:app --reload --host 127.0.0.1 --port 8000
```
*The static vanilla HTML frontend will be available at [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html).*

### 3. Frontend Setup (Next.js)
In a new terminal, navigate to the `frontend` directory:
```bash
cd frontend
npm install
npm run dev
```
*The Next.js frontend will be available at [http://localhost:3000](http://localhost:3000).*

## Deployment

The application is configured to run serverless Python functions on **Vercel**. 
Ensure you set the `.env` variables in your Vercel Project Settings when deploying.