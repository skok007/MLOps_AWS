import pytest
from server.src.services.retrieval_service import retrieve_top_k_chunks, get_db_connection
from dotenv import load_dotenv
import os
from unittest.mock import patch, MagicMock

# TODO: update to use BaseSettings implementation
load_dotenv()

DATA_PATH = os.getenv("DATA_PATH")

# Database connection configuration
db_config = {
    "dbname": os.environ.get("POSTGRES_DB", "test_db"),
    "user": os.environ.get("POSTGRES_USER", "test_user"),
    "password": os.environ.get("POSTGRES_PASSWORD", "test_password"),
    "host": os.environ.get("POSTGRES_HOST", "localhost"),
    "port": os.environ.get("POSTGRES_PORT", "5432"),
}

# Test function for the retrieval service
def test_retrieve_top_k_chunks():
    # Mock query and top_k value
    query = "perovskite"
    top_k = 5

    # Create a mock embedding model that returns a 384-dimensional vector
    mock_embedding = [0.1] * 384  # Create a 384-dimensional vector with all 0.1 values
    
    # Mock the embedding model's encode method
    with patch("server.src.services.retrieval_service.embedding_model") as mock_model, \
         patch("server.src.services.retrieval_service.get_db_connection") as mock_db_conn:
        
        # Set up the mock embedding model
        mock_model.encode.return_value = MagicMock(tolist=lambda: mock_embedding)
        
        # Set up the mock database connection
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        mock_db_conn.return_value = mock_conn
        
        # Set up the mock cursor to return some test data
        mock_cursor.fetchall.return_value = [
            (1, "Test Paper 1", "Summary 1", "Perovskite materials are used in solar cells.", 0.8),
            (2, "Test Paper 2", "Summary 2", "Perovskites have unique electronic properties.", 0.7),
            (3, "Test Paper 3", "Summary 3", "The efficiency of perovskite solar cells has improved.", 0.6)
        ]
        
        # Call the function
        try:
            documents = retrieve_top_k_chunks(query, top_k, db_config)

            # Verify the embedding model was called correctly
            mock_model.encode.assert_called_once_with(query, convert_to_tensor=False)
            
            # Verify the database connection was established correctly
            mock_db_conn.assert_called_once_with(db_config)
            
            # Verify the cursor was created and used correctly
            mock_conn.cursor.assert_called_once()
            
            # Verify the SQL query was executed correctly
            mock_cursor.execute.assert_called_once()
            
            # Verify the cursor was closed and the connection was closed
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()

            # Assertions for the returned documents
            assert isinstance(documents, list)
            assert len(documents) <= top_k

            for doc in documents:
                assert "id" in doc
                assert "title" in doc
                assert "summary" in doc
                assert "chunk" in doc
                assert "similarity_score" in doc
        except Exception as e:
            pytest.fail(f"Test failed with error: {str(e)}")

def test_retrieve_relevant_chunks():
    # Mock parameters
    query = "Test query"
    k = 3
    
    # Mock the vector store
    with patch("server.src.services.retrieval_service.vector_store") as mock_vector_store:
        # Set up the mock vector store to return test chunks
        mock_chunks = [
            {"text": "Chunk 1", "metadata": {"source": "doc1"}},
            {"text": "Chunk 2", "metadata": {"source": "doc1"}},
            {"text": "Chunk 3", "metadata": {"source": "doc2"}}
        ]
        mock_vector_store.similarity_search.return_value = mock_chunks
        
        # Call the function
        chunks = retrieve_relevant_chunks(query, k)
        
        # Verify the vector store was called correctly
        mock_vector_store.similarity_search.assert_called_once_with(query, k=k)
        
        # Verify the chunks
        assert len(chunks) == 3
        assert all(isinstance(chunk, dict) for chunk in chunks)
        assert all("text" in chunk and "metadata" in chunk for chunk in chunks)
