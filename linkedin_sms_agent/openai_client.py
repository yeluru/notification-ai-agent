"""OpenAI LLM client implementation."""

import logging
from typing import Optional

from .config import LLMConfig
from .llm_client import LLMClient

logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    logger.warning("OpenAI library not installed. Install with: pip install openai")


class OpenAILLMClient(LLMClient):
    """OpenAI API client for LLM completion."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the OpenAI client.
        
        Args:
            config: LLM configuration.
        """
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "OpenAI library not installed. Install with: pip install openai"
            )
        
        self.config = config
        self.client = OpenAI(
            api_key=config.api_key,
            base_url=config.base_url if config.base_url else None
        )
    
    def complete(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Complete a prompt using OpenAI's API.
        
        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum number of tokens in the response.
            temperature: Sampling temperature.
            
        Returns:
            The LLM's response text (trimmed).
        """
        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = response.choices[0].message.content.strip()
            return result
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise


class GenericHTTPLLMClient(LLMClient):
    """Generic HTTP client for OpenAI-compatible LLM APIs."""
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the generic HTTP client.
        
        Args:
            config: LLM configuration.
        """
        import requests
        self.config = config
        self.base_url = config.base_url or "https://api.openai.com/v1"
        self.api_key = config.api_key
        self.model = config.model
        self.requests = requests
    
    def complete(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Complete a prompt using a generic HTTP API (OpenAI-compatible).
        
        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum number of tokens in the response.
            temperature: Sampling temperature.
            
        Returns:
            The LLM's response text (trimmed).
        """
        url = f"{self.base_url}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": self.model,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
        
        try:
            response = self.requests.post(url, json=payload, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            result = data["choices"][0]["message"]["content"].strip()
            return result
        except Exception as e:
            logger.error(f"HTTP LLM API error: {e}")
            raise


