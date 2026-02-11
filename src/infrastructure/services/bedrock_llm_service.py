"""Bedrock LLM service implementation."""
import json
from typing import Any, AsyncIterator

import boto3
from botocore.config import Config

from src.domain.interfaces.llm_service import ILLMService


class BedrockLLMService(ILLMService):
    """LLM service implementation using AWS Bedrock."""

    def __init__(
        self,
        model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0",
        region: str = "us-east-1",
        boto_config: Config | None = None,
    ) -> None:
        """
        Initialize Bedrock LLM service.

        Args:
            model_id: Bedrock model identifier
            region: AWS region
            boto_config: Optional boto3 configuration
        """
        self._model_id = model_id
        self._region = region

        config = boto_config or Config(
            region_name=region,
            retries={"max_attempts": 3, "mode": "adaptive"},
            read_timeout=300,
        )

        self._bedrock_runtime = boto3.client("bedrock-runtime", config=config)

    async def generate(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> str:
        """
        Generate a response from Bedrock.

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
        try:
            # Construct messages for Claude 3
            messages = [{"role": "user", "content": prompt}]

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
            }

            if system_prompt:
                request_body["system"] = system_prompt

            response = self._bedrock_runtime.invoke_model(
                modelId=self._model_id,
                body=json.dumps(request_body),
            )

            response_body = json.loads(response["body"].read())
            content = response_body.get("content", [])

            if not content:
                raise RuntimeError("No content in LLM response")

            return content[0].get("text", "")

        except Exception as e:
            raise RuntimeError(f"Failed to generate LLM response: {str(e)}")

    async def generate_stream(
        self,
        prompt: str,
        system_prompt: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
    ) -> AsyncIterator[str]:
        """
        Generate a streaming response from Bedrock.

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
        try:
            # Construct messages for Claude 3
            messages = [{"role": "user", "content": prompt}]

            request_body = {
                "anthropic_version": "bedrock-2023-05-31",
                "max_tokens": max_tokens,
                "messages": messages,
                "temperature": temperature,
            }

            if system_prompt:
                request_body["system"] = system_prompt

            response = self._bedrock_runtime.invoke_model_with_response_stream(
                modelId=self._model_id,
                body=json.dumps(request_body),
            )

            stream = response.get("body")
            if not stream:
                raise RuntimeError("No stream in response")

            for event in stream:
                chunk = event.get("chunk")
                if chunk:
                    chunk_data = json.loads(chunk.get("bytes").decode())

                    if chunk_data.get("type") == "content_block_delta":
                        delta = chunk_data.get("delta", {})
                        if delta.get("type") == "text_delta":
                            yield delta.get("text", "")

        except Exception as e:
            raise RuntimeError(f"Failed to generate streaming LLM response: {str(e)}")

    async def embed_text(self, text: str) -> list[float]:
        """
        Generate embeddings for text using Bedrock Titan Embeddings.

        Args:
            text: Text to embed

        Returns:
            Vector embedding as list of floats

        Raises:
            RuntimeError: If embedding fails
        """
        try:
            # Use Amazon Titan Embeddings model
            embedding_model_id = "amazon.titan-embed-text-v1"

            request_body = json.dumps({"inputText": text})

            response = self._bedrock_runtime.invoke_model(
                modelId=embedding_model_id,
                body=request_body,
            )

            response_body = json.loads(response["body"].read())
            embedding = response_body.get("embedding")

            if not embedding:
                raise RuntimeError("No embedding in response")

            return embedding

        except Exception as e:
            raise RuntimeError(f"Failed to generate embeddings: {str(e)}")
