# PDF RAG Chatbot

A backend service for a chatbot that uses Retrieval Augmented Generation (RAG) to answer questions about PDF documents. Built with FastAPI, PydanticAI, Pydantic, and Logfire.

## Features

- PDF document ingestion and indexing
- Question answering using RAG with GPT-4o-mini
- Secure API endpoints with FastAPI
- Structured logging with Logfire
- Data validation with Pydantic
- AI agent implementation with PydanticAI

## Project Structure

```
app/
├── api/          # API version management
├── core/         # Core application components
├── models/       # Database and PydanticAI models
├── routers/      # API route handlers
├── schemas/      # Pydantic models for validation
├── tests/        # Test files
├── logging/      # Logfire configuration
└── main.py      # Application entry point
```

## Requirements

- Python 3.11+
- FastAPI
- PydanticAI
- Pydantic
- Logfire
- Additional dependencies in requirements.txt

## Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd pdf-rag-chatbot
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Run the application:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at `http://localhost:8000`

## API Documentation

Once running, visit:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Development

- Follow PEP 8 style guide
- Use type hints
- Write tests for new features
- Update documentation as needed

## License

[Your chosen license] 