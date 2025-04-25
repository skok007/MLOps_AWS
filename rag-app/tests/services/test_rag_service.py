import pytest
from server.src.services.rag_service import process_query
from unittest.mock import patch, MagicMock

def test_process_query():
    # Mock parameters
    query = "Test query"
    
    # Mock the embedding service
    with patch("server.src.services.rag_service.get_embedding") as mock_get_embedding:
        # Set up the mock embedding service to return a test embedding
        mock_embedding = [0.1] * 384
        mock_get_embedding.return_value = mock_embedding
        
        # Mock the retrieval service
        with patch("server.src.services.rag_service.retrieve_relevant_chunks") as mock_retrieve:
            # Set up the mock retrieval service to return test chunks
            mock_chunks = [
                {"text": "Chunk 1", "metadata": {"source": "doc1"}},
                {"text": "Chunk 2", "metadata": {"source": "doc1"}},
                {"text": "Chunk 3", "metadata": {"source": "doc2"}}
            ]
            mock_retrieve.return_value = mock_chunks
            
            # Mock the LLM service
            with patch("server.src.services.rag_service.generate_response") as mock_generate:
                # Set up the mock LLM service to return a test response
                mock_response = "This is a test response"
                mock_generate.return_value = mock_response
                
                # Call the function
                response = process_query(query)
                
                # Verify the embedding service was called correctly
                mock_get_embedding.assert_called_once_with(query)
                
                # Verify the retrieval service was called correctly
                mock_retrieve.assert_called_once_with(query, k=3)
                
                # Verify the LLM service was called correctly
                mock_generate.assert_called_once_with(query, mock_chunks)
                
                # Verify the response
                assert isinstance(response, str)
                assert len(response) > 0 