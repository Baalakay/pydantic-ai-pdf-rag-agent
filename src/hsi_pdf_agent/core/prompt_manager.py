import json
from datetime import datetime
from pathlib import Path

from hsi_pdf_agent.models.prompt_config import PromptConfig, PromptConfigurations


class PromptManager:
    """Manages loading and updating prompt configurations."""
    
    PROMPTS_DIR = Path(__file__).parent / "prompts"
    
    @classmethod
    def load_prompts(cls) -> PromptConfigurations:
        """Load all prompt configurations from JSON files."""
        prompts = {}
        
        # Ensure prompts directory exists
        cls.PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
        
        # Load each JSON file in the prompts directory
        for file_path in cls.PROMPTS_DIR.glob("*.json"):
            with open(file_path, "r") as f:
                prompt_data = json.load(f)
                prompts[file_path.stem] = PromptConfig.model_validate(prompt_data)
        
        return PromptConfigurations(
            analysis_prompt=prompts.get("analysis"),
            findings_prompt=prompts.get("findings")
        )
    
    @classmethod
    def update_prompt(cls, prompt_name: str, prompt_config: PromptConfig, admin: str) -> PromptConfigurations:
        """Update a specific prompt configuration."""
        # Validate prompt name
        if prompt_name not in ["analysis", "findings"]:
            raise ValueError(f"Invalid prompt name: {prompt_name}")
        
        # Update prompt metadata
        prompt_config.last_modified = datetime.utcnow()
        prompt_config.modified_by = admin
        
        # Save updated prompt
        file_path = cls.PROMPTS_DIR / f"{prompt_name}.json"
        with open(file_path, "w") as f:
            json.dump(prompt_config.model_dump(mode="json"), f, indent=2)
        
        return cls.load_prompts() 