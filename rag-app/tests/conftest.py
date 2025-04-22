import pytest
from server.src.services.generation_service import generate_response
from unittest.mock import patch
import opik
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


@pytest.fixture
def mock_query():
    """Fixture to provide a sample query for testing."""
    return "Tell me about perovskites in solar cells."


@pytest.fixture
def mock_chunks():
    """Fixture to provide mock retrieved document chunks for generation tests."""
    return [
        {"text": "Perovskite materials are used in solar cells."},
        {"text": "Perovskites have unique electronic properties."},
        {"text": "The efficiency of perovskite solar cells has improved."},
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
    """Fixture that mocks the LLM generation process in the generate_response function."""
    with patch("server.src.services.generation_service.generate_response") as mock_gen:
        yield mock_gen


@pytest.fixture(autouse=True)
def configure_opik():
    """Configure Opik for testing environment."""
    opik.configure(
        api_key=os.environ.get("OPIK_API_KEY"),
        workspace=os.environ.get("OPIK_WORKSPACE"),
        environment="test"
    )
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
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    chunk TEXT NOT NULL,
                    embedding vector(384)
                );
                
                -- Insert some test data
                INSERT INTO papers (title, chunk, embedding) VALUES
                ('Test Paper 1', 'Perovskite materials are used in solar cells.', 
                 array_fill(0.1, ARRAY[384])),
                ('Test Paper 2', 'Perovskites have unique electronic properties.', 
                 array_fill(0.2, ARRAY[384])),
                ('Test Paper 3', 'The efficiency of perovskite solar cells has improved.', 
                 array_fill(0.3, ARRAY[384]));
            """)
            conn.commit()
    finally:
        conn.close()
