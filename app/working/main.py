from contextlib import asynccontextmanager
from typing import Any, List

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import logfire

from .routers import pdf, chat

# Load environment variables
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    """Handle application startup and shutdown events."""
    # Startup
    logfire.info("Starting up PDF RAG Chatbot")
    yield
    # Shutdown
    logfire.info("Shutting down PDF RAG Chatbot")

# Configure Logfire
logfire.configure()  # This will use credentials from ~/.logfire/default.toml

# Create FastAPI app
app = FastAPI(
    title="PDF RAG Chatbot",
    description="A chatbot that answers questions based on PDF content using RAG",
    version="1.0.0",
    lifespan=lifespan
)

# Instrument FastAPI and Pydantic
logfire.instrument_fastapi(app)
logfire.instrument_pydantic()

# CORS middleware
origins: List[str] = ["*"]  # Update this with your frontend URL in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add routers
app.include_router(pdf.router)
app.include_router(chat.router)

@app.get("/")
async def root() -> JSONResponse:
    """Root endpoint to verify the API is running."""
    return JSONResponse(
        content={"message": "PDF RAG Chatbot API is running"},
        status_code=200
    )
