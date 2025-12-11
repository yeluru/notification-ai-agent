"""Abstract LLM client interface."""

from abc import ABC, abstractmethod


class LLMClient(ABC):
    """Abstract base class for LLM clients."""
    
    @abstractmethod
    def complete(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """
        Complete a prompt using the LLM.
        
        Args:
            prompt: The prompt to send to the LLM.
            max_tokens: Maximum number of tokens in the response.
            temperature: Sampling temperature (0.0-1.0).
            
        Returns:
            The LLM's response text (trimmed).
        """
        pass


