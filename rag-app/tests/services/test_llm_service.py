import pytest
from server.src.services.llm_service import generate_response
from unittest.mock import patch, MagicMock

def test_generate_response():
    # Mock parameters
    query = "Test query"
    context = "Test context"
    
    # Mock the LLM
    with patch("server.src.services.llm_service.llm") as mock_llm:
        # Set up the mock LLM to return a test response
        mock_response = "This is a test response"
        mock_llm.invoke.return_value = mock_response
        
        # Call the function
        response = generate_response(query, context)
        
        # Verify the LLM was called correctly
        mock_llm.invoke.assert_called_once()
        
        # Verify the response
        assert isinstance(response, str)
        assert len(response) > 0 