from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
import logfire
import httpx
import asyncio
import json
from ..models.prompt_config import OllamaConfig

class Message(BaseModel):
    role: str
    content: str

class ChatResponse(BaseModel):
    answer: str = Field(..., alias="content")  # This allows both .answer and .content to work
    context_sections: List[str] = []

    @property
    def content(self) -> str:
        """Backward compatibility for code expecting .content"""
        return self.answer

class AIProvider(ABC):
    @abstractmethod
    async def complete(self, messages: List[Message], **kwargs) -> ChatResponse:
        pass

class OllamaProvider(AIProvider):
    """Provider for Ollama API."""
    def __init__(self, base_url: str = "http://host.docker.internal:11434", timeout: int = 10):
        self.base_url = base_url
        self.timeout = timeout
        
    async def complete(self, messages: List[Message], **kwargs) -> ChatResponse:
        formatted_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        logfire.info("starting_ollama_request", 
            message_count=len(messages),
            first_message_preview=messages[0].content[:100] if messages else None,
            kwargs=kwargs
        )
        
        try:
            # Set specific timeouts for connect, read, and write operations
            timeout = httpx.Timeout(
                connect=5.0,    # Connection timeout
                read=10.0,      # Read timeout
                write=5.0,      # Write timeout
                pool=5.0        # Pool timeout
            )
            
            logfire.info("creating_http_client")
            async with httpx.AsyncClient(timeout=timeout) as client:
                request_data = {
                    "model": kwargs.get("model", "deepseek-r1:7b"),
                    "messages": formatted_messages
                }
                logfire.info("ollama_request_prepared", 
                    url=f"{self.base_url}/api/chat",
                    request_data=request_data
                )
                
                logfire.info("sending_request")
                try:
                    response = await client.post(
                        f"{self.base_url}/api/chat",
                        json=request_data
                    )
                except httpx.ConnectError:
                    logfire.error(
                        "ollama_connection_error",
                        message="Could not connect to Ollama service. Is it running?"
                    )
                    raise ValueError(
                        "Could not connect to Ollama service. Please ensure Ollama is running on port 11434"
                    )
                logfire.info("received_response", status_code=response.status_code)
                
                if not response.is_success:
                    error_body = await response.aread()
                    error_text = error_body.decode()
                    logfire.error(
                        "ollama_error_response", 
                        status_code=response.status_code,
                        error_body=error_text,
                        request_data=request_data
                    )
                    raise ValueError(f"Ollama error response: {error_text}")
                
                # Get raw response text first
                response_bytes = await response.aread()
                raw_response = response_bytes.decode()
                logfire.info("raw_response_debug", 
                    response_preview=raw_response[:200],
                    response_length=len(raw_response),
                    has_content=bool(raw_response.strip()),
                    first_line=raw_response.split('\n')[0] if raw_response else None
                )
                
                try:
                    # Handle Ollama's streaming response format
                    full_response = ""
                    in_think_block = False
                    line_count = 0
                    for line in raw_response.splitlines():
                        line_count += 1
                        if not line.strip():
                            continue
                        try:
                            chunk = json.loads(line)
                            logfire.info("processing_chunk", 
                                has_response="response" in chunk,
                                has_message="message" in chunk,
                                content=chunk.get("message", {}).get("content", "")[:50],
                                line_number=line_count,
                                done=chunk.get("done", False)
                            )
                            
                            # Only process message content
                            if "message" in chunk and "content" in chunk["message"]:
                                content = chunk["message"]["content"]
                                
                                # Handle think tags (both escaped and unescaped)
                                if content == "<think>" or content == "\u003cthink\u003e":
                                    in_think_block = True
                                    continue
                                elif content == "</think>" or content == "\u003c/think\u003e":
                                    in_think_block = False
                                    continue
                                
                                if not in_think_block:
                                    full_response += content
                                
                            # If this is the final message, break
                            if chunk.get("done", False):
                                break
                        except json.JSONDecodeError:
                            logfire.error("line_parse_error", 
                                line_preview=line[:100],
                                line_number=line_count
                            )
                            continue
                except json.JSONDecodeError:
                    logfire.error("json_decode_error", response=raw_response[:200])
                    raise ValueError("Invalid JSON response from Ollama")
                
                if not full_response:
                    logfire.error("empty_response", message="No valid content received from Ollama")
                    raise ValueError("No valid content received from Ollama")
                
                full_response = full_response.strip()
                
                # Extract JSON from code block if present
                if full_response.startswith("```json"):
                    try:
                        # Extract content between ```json and the next ```
                        json_text = full_response.split("```json\n", 1)[1].split("```", 1)[0].strip()
                        full_response = json_text
                    except IndexError:
                        logfire.error("code_block_parse_error", 
                            response_preview=full_response[:200]
                        )
                
                # Ensure we have a valid JSON response with required fields
                try:
                    # If response is already JSON, parse it
                    json_data = json.loads(full_response)
                except json.JSONDecodeError:
                    # If not JSON, create a default structure
                    json_data = {
                        "findings": {
                            "recommendations": [],
                            "summary": "No analysis available.",
                            "technical_details": "No detailed analysis available."
                        }
                    }
                    logfire.error("invalid_json_format", 
                        response_preview=full_response[:200],
                        error="Response was not in JSON format"
                    )
                
                # Ensure all required fields are present
                if "findings" not in json_data:
                    json_data = {"findings": json_data}
                if "technical_details" not in json_data["findings"]:
                    json_data["findings"]["technical_details"] = "Technical details not provided"
                if "recommendations" not in json_data["findings"]:
                    json_data["findings"]["recommendations"] = []
                if "summary" not in json_data["findings"]:
                    json_data["findings"]["summary"] = "Summary not provided"
                    
                return ChatResponse(
                    content=json.dumps(json_data),
                    context_sections=[]
                )
                
        except Exception as e:
            logfire.error("ollama_request_error", error=str(e), error_type=type(e).__name__)
            raise ValueError(f"Failed to communicate with Ollama: {str(e)}") 