import boto3
from botocore.exceptions import ClientError
import os
from typing import List, Dict, Union, Optional
from server.src.models.document import RetrievedDocument  # Import the Pydantic model
from server.src.config import Settings
from fastapi import Depends
import requests
import json
from server.src.config import settings
import opik
from openai import OpenAI
from functools import lru_cache

def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """
    Factory function to create an OpenAI client instance.
    
    Args:
        api_key (Optional[str]): OpenAI API key. If not provided, will attempt to get from environment.
        
    Returns:
        OpenAI: Configured OpenAI client instance
        
    Raises:
        ValueError: If no API key is available
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError("OpenAI API key must be provided either directly or via OPENAI_API_KEY environment variable")
    return OpenAI(api_key=key)

@lru_cache()
def get_default_client() -> OpenAI:
    """
    Get or create a cached default OpenAI client instance.
    Uses environment variables for configuration.
    
    Returns:
        OpenAI: Configured OpenAI client instance
    """
    return get_openai_client()

@opik.track
def call_llm(prompt: str, client: Optional[OpenAI] = None) -> Dict[str, Union[str, float, None]]:
    """
    Call OpenAI's API to generate a response.
    
    Args:
        prompt (str): The prompt to send to the language model
        client (Optional[OpenAI]): OpenAI client instance. If not provided, uses default client.
        
    Returns:
        Dict containing:
            - response (str): The generated response text
            - response_tokens_per_second (Optional[float]): Token generation rate if available
    """
    try:
        # Use provided client or get default
        openai_client = client or get_default_client()
            
        response = openai_client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
        )

        data = {
            "response": response.choices[0].message.content,
            "response_tokens_per_second": (
                (response.usage.total_tokens / response.usage.completion_tokens)
                if hasattr(response, "usage")
                else None
            )
        }
        return data

    except Exception as e:
        return {
            "response": f"I'm sorry, but I encountered an error while generating a response: {str(e)}",
            "response_tokens_per_second": None
        }

@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
    client: Optional[OpenAI] = None
) -> Dict[str, Union[str, float, None]]:
    """
    Generate a response using the OpenAI API based on provided context and query.
    
    Args:
        query (str): The user query to respond to
        chunks (List[Dict]): List of document chunks containing context
        max_tokens (int): Maximum number of tokens to generate in response
        temperature (float): Sampling temperature for response generation
        client (Optional[OpenAI]): OpenAI client instance for dependency injection
        
    Returns:
        Dict containing the generated response and metadata
    """
    QUERY_PROMPT = """
    You are a helpful AI language assistant, please use the following context to answer the query. Answer in English.
    Context: {context}
    Query: {query}
    Answer:
    """
    # Concatenate documents' summaries as the context for generation
    context = "\n".join([chunk["chunk"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)
    return call_llm(prompt, client=client)