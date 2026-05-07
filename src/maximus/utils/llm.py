"""LLM client for Maximus.ai - Ollama (free) + OpenAI-compatible APIs."""

from __future__ import annotations

import json
import logging
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

logger = logging.getLogger(__name__)


class OllamaClient:
    """Local Ollama client - 100% free inference."""

    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.AsyncClient(timeout=httpx.Timeout(120.0, connect=10.0))

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        tools: Optional[List[Dict]] = None,
        temperature: float = 0.7,
        stream: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream chat completions from Ollama."""
        payload = {
            "model": model,
            "messages": messages,
            "stream": stream,
            "options": {"temperature": temperature},
        }
        if tools:
            payload["tools"] = tools

        async with self.client.stream(
            "POST", f"{self.base_url}/api/chat", json=payload
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.strip():
                    continue
                try:
                    chunk = json.loads(line)
                    yield chunk
                except json.JSONDecodeError:
                    logger.warning(f"Failed to parse JSON: {line}")

    async def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
    ) -> str:
        """Generate text from Ollama (non-streaming)."""
        payload: Dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": temperature},
        }
        if system:
            payload["system"] = system

        response = await self.client.post(
            f"{self.base_url}/api/generate", json=payload
        )
        response.raise_for_status()
        data = response.json()
        return data.get("response", "")

    async def list_models(self) -> List[str]:
        """List available Ollama models."""
        response = await self.client.get(f"{self.base_url}/api/tags")
        response.raise_for_status()
        data = response.json()
        return [m["name"] for m in data.get("models", [])]

    async def close(self):
        await self.client.aclose()


class LLMClient:
    """Unified LLM client supporting Ollama (free) and OpenAI-compatible APIs."""

    def __init__(self, config):
        self.config = config
        self.ollama = OllamaClient(config.ollama_url)
        self.openai_client = None

        # Initialize OpenAI if API key present (optional)
        if config.model.startswith("gpt-") or config.model.startswith("openai:"):
            try:
                from openai import AsyncOpenAI
                import os
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    self.openai_client = AsyncOpenAI(api_key=api_key)
            except ImportError:
                logger.warning("openai package not installed")

    async def chat(self, messages: List[Dict], tools: Optional[List] = None, **kwargs):
        """Route to appropriate backend."""
        model = kwargs.get("model", self.config.model)

        if model.startswith("gpt-") and self.openai_client:
            async for chunk in self._openai_chat(messages, tools, **kwargs):
                yield chunk
        else:
            async for chunk in self.ollama.chat(model, messages, tools, **kwargs):
                yield chunk

    async def generate(self, prompt: str, system: Optional[str] = None, **kwargs) -> str:
        """Generate text."""
        model = kwargs.get("model", self.config.model)

        if model.startswith("gpt-") and self.openai_client:
            return await self._openai_generate(prompt, system, **kwargs)
        else:
            return await self.ollama.generate(model=model, prompt=prompt, system=system)

    async def _openai_chat(self, messages, tools, **kwargs):
        """OpenAI-compatible chat streaming."""
        from openai import NOT_GIVEN
        stream = await self.openai_client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=messages,
            tools=tools or NOT_GIVEN,
            stream=True,
        )
        async for chunk in stream:
            yield chunk

    async def _openai_generate(self, prompt, system, **kwargs) -> str:
        """OpenAI text generation."""
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        response = await self.openai_client.chat.completions.create(
            model=kwargs.get("model", "gpt-4"),
            messages=messages,
            temperature=kwargs.get("temperature", 0.7),
        )
        return response.choices[0].message.content

    async def close(self):
        await self.ollama.close()
