"""LLM service interface - defines contract for language model interactions."""
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator


class ILLMService(ABC):
    """Interface for Large Language Model service."""

    @abstractmethod
    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a response from the LLM.

        Args:
            prompt: User prompt/query
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response

        Returns:
            Generated text response

        Raises:
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from the LLM.

        Args:
            prompt: User prompt/query
            system_prompt: Optional system instructions
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response

        Yields:
            Chunks of generated text

        Raises:
            RuntimeError: If generation fails
        """
        pass

    @abstractmethod
    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embeddings for text.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats

        Raises:
            RuntimeError: If embedding fails
        """
        pass
