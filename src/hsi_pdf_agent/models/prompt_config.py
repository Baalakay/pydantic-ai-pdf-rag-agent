from pydantic import BaseModel, Field, SecretStr
from typing import Optional


class LLMConfig(BaseModel):
    model: str = Field(..., description="The LLM model to use (e.g. gpt-4-turbo-preview)")
    api_key: SecretStr = Field(..., description="API key for the LLM service")
    organization_id: Optional[SecretStr] = Field(None, description="Optional organization ID for the LLM service")
    temperature: float = Field(0.7, description="Temperature setting for the LLM")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens for the response")


class PromptConfig(BaseModel):
    name: str = Field(..., description="Name of the prompt configuration")
    description: str = Field(..., description="Description of what this prompt does")
    prompt_template: str = Field(..., description="The actual prompt template")
    llm_config: LLMConfig = Field(..., description="LLM configuration for this prompt")
    version: str = Field("1.0.0", description="Version of this prompt configuration")
    last_modified: Optional[str] = None
    modified_by: Optional[str] = None


class PromptConfigurations(BaseModel):
    analysis_prompt: PromptConfig = Field(..., description="Configuration for the analysis prompt")
    findings_prompt: PromptConfig = Field(..., description="Configuration for the findings prompt")


class OllamaConfig(BaseModel):
    model: str = Field("deepseek-r1:7b", description="The Ollama model to use")
    base_url: str = Field("http://host.docker.internal:11434", description="Base URL for Ollama server")
    temperature: float = Field(0.7, description="Temperature setting for the model") 