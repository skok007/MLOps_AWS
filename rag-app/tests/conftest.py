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
        {"id": 1, "title": "Test Paper 1", "chunk": "Perovskite materials are used in solar cells.", "similarity_score": 0.8},
        {"id": 2, "title": "Test Paper 2", "chunk": "Perovskites have unique electronic properties.", "similarity_score": 0.7},
        {"id": 3, "title": "Test Paper 3", "chunk": "The efficiency of perovskite solar cells has improved.", "similarity_score": 0.6},
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
    try:
        opik.configure(
            api_key=os.environ.get("OPIK_API_KEY"),
            workspace=os.environ.get("OPIK_WORKSPACE"),
            environment="test"
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
            cur.execute("""
                CREATE EXTENSION IF NOT EXISTS vector;
                
                CREATE TABLE IF NOT EXISTS papers (
                    id SERIAL PRIMARY KEY,
                    title TEXT NOT NULL,
                    summary TEXT NOT NULL,
                    chunk TEXT NOT NULL,
                    embedding vector(384)
                );
                
                -- Clear existing test data
                TRUNCATE TABLE papers;
                
                -- Insert test data
                INSERT INTO papers (title, summary, chunk, embedding) VALUES
                ('Test Paper 1', 'This paper discusses perovskite materials used in solar cells.', 
                 'Perovskite materials are used in solar cells.', 
                 array_fill(0.1, ARRAY[384])),
                ('Test Paper 2', 'This paper explores the unique electronic properties of perovskites.', 
                 'Perovskites have unique electronic properties.', 
                 array_fill(0.2, ARRAY[384])),
                ('Test Paper 3', 'This paper reports on improved efficiency of perovskite solar cells.', 
                 'The efficiency of perovskite solar cells has improved.', 
                 array_fill(0.3, ARRAY[384]));
            """)
            conn.commit()
    finally:
        conn.close()

    yield  # Allow tests to run

    # Cleanup after all tests
    conn = psycopg2.connect(**db_config)
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE papers;")
            conn.commit()
    finally:
        conn.close()
