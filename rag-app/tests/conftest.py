import os
import sys
import pytest
from unittest.mock import patch
import opik
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT

# Add the project root to the Python path
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
sys.path.insert(0, project_root)


@pytest.fixture
def mock_query():
    """Fixture to provide a sample query for testing."""
    return "Tell me about perovskites in solar cells."


@pytest.fixture
def mock_chunks():
    """Fixture to provide mock retrieved document chunks for generation tests."""
    return [
        {
            "id": 1, 
            "title": "Test Paper 1", 
            "chunk": "Perovskite materials are used in solar cells.", 
            "similarity_score": 0.8
        },
        {
            "id": 2, 
            "title": "Test Paper 2", 
            "chunk": "Perovskites have unique electronic properties.", 
            "similarity_score": 0.7
        },
        {
            "id": 3, 
            "title": "Test Paper 3", 
            "chunk": "The efficiency of perovskite solar cells has improved.", 
            "similarity_score": 0.6
        },
    ]


@pytest.fixture
def mock_config():
    """Fixture for mock configuration settings."""
    return {
        "max_tokens": 150,
        "temperature": 0.7,
    }


@pytest.fixture
def mock_generate_response():
    """Fixture that mocks the LLM generation process in the call_llm function."""
    with patch("server.src.services.generation_service.call_llm") as mock_llm:
        yield mock_llm


@pytest.fixture(autouse=True)
def configure_opik():
    """Configure Opik for testing environment."""
    try:
        opik.configure(
            api_key=os.environ.get("OPIK_API_KEY"),
            workspace=os.environ.get("OPIK_WORKSPACE")
        )
        print("Opik configuration successful for tests")
    except Exception as e:
        print(f"Warning: Opik configuration failed for tests: {str(e)}")
        print("Tests will continue without Opik tracking")
    yield


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Set up the test database with required schema and test data."""
    # Database connection configuration
    db_config = {
        "dbname": os.environ.get("POSTGRES_DB", "test_db"),
        "user": os.environ.get("POSTGRES_USER", "test_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", "test_password"),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }
    
    # Connect to PostgreSQL server
    conn = psycopg2.connect(
        dbname="postgres",
        user=db_config["user"],
        password=db_config["password"],
        host=db_config["host"],
        port=db_config["port"]
    )
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    
    try:
        # Create test database if it doesn't exist
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (db_config["dbname"],))
            if not cur.fetchone():
                cur.execute(f"CREATE DATABASE {db_config['dbname']}")
    finally:
        conn.close()
    
    # Connect to the test database
    conn = psycopg2.connect(**db_config)
    try:
        with conn.cursor() as cur:
            # Create the papers table with vector support
            # Using 384 dimensions to match the paraphrase-MiniLM-L6-v2 model
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    chunk TEXT NOT NULL,
                    embedding vector(384)
                );
            """)
            
            # Create a 384-dimensional vector for testing
            # We'll use a simple pattern: [0.1, 0.2, 0.3, ..., 0.1, 0.2, 0.3]
            # This creates a 384-dimensional vector with repeating values
            vector_values = []
            for i in range(384):
                vector_values.append(str(0.1 + (i % 3) * 0.1))
            vector_str = f"[{', '.join(vector_values)}]"
            
            # Insert test data with the correct vector dimensions
            cur.execute(f"""
                INSERT INTO papers (title, summary, chunk, embedding)
                VALUES 
                    ('Test Paper 1', 'Summary of test paper 1', 'Perovskite materials are used in solar cells.', '{vector_str}'::vector),
                    ('Test Paper 2', 'Summary of test paper 2', 'Perovskites have unique electronic properties.', '{vector_str}'::vector),
                    ('Test Paper 3', 'Summary of test paper 3', 'The efficiency of perovskite solar cells has improved.', '{vector_str}'::vector)
                ON CONFLICT DO NOTHING;
            """)
            
            conn.commit()
    finally:
        conn.close()
    
    yield
    
    # Clean up after tests
    conn = psycopg2.connect(**db_config)
    try:
        with conn.cursor() as cur:
            cur.execute("DROP TABLE IF EXISTS papers;")
            conn.commit()
    finally:
        conn.close()
