from contextlib import asynccontextmanager
from typing import Any, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
# import logfire  # Temporarily disabled

# Import routers directly
from .routers.pdf import router as pdf_router
from .routers.chat import chat_router, compare_router
from .routers.analysis import router as analysis_router

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Handle application startup and shutdown events."""
    # Startup
    print("Starting up PDF RAG Chatbot")  # Using print instead of logfire
    yield
    # Shutdown
    print("Shutting down PDF RAG Chatbot")  # Using print instead of logfire

# Create FastAPI app
app = FastAPI(
    title="PDF RAG Chatbot",
    description="A chatbot that answers questions based on PDF content using RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS - Add more allowed origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(pdf_router)
app.include_router(chat_router)
app.include_router(compare_router)
app.include_router(analysis_router)

@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint to verify the API is running."""
    return JSONResponse(
        content={"message": "PDF RAG Chatbot API is running"},
        status_code=200
    )
