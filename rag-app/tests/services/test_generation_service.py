# example_prompts = ["tell me about quantum criticality for perovskites?",
#                    "what materials are often used along with perovskites?",
#                    "what electronic structure phenomena are important in recent perovskite papers?",
#                    "do any of the papers you know about mention band gaps of perovskites?"
#                    ]

import pytest
from typing import Dict, Union
from server.src.services.generation_service import generate_response

# Leverages the mock's from conftest.py
@pytest.mark.asyncio
async def test_generate_response_basic(
    mock_query, mock_chunks, mock_config, mock_generate_response
):
    """Test the basic functionality of the generate_response function.

    This test verifies that the function correctly processes a basic query
    with provided mock document chunks and configuration. It ensures that
    the response includes pertinent information from both the query and context.

    Args:
        mock_query: The mock query input for testing
        mock_chunks: List of mock document chunks with id, title, chunk, and similarity_score
        mock_config: Configuration settings for the generation
        mock_generate_response: Mock for the LLM response generation

    Assertions:
        - The response is a dictionary containing the expected keys
        - The response includes content from the query and context
        - The response structure matches the expected format
    """
    mock_generate_response.return_value = {
        "response": "Here is information about perovskites: They are used in solar cells.",
        "response_tokens_per_second": 100.0
    }

    response = await generate_response(mock_query, mock_chunks, **mock_config)

    assert isinstance(response, dict), "Response should be a dictionary"
    assert "response" in response, "Response should contain a 'response' key"
    assert "response_tokens_per_second" in response, "Response should contain token rate information"
    assert "perovskites" in response["response"].lower(), "Response should contain query content"
    assert "solar cells" in response["response"].lower(), "Response should reference context from chunks"


@pytest.mark.asyncio
async def test_generate_response_empty_chunks(
    mock_query, mock_config, mock_generate_response
):
    """Test the generate_response function with an empty list of chunks.

    This test verifies that the function handles the case of no context
    appropriately and returns a meaningful response.

    Args:
        mock_query: The mock query input for testing
        mock_config: Configuration settings for the generation
        mock_generate_response: Mock for the LLM response generation

    Assertions:
        - The response indicates no relevant information was found
        - The response structure matches the expected format
    """
    mock_generate_response.return_value = {
        "response": "No relevant information found for the query.",
        "response_tokens_per_second": None
    }

    response = await generate_response(mock_query, [], **mock_config)

    assert isinstance(response, dict), "Response should be a dictionary"
    assert "response" in response, "Response should contain a 'response' key"
    assert "response_tokens_per_second" in response, "Response should contain token rate information"
    assert "no relevant information" in response["response"].lower(), "Response should indicate no context found"


@pytest.mark.asyncio
async def test_generate_response_high_temperature(
    mock_query, mock_chunks, mock_generate_response
):
    """Test the generate_response function with a high temperature setting.

    This test verifies that the function respects temperature settings
    and token limits while generating responses.

    Args:
        mock_query: The mock query input for testing
        mock_chunks: List of mock document chunks with id, title, chunk, and similarity_score
        mock_generate_response: Mock for the LLM response generation

    Assertions:
        - The response respects the max_tokens limit
        - The response structure matches the expected format
    """
    mock_generate_response.return_value = {
        "response": "Perovskites might revolutionize solar cells with surprising applications.",
        "response_tokens_per_second": 150.0
    }

    response = await generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=1.5
    )

    assert isinstance(response, dict), "Response should be a dictionary"
    assert "response" in response, "Response should contain a 'response' key"
    assert "response_tokens_per_second" in response, "Response should contain token rate information"
    assert len(response["response"].split()) <= 150, "Response should respect max_tokens limit"


@pytest.mark.asyncio
async def test_generate_response_long_query(mock_chunks, mock_generate_response):
    """Test generate_response with a long query string

    This test checks if the generate_response function can handle a long query
    without errors and produce a valid response.

    Mocks:
        mock_generate_response: Mocks the response from the LLM to return a
            predefined string containing 'Perovskites' and 'solar cells'.

    Assertions:
        - The response contains the keyword 'Perovskites'.
        - The response does not exceed the max_tokens limit.
    """
    # Simulate a long query by repeating the word 'Perovskites'
    long_query = "Perovskites " * 100

    # Mock the response expected from the LLM for the long query
    mock_generate_response.return_value = (
        "Perovskites are materials used in solar cells."
    )

    # Call the generate_response function with the long query
    response = await generate_response(
        long_query, mock_chunks, max_tokens=150, temperature=0.7
    )

    # Assertions
    assert isinstance(response, Dict), "Response should be a Dict."
    assert "response" in response, "Response should contain a 'response' key."
    assert "Perovskites" in response["response"], "Response should handle long query without error."
    assert len(response["response"].split()) <= 150, "Response should not exceed max_tokens."


@pytest.mark.asyncio
async def test_generate_response_with_multiple_chunks(
    mock_query, mock_chunks, mock_generate_response
):
    """Test generate_response with multiple chunks.

    This test verifies that the function can handle multiple chunks
    and produce a coherent response incorporating information from all chunks.

    Args:
        mock_query: The mock query input for testing
        mock_chunks: List of mock document chunks with id, title, chunk, and similarity_score
        mock_generate_response: Mock for the LLM response generation

    Assertions:
        - The response incorporates content from multiple chunks
        - The response structure matches the expected format
    """
    mock_generate_response.return_value = {
        "response": "Perovskites are used in solar cells and have unique properties. Their efficiency has recently improved.",
        "response_tokens_per_second": 200.0
    }

    response = await generate_response(
        mock_query, mock_chunks, max_tokens=150, temperature=0.7
    )

    assert isinstance(response, dict), "Response should be a dictionary"
    assert "response" in response, "Response should contain a 'response' key"
    assert "response_tokens_per_second" in response, "Response should contain token rate information"
    assert "used in solar cells" in response["response"].lower()
    assert "unique properties" in response["response"].lower()
    assert "efficiency has improved" in response["response"].lower()
