"""
Model provider abstraction for multi-model support.
Supports: Gemini, Groq, and Ollama (aerospace-focused).
"""
import os
from typing import Optional, Dict, Any, List
from abc import ABC, abstractmethod
import json
from dotenv import load_dotenv

load_dotenv()


def get_ollama_models() -> List[str]:
    """Get list of locally available Ollama models."""
    try:
        from openai import OpenAI
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        client = OpenAI(
            api_key="ollama",
            base_url=f"{base_url}/v1"
        )
        
        # Try to list models using OpenAI-compatible API
        response = client.models.list()
        models = [model.id for model in response.data]
        return models if models else ["llama3.2", "llama3.1", "mistral", "phi3"]
    except Exception as e:
        print(f"Could not fetch Ollama models: {e}")
        return ["llama3.2", "llama3.1", "mistral", "phi3", "qwen2.5"]


class ModelProvider(ABC):
    """Abstract base class for model providers."""
    
    @abstractmethod
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """Generate text completion."""
        pass
    
    @abstractmethod
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        """Generate structured JSON output."""
        pass


class GeminiProvider(ModelProvider):
    """Google Gemini provider."""
    
    def __init__(self, model_name: str = "gemini-2.0-flash-exp"):
        import google.generativeai as genai
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise ValueError("GEMINI_API_KEY not found in environment")
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        generation_config = {
            "temperature": temperature,
            "max_output_tokens": max_tokens,
        }
        response = self.model.generate_content(prompt, generation_config=generation_config)
        return response.text
    
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        import google.generativeai as genai
        
        # Add JSON schema instruction to prompt
        schema_prompt = f"""{prompt}

You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return only the JSON object, no additional text."""
        
        generation_config = {
            "temperature": 0.3,
            "response_mime_type": "application/json",
        }
        
        response = self.model.generate_content(schema_prompt, generation_config=generation_config)
        return json.loads(response.text)


class ClaudeProvider(ModelProvider):
    """Anthropic Claude provider."""
    
    def __init__(self, model_name: str = "claude-3-5-sonnet-20241022"):
        from anthropic import Anthropic
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY not found in environment")
        self.client = Anthropic(api_key=api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=max_tokens,
            temperature=temperature,
            messages=[{"role": "user", "content": prompt}]
        )
        return message.content[0].text
    
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_prompt = f"""{prompt}

You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return only the JSON object, no additional text."""
        
        message = self.client.messages.create(
            model=self.model_name,
            max_tokens=4000,
            temperature=0.3,
            messages=[{"role": "user", "content": schema_prompt}]
        )
        
        response_text = message.content[0].text
        # Extract JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)


class GPTProvider(ModelProvider):
    """OpenAI GPT provider."""
    
    def __init__(self, model_name: str = "gpt-4o"):
        from openai import OpenAI
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment")
        self.client = OpenAI(api_key=api_key)
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_prompt = f"""{prompt}

You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return only the JSON object, no additional text."""
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": schema_prompt}],
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        return json.loads(response.choices[0].message.content)


class GroqProvider(ModelProvider):
    """Groq provider (using OpenAI-compatible API)."""
    
    def __init__(self, model_name: str = "llama-3.3-70b-versatile"):
        from openai import OpenAI
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in environment")
        self.client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1"
        )
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_prompt = f"""{prompt}

You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return only the JSON object, no additional text."""
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": schema_prompt}],
            temperature=0.3,
            max_tokens=4000,
            response_format={"type": "json_object"}
        )
        
        response_text = response.choices[0].message.content
        # Extract JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)


class OllamaProvider(ModelProvider):
    """Ollama local model provider."""
    
    def __init__(self, model_name: str = "llama3.2"):
        from openai import OpenAI
        base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.client = OpenAI(
            api_key="ollama",  # Ollama doesn't require API key
            base_url=f"{base_url}/v1"
        )
        self.model_name = model_name
    
    def generate(self, prompt: str, temperature: float = 0.7, max_tokens: int = 2000) -> str:
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": prompt}],
            temperature=temperature,
            max_tokens=max_tokens
        )
        return response.choices[0].message.content
    
    def generate_structured(self, prompt: str, response_schema: Dict[str, Any]) -> Dict[str, Any]:
        schema_prompt = f"""{prompt}

You must respond with valid JSON matching this schema:
{json.dumps(response_schema, indent=2)}

Return only the JSON object, no additional text."""
        
        response = self.client.chat.completions.create(
            model=self.model_name,
            messages=[{"role": "user", "content": schema_prompt}],
            temperature=0.3,
            max_tokens=4000
        )
        
        response_text = response.choices[0].message.content
        # Extract JSON if wrapped in markdown
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0].strip()
        
        return json.loads(response_text)


def create_model_provider(provider_name: str, model_name: str) -> ModelProvider:
    """Factory function to create model providers (Gemini, Groq, Ollama only)."""
    providers = {
        "gemini": GeminiProvider,
        "groq": GroqProvider,
        "ollama": OllamaProvider,
    }
    
    provider_class = providers.get(provider_name.lower())
    if not provider_class:
        raise ValueError(f"Unknown provider: {provider_name}. Supported: gemini, groq, ollama")
    
    return provider_class(model_name)


# Model configurations (aerospace-focused)
MODEL_CONFIGS = {
    "gemini": {
        "models": [
            "gemini-2.0-flash-exp", 
            "gemini-1.5-pro", 
            "gemini-1.5-flash",
            "gemini-2.0-flash-thinking-exp"
        ],
        "best_for_structured": "gemini-2.0-flash-exp",
        "best_for_reasoning": "gemini-1.5-pro"
    },
    "groq": {
        "models": [
            "llama-3.3-70b-versatile", 
            "llama-3.1-70b-versatile", 
            "llama-3.2-90b-vision-preview",
            "mixtral-8x7b-32768",
            "gemma2-9b-it"
        ],
        "best_for_structured": "llama-3.3-70b-versatile",
        "best_for_reasoning": "llama-3.3-70b-versatile"
    },
    "ollama": {
        "models": ["llama3.2", "llama3.1", "mistral", "phi3", "qwen2.5", "deepseek-r1"],
        "best_for_structured": "llama3.2",
        "best_for_reasoning": "llama3.2"
    }
}
