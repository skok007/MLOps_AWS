import pytest
from server.src.services.retrieval_service import retrieve_top_k_chunks, get_db_connection, retrieve_relevant_chunks
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
    db_config = {
        "dbname": "test_db",
        "user": "test_user",
        "password": "test_password",
        "host": "localhost",
        "port": "5432"
    }
    
    # Mock the embedding model
    with patch("server.src.services.retrieval_service.embedding_model") as mock_embedding_model:
        # Set up mock embedding model to return a test embedding
        mock_embedding = [0.1] * 384  # 384-dimensional vector for testing
        mock_embedding_model.encode.return_value = mock_embedding
        
        # Mock the database connection and cursor
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        mock_conn.cursor.return_value = mock_cursor
        
        # Set up mock cursor to return test results
        mock_results = [
            (1, "Title 1", "Summary 1", "Chunk 1", 0.8),
            (2, "Title 2", "Summary 2", "Chunk 2", 0.7),
            (3, "Title 3", "Summary 3", "Chunk 3", 0.6)
        ]
        mock_cursor.fetchall.return_value = mock_results
        
        # Mock the database connection function
        with patch("server.src.services.retrieval_service.get_db_connection") as mock_get_db:
            mock_get_db.return_value = mock_conn
            
            # Call the function
            results = retrieve_top_k_chunks(query, k, db_config)
            
            # Verify the embedding model was called correctly
            mock_embedding_model.encode.assert_called_once_with(query, convert_to_tensor=False)
            
            # Verify database connection was established
            mock_get_db.assert_called_once_with(db_config)
            
            # Verify cursor operations
            mock_conn.cursor.assert_called_once()
            mock_cursor.execute.assert_called_once()
            mock_cursor.fetchall.assert_called_once()
            
            # Verify results
            assert len(results) == 3
            assert all(isinstance(result, dict) for result in results)
            assert all(
                key in result 
                for result in results 
                for key in ["id", "title", "summary", "chunk", "similarity_score"]
            )
            
            # Verify cleanup
            mock_cursor.close.assert_called_once()
            mock_conn.close.assert_called_once()
