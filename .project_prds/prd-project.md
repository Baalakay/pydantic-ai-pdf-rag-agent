# PDF RAG Chatbot Project Documentation

## Overview
A PDF RAG (Retrieval Augmented Generation) Chatbot that enables users to query and extract information from product PDF manuals and datasheets. The system uses advanced natural language processing and vector embeddings to provide accurate, context-aware responses.

## Core Components

### 1. PDF Processing (`app/pdf_reader.py`)
- **Purpose**: Extracts and processes content from PDF documents
- **Key Features**:
  - Text extraction using PDFPlumber
  - Section categorization (features, advantages, electrical specs, etc.)
  - Diagram extraction
  - Model comparison functionality
- **Main Functions**:
  - `find_pdf_by_model()`: Locates PDF files based on model keywords
  - `extract_sections()`: Categorizes PDF content into structured sections
  - `extract_model_from_query()`: Parses model numbers from natural language queries
  - `identify_query_type()`: Determines query intent and target section
  - `search_pdf()`: Performs targeted searches within PDFs

### 2. Vector Store (`app/core/vector_store.py`)
- **Purpose**: Manages semantic search functionality using vector embeddings
- **Technology**: OpenAI's text-embedding-3-small model
- **Features**:
  - Vector embedding generation and storage
  - Similarity-based search
  - Persistent storage in JSON format
  - Async operations for better performance
- **Key Components**:
  - Vector entry management
  - Cosine similarity search
  - Disk-based persistence
  - Error handling and logging

### 3. FastAPI Backend (`app/working/main.py`)
- **Purpose**: Provides REST API endpoints for the application
- **Features**:
  - PDF upload and management endpoints
  - Chat functionality
  - CORS middleware for frontend integration
  - Structured logging with Logfire
- **Components**:
  - Modular routers for PDF and chat functionality
  - Lifespan management
  - Error handling
  - Request/response validation

## Technology Stack
- **Web Framework**: FastAPI
- **AI/ML**:
  - OpenAI Embeddings (text-embedding-3-small)
  - GPT-4o-mini for chat completion
- **Data Validation**: Pydantic
- **PDF Processing**:
  - PDFPlumber
  - PyMuPDF (fitz)
- **Vector Operations**: NumPy
- **Observability**: Logfire
- **Development**:
  - Python 3.11+
  - Async/await for concurrency
  - Type hints and validation

## Key Features

### 1. Semantic Search
- Vector embeddings for accurate content retrieval
- Cosine similarity-based ranking
- Top-k results retrieval
- Persistent storage of embeddings

### 2. PDF Processing
- Section extraction and categorization
- Diagram and image extraction
- Model specification parsing
- Structured content organization

### 3. Model Comparison
- Feature comparison between different models
- Specification matching
- Difference highlighting
- Technical parameter comparison

### 4. Observability
- Structured logging with Logfire
- Request tracking
- Error monitoring
- Performance metrics

## Architecture Design

### Data Flow
1. User submits query through API
2. Query is processed and intent is identified
3. Relevant PDF content is retrieved using vector search
4. Response is generated using GPT-4o-mini
5. Structured response is returned to user

### Security Considerations
- Input validation using Pydantic
- CORS configuration
- Environment variable management
- Secure file handling

### Performance Optimizations
- Async operations
- Vector similarity caching
- Efficient PDF processing
- Batched operations where possible

## Usage Examples

### PDF Queries
```python
# Example query for electrical specifications
GET /chat?query="What are the electrical specifications for HSR-520R?"

# Example model comparison
GET /chat?query="Compare HSR-520R and HSR-637W-2"

# Example diagram request
GET /chat?query="Show me the diagram for HSR-520R"
```

### Response Format
```json
{
  "response": "...",
  "source": "HSR-520R-Series-Rev-K.pdf",
  "confidence": 0.95,
  "sections": ["electrical", "specifications"]
}
```

## Future Enhancements
1. Multi-language support
2. Advanced caching mechanisms
3. User feedback integration
4. Enhanced diagram processing
5. Automated testing suite
6. Performance monitoring dashboard

## Development Guidelines
1. Follow type hints and Pydantic models
2. Implement comprehensive error handling
3. Add structured logging for key operations
4. Maintain modular architecture
5. Document new features and changes
6. Write unit tests for core functionality 