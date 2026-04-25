"""FastAPI server for Energy Docs RAG Pipeline"""
import os
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pydantic import BaseModel

from energy_docs_chat.src.chat_with_doc.retrieval import RetrievalPipeline
from energy_docs_chat.logger.custom_logger import logger


# Pydantic request/response models
class ChatRequest(BaseModel):
    """User chat request"""
    question: str
    session_id: str = "default"


class ChatResponse(BaseModel):
    """RAG pipeline response"""
    question: str
    answer: str
    session_id: str
    timestamp: str


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    message: str
    timestamp: str


# Global pipeline instance
pipeline = None
rag_chain = None


@asynccontextmanager
async def lifespan(_app: FastAPI):
    """Initialize pipeline on first request (lazy loading)"""
    global pipeline, rag_chain
    yield
    # Optional: cleanup on shutdown
    if rag_chain is not None:
        logger.info("Shutting down RAG pipeline")


# Initialize FastAPI app
app = FastAPI(
    title="Energy Docs RAG API",
    description="Retrieval-Augmented Generation for Energy Documents",
    version="1.0.0",
    lifespan=lifespan
)

# Mount static files (CSS, JS, etc.)
static_dir = Path(__file__).parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=static_dir), name="static")


# ============================================================================
# Health Check
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint"""
    if rag_chain is None:
        raise HTTPException(status_code=503, detail="RAG pipeline not initialized")
    return HealthResponse(
        status="healthy",
        message="RAG pipeline is ready",
        timestamp=datetime.now().isoformat()
    )


# ============================================================================
# Chat API Endpoint
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Query the RAG pipeline.

    Example:
        POST /chat
        {"question": "What is the Standard Frequency Range?", "session_id": "user_123"}
    """
    global pipeline, rag_chain

    try:
        # Lazy load pipeline on first request
        if rag_chain is None:
            logger.info("Lazy loading RAG pipeline on first request...")
            pipeline = RetrievalPipeline()
            rag_chain = pipeline.build_chain()
            logger.info("RAG pipeline loaded successfully")

        logger.info(f"Chat: {request.question[:100]}... (session: {request.session_id})")

        answer = rag_chain.invoke(
            {"question": request.question},
            config={"configurable": {"session_id": request.session_id}}
        )

        return ChatResponse(
            question=request.question,
            answer=answer,
            session_id=request.session_id,
            timestamp=datetime.now().isoformat()
        )

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# Web UI
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def web_ui():
    """Interactive chat interface"""
    index_path = Path(__file__).parent / "static" / "index.html"
    if index_path.exists():
        return index_path.read_text(encoding='utf-8')
    return "<h1>Chat UI not found</h1><p>Make sure static/index.html exists</p>"


# ============================================================================
# Run Server
# ============================================================================

if __name__ == "__main__":
    import uvicorn

    print("\n" + "=" * 70)
    print("  Energy Docs RAG - FastAPI Server")
    print("=" * 70)
    print("  Web UI:       http://localhost:8000/")
    print("  API Docs:     http://localhost:8000/docs")
    print("  ReDoc:        http://localhost:8000/redoc")
    print("  Health:       http://localhost:8000/health")
    print("=" * 70 + "\n")

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )
