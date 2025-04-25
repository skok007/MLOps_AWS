import pytest
from server.src.services.embedding_service import get_embedding
from unittest.mock import patch, MagicMock

def test_get_embedding():
    # Mock parameters
    text = "Test text for embedding"
    
    # Mock the embedding model
    with patch("server.src.services.embedding_service.model") as mock_model:
        # Set up the mock model to return a test embedding
        mock_embedding = [0.1] * 384  # Assuming 384-dimensional embeddings
        mock_model.encode.return_value = mock_embedding
        
        # Call the function
        embedding = get_embedding(text)
        
        # Verify the model was called correctly
        mock_model.encode.assert_called_once_with(text)
        
        # Verify the embedding
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)
        assert all(0 <= x <= 1 for x in embedding)  # Assuming normalized embeddings 