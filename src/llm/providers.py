"""
LLM Provider Abstraction Layer
Supports: Claude (Anthropic), Kimi (Moonshot), OpenAI, Ollama (local)
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, AsyncGenerator
import os
import json


class LLMProvider(ABC):
    """Abstract base class for LLM providers"""
    
    @abstractmethod
    async def generate(self, prompt: str, **kwargs) -> str:
        """Generate text completion"""
        pass
    
    @abstractmethod
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Generate structured JSON output"""
        pass
    
    @abstractmethod
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        """Stream text generation"""
        pass


class ClaudeProvider(LLMProvider):
    """Anthropic Claude API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-opus-20240229"):
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        self.model = model
        try:
            from anthropic import AsyncAnthropic
            self.client = AsyncAnthropic(api_key=self.api_key)
        except ImportError:
            raise ImportError("Install anthropic: pip install anthropic")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.messages.create(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Use tool use for structured output"""
        import json
        
        # Add schema instructions to prompt
        schema_prompt = f"""{prompt}

You must respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no other text."""
        
        response = await self.generate(schema_prompt, **kwargs)
        
        # Parse JSON
        try:
            # Extract JSON from markdown if present
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}\nResponse: {response}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        async with self.client.messages.stream(
            model=self.model,
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            messages=[{"role": "user", "content": prompt}]
        ) as stream:
            async for text in stream.text_stream:
                yield text


class KimiProvider(LLMProvider):
    """Moonshot Kimi API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "moonshot-v1-128k"):
        self.api_key = api_key or os.getenv("KIMI_API_KEY")
        self.model = model
        self.base_url = "https://api.moonshot.cn/v1"
        try:
            from openai import AsyncOpenAI
            # Kimi uses OpenAI-compatible API
            self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)
        except ImportError:
            raise ImportError("Install openai: pip install openai")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.choices[0].message.content
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        import json
        
        schema_prompt = f"""{prompt}

You must respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no other text."""
        
        response = await self.generate(schema_prompt, **kwargs)
        
        try:
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON response: {e}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OpenAIProvider(LLMProvider):
    """OpenAI GPT API"""
    
    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4-turbo-preview"):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model
        try:
            from openai import AsyncOpenAI
            self.client = AsyncOpenAI(api_key=self.api_key)
        except ImportError:
            raise ImportError("Install openai: pip install openai")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7)
        )
        return response.choices[0].message.content
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """Use function calling for structured output"""
        import json
        
        # Create function from schema
        function_name = "structured_response"
        
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            functions=[{
                "name": function_name,
                "description": "Return structured response",
                "parameters": schema
            }],
            function_call={"name": function_name},
            max_tokens=kwargs.get("max_tokens", 4096)
        )
        
        function_call = response.choices[0].message.function_call
        if function_call:
            return json.loads(function_call.arguments)
        else:
            raise ValueError("No function call in response")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 4096),
            temperature=kwargs.get("temperature", 0.7),
            stream=True
        )
        async for chunk in response:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content


class OllamaProvider(LLMProvider):
    """Local models via Ollama"""
    
    def __init__(self, model: str = "llama3.2", base_url: str = "http://localhost:11434"):
        self.model = model
        self.base_url = base_url
        try:
            import aiohttp
            self.aiohttp = aiohttp
        except ImportError:
            raise ImportError("Install aiohttp: pip install aiohttp")
    
    async def generate(self, prompt: str, **kwargs) -> str:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", 0.7)
                    }
                }
            ) as response:
                data = await response.json()
                return data.get("response", "")
    
    async def generate_structured(self, prompt: str, schema: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        import json
        
        schema_prompt = f"""{prompt}

You must respond with a valid JSON object matching this schema:
{json.dumps(schema, indent=2)}

Respond ONLY with the JSON object, no other text."""
        
        response = await self.generate(schema_prompt, **kwargs)
        
        try:
            # Extract JSON
            if "```json" in response:
                json_str = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                json_str = response.split("```")[1].split("```")[0]
            else:
                json_str = response
            return json.loads(json_str.strip())
        except json.JSONDecodeError as e:
            raise ValueError(f"Failed to parse JSON: {e}")
    
    async def generate_stream(self, prompt: str, **kwargs) -> AsyncGenerator[str, None]:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": True
                }
            ) as response:
                async for line in response.content:
                    if line:
                        try:
                            data = json.loads(line)
                            if "response" in data:
                                yield data["response"]
                        except:
                            pass


class LLMFactory:
    """Factory for creating LLM providers"""
    
    PROVIDERS = {
        "claude": ClaudeProvider,
        "kimi": KimiProvider,
        "openai": OpenAIProvider,
        "ollama": OllamaProvider
    }
    
    @classmethod
    def create(cls, provider_name: str, **kwargs) -> LLMProvider:
        """Create LLM provider by name"""
        provider_name = provider_name.lower()
        if provider_name not in cls.PROVIDERS:
            raise ValueError(f"Unknown provider: {provider_name}. Available: {list(cls.PROVIDERS.keys())}")
        
        return cls.PROVIDERS[provider_name](**kwargs)
    
    @classmethod
    def from_env(cls) -> LLMProvider:
        """Auto-detect provider from environment variables"""
        if os.getenv("ANTHROPIC_API_KEY"):
            return cls.create("claude")
        elif os.getenv("KIMI_API_KEY"):
            return cls.create("kimi")
        elif os.getenv("OPENAI_API_KEY"):
            return cls.create("openai")
        else:
            # Try local Ollama
            return cls.create("ollama")
