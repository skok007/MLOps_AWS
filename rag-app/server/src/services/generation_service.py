import os
from typing import List, Dict, Union, Optional
from server.src.models.document import RetrievedDocument
from server.src.config import settings
import opik
from openai import OpenAI
from functools import lru_cache

def get_openai_client(api_key: Optional[str] = None) -> OpenAI:
    """Create an OpenAI client instance with the provided or environment API key.

    Args:
        api_key (Optional[str]): OpenAI API key. If not provided, will attempt to get from environment.

    Returns:
        OpenAI: Configured OpenAI client instance.

    Raises:
        ValueError: If no API key is available in either the parameter or environment.
    """
    key = api_key or os.environ.get("OPENAI_API_KEY")
    if not key:
        raise ValueError(
            "OpenAI API key must be provided either directly or via "
            "OPENAI_API_KEY environment variable"
        )
    return OpenAI(api_key=key)

@lru_cache()
def get_default_client() -> OpenAI:
    """Get or create a cached default OpenAI client instance.

    This function uses environment variables for configuration and caches the client
    to avoid creating multiple instances.

    Returns:
        OpenAI: Configured OpenAI client instance using environment variables.

    Raises:
        ValueError: If OPENAI_API_KEY is not set in environment variables.
    """
    return get_openai_client()

@opik.track
def call_llm(prompt: str, client: Optional[OpenAI] = None) -> Dict[str, Union[str, float, None]]:
    """Call OpenAI's API to generate a response.

    This function sends a prompt to the OpenAI API and returns the generated response.
    It handles error cases and provides token usage information when available.

    Args:
        prompt (str): The prompt to send to the language model.
        client (Optional[OpenAI]): OpenAI client instance. If not provided, uses default client.

    Returns:
        Dict[str, Union[str, float, None]]: A dictionary containing:
            - response (str): The generated response text
            - response_tokens_per_second (Optional[float]): Token generation rate if available

    Raises:
        ValueError: If no API key is available
        Exception: If the API call fails
    """
    try:
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
        error_msg = (
            "I'm sorry, but I encountered an error while generating a response: "
            f"{str(e)}"
        )
        return {
            "response": error_msg,
            "response_tokens_per_second": None
        }

@opik.track
async def generate_response(
    query: str,
    chunks: List[RetrievedDocument],
    max_tokens: int = 200,
    temperature: float = 0.7,
    client: Optional[OpenAI] = None
) -> Dict[str, Union[str, float, None]]:
    """Generate a response using the OpenAI API based on provided context and query.

    This function takes a user query and relevant document chunks, formats them into
    a context-aware prompt, and generates a response using the OpenAI API.

    Args:
        query (str): The user query to respond to.
        chunks (List[RetrievedDocument]): List of document chunks containing context.
        max_tokens (int, optional): Maximum number of tokens to generate in response. Defaults to 200.
        temperature (float, optional): Temperature parameter for response generation. Defaults to 0.7.
        client (Optional[OpenAI], optional): OpenAI client instance. Defaults to None.

    Returns:
        Dict[str, Union[str, float, None]]: A dictionary containing:
            - response (str): The generated response text
            - response_tokens_per_second (Optional[float]): Token generation rate if available

    Raises:
        Exception: If the API call fails or context formatting fails
    """
    context = format_context_from_chunks(chunks)
    prompt = create_prompt_with_context(query, context)
    return call_llm(prompt, client)

def format_context_from_chunks(chunks: List[RetrievedDocument]) -> str:
    """Format document chunks into a context string for the prompt.

    This function takes a list of retrieved documents and formats them into a
    structured context string that can be used in the prompt.

    Args:
        chunks (List[RetrievedDocument]): List of document chunks to format.

    Returns:
        str: Formatted context string with document titles and content.

    Note:
        If no chunks are provided, returns a default message indicating no context is available.
    """
    if not chunks:
        return "No relevant context available."
    
    formatted_chunks = []
    for i, chunk in enumerate(chunks, 1):
        title = chunk.get("title", "Untitled")
        content = chunk.get("chunk", "")
        formatted_chunks.append(f"Document {i} - {title}:\n{content}\n")
    
    return "\n".join(formatted_chunks)

def create_prompt_with_context(query: str, context: str) -> str:
    """Create a prompt that includes the user query and relevant context.

    This function constructs a complete prompt for the language model by combining
    the user's query with the formatted context from retrieved documents.

    Args:
        query (str): The user query to be answered.
        context (str): Formatted context from document chunks.

    Returns:
        str: Complete prompt for the language model, including context and query.
    """
    return (
        "You are a helpful AI assistant that provides information based on the "
        "following context:\n\n"
        f"{context}\n\n"
        f"User Query: {query}\n\n"
        "Please provide a comprehensive answer based on the information in the "
        "context above. If the context doesn't contain relevant information to "
        "answer the query, please say so."
    )