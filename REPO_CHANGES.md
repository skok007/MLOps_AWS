# Critical Changes Required for oxford-genai-llmops-project

This document outlines the critical changes needed to make the [oxford-genai-llmops-project](https://github.com/AndyMc629/oxford-genai-llmops-project) repository work properly. These changes address compatibility issues, dependency problems, and configuration errors that prevent the application from running correctly.

The most important and signifficant structural change is that it uses OpenAI directly rather than Ollama

## 1. Python Version and Dependencies

### 1.1 Update Python Version Constraint

The original repository uses Python 3.12, but some dependencies don't work well with this version. Change the Python version constraint in `rag-app/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = ">=3.11,<3.13"  # Changed from "^3.12"
```

This change is necessary because `sentence-transformers` and `tensorflow` have compatibility issues with Python 3.12.

### 1.2 Update Database Driver

Replace `psycopg2` with `psycopg2-binary` in `rag-app/pyproject.toml` to avoid compilation issues:

```toml
[tool.poetry.dependencies]
psycopg2-binary = "^2.9.9"  # Changed from psycopg2
```

### 1.3 Create Custom requirements.txt

Create a new `rag-app/requirements.txt` file with specific versions to ensure compatibility:

```txt
sentence-transformers==2.2.2
tensorflow==2.15.0
psycopg2-binary==2.9.9
fastapi==0.109.2
uvicorn==0.27.1
python-dotenv==1.0.1
pydantic==2.6.1
streamlit==1.31.1
requests==2.31.0
```

This file is used for pip installation instead of poetry due to potential certificate issues with corporate proxies.

## 2. Embedding Model Changes

### 2.1 Update Embedding Model

Change the model in `rag-app/server/src/ingestion/embeddings.py` from `all-MiniLM-L6-v2` to `paraphrase-MiniLM-L6-v2`:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Changed from all-MiniLM-L6-v2
```

### 2.2 Standardize Embedding Model Across Application

Update the model in `rag-app/server/src/services/retrieval_service.py` to use the same model:

```python
def get_embeddings(self, text: str) -> List[float]:
    model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Changed from all-MiniLM-L6-v2
    embedding = model.encode(text)
    return embedding.tolist()  # Added .tolist() for pgvector compatibility
```

The `paraphrase-MiniLM-L6-v2` model is specifically designed for paraphrase detection and semantic similarity tasks, making it more suitable for this RAG application.

## 3. PostgreSQL Database Configuration

### 3.1 Create Custom Dockerfile for PostgreSQL

Create `rag-app/deploy/docker/postgres/pgvector2.Dockerfile` to handle certificate issues and build pgvector:

```dockerfile
# Stage 1: Certificate setup
FROM alpine:latest as cert-setup
RUN apk add --no-cache ca-certificates

# Stage 2: Build pgvector
FROM postgres:15-alpine as builder
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
RUN apk add --no-cache \
    git \
    make \
    gcc \
    libc-dev \
    postgresql-dev \
    && git clone --branch v0.5.1 https://github.com/pgvector/pgvector.git \
    && cd pgvector \
    && make \
    && make install

# Stage 3: Final image
FROM postgres:15-alpine
COPY --from=builder /usr/lib/postgresql/15/lib/vector.so /usr/lib/postgresql/15/lib/
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
RUN apk add --no-cache musl-locales musl-locales-lang tzdata
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
```

### 3.2 Fix Locale Issues in PostgreSQL Container

Add locale packages to the final PostgreSQL image and set environment variables for default locale:

```dockerfile
RUN apk add --no-cache musl-locales musl-locales-lang tzdata
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
```

This resolves the "no usable system locales were found" warning.

### 3.3 Update Docker Compose Configuration

Modify `rag-app/deploy/docker/postgres/docker-compose.yaml` to use the new Dockerfile:

```yaml
version: '3.8'
services:
  db:
    build:
      context: .
      dockerfile: pgvector2.Dockerfile
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    ports:
      - "${POSTGRES_PORT}:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 5s
      timeout: 5s
      retries: 5
```

### 3.4 Fix Database Connection from Devcontainer

Change database host from `localhost` to `host.docker.internal` in your environment configuration:

```env
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydb
POSTGRES_PORT=5432
POSTGRES_HOST=host.docker.internal  # Changed from localhost
```

This allows the application running in the devcontainer to connect to the PostgreSQL database running on the host machine.

## 4. Retrieval Service Fixes

### 4.1 Fix Embedding Handling

Ensure proper conversion of embeddings to list format in `rag-app/server/src/services/retrieval_service.py`:

```python
def get_embeddings(self, text: str) -> List[float]:
    embedding = model.encode(text)
    return embedding.tolist()  # Added .tolist() for pgvector compatibility
```

### 4.2 Improve Connection Handling

Add proper try/finally blocks to ensure database connections are closed in `rag-app/server/src/services/retrieval_service.py`:

```python
def get_db_connection():
    conn = None
    try:
        conn = psycopg2.connect(
            dbname=os.getenv("POSTGRES_DB"),
            user=os.getenv("POSTGRES_USER"),
            password=os.getenv("POSTGRES_PASSWORD"),
            host=os.getenv("POSTGRES_HOST"),
            port=os.getenv("POSTGRES_PORT")
        )
        return conn
    except Exception as e:
        if conn:
            conn.close()
        raise e
```

## 5. Generation Service Fixes

### 5.1 Add Error Handling for OpenAI API

Add fallback response in `rag-app/server/src/services/generation_service.py` when OpenAI API key is not available:

```python
def call_llm(prompt: str) -> str:
    try:
        # OpenAI API call
        return response.choices[0].text
    except Exception as e:
        return f"Error calling OpenAI API: {str(e)}"
```

## 6. Environment Configuration

### 6.1 Add Zscaler Certificate Support

Add Zscaler certificate to the devcontainer Dockerfile and configure environment variables to respect custom certificates:

```json
{
  "remoteEnv": {
    "REQUESTS_CA_BUNDLE": "/etc/ssl/certs/ca-certificates.crt",
    "NODE_EXTRA_CA_CERTS": "/etc/ssl/certs/ca-certificates.crt",
    "SSL_CERT_FILE": "/etc/ssl/certs/ca-certificates.crt",
    "PIP_CERT": "/etc/ssl/certs/ca-certificates.crt"
  }
}
```

## 7. Test Fixes

### 7.1 Fix Opik Configuration

Remove problematic `project_name` parameter from Opik configuration in both `main.py` and `conftest.py`:

```python
# Before
opik.configure(project_name="rag-app", environment="test")

# After
opik.configure()
```

### 7.2 Fix Test Database Setup

Add proper cleanup between test runs with `TRUNCATE TABLE papers` statement in `conftest.py`:

```python
@pytest.fixture(autouse=True)
def setup_database():
    conn = get_db_connection()
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE papers")
        conn.commit()
    finally:
        conn.close()
```

### 7.3 Fix Document Structure Inconsistencies

Update `mock_chunks` fixture in `conftest.py` to use "chunk" key instead of "text":

```python
@pytest.fixture
def mock_chunks():
    return [
        {
            "id": "1",
            "title": "Test Paper 1",
            "chunk": "This is a test chunk 1",
            "summary": "Test summary 1",
            "similarity_score": 0.9
        },
        {
            "id": "2",
            "title": "Test Paper 2",
            "chunk": "This is a test chunk 2",
            "summary": "Test summary 2",
            "similarity_score": 0.8
        }
    ]
```

### 7.4 Fix Database Schema Issues

Add missing "summary" column to test database schema:

```sql
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT,
    chunk TEXT,
    summary TEXT,
    embedding vector(384)
);
```

## 8. Streamlit Client Fixes

### 8.1 Fix Streamlit Client Response Handling

Update the Streamlit app to correctly parse the "response" key from the FastAPI backend:

```python
def query_fastapi(query, top_k=5, max_tokens=200, temperature=0.7):
    url = "http://localhost:8000/generate"
    params = {
        "query": query,
        "top_k": top_k,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    try:
        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {"error": str(e)}

# In the chat interface:
if "error" in response:
    answer = f"⚠️ Error: {response['error']}"
else:
    answer = response.get("response", "No response from server.")  # Changed from "answer" to "response"
```

## 9. Running the Application

After making these changes, you can run the application using the following commands:

```bash
# Build the database
cd rag-app
make build-db

# Download the data locally
make download-data

# Run the ingestion pipeline
make run-ingestion

# Run the FastAPI app
make run-app

# Run the tests
make test
```

These changes should resolve the major issues with the original repository and allow the application to run correctly.

## 10. Ollama Integration Changes

### 10.1 Generation Service Modifications

The following changes are required to switch from OpenAI to Ollama for text generation:

```python
# In rag-app/server/src/services/generation_service.py

# Remove OpenAI-specific imports and add Ollama client
from ollama import Client

def get_ollama_client() -> Client:
    """Create an Ollama client instance.
    
    Returns:
        Client: Configured Ollama client instance.
    """
    return Client(host='http://localhost:11434')

@opik.track
def call_llm(prompt: str, client: Optional[Client] = None) -> Dict[str, Union[str, float, None]]:
    """Call Ollama's API to generate a response.
    
    Args:
        prompt (str): The prompt to send to the language model.
        client (Optional[Client]): Ollama client instance.
        
    Returns:
        Dict[str, Union[str, float, None]]: Response containing generated text.
    """
    try:
        ollama_client = client or get_ollama_client()
        
        response = ollama_client.generate(
            model=settings.ollama_model,
            prompt=prompt,
            temperature=settings.temperature,
            num_predict=settings.max_tokens,
            top_p=settings.top_p,
        )
        
        return {
            "response": response['response'],
            "response_tokens_per_second": None  # Ollama doesn't provide token rate
        }
        
    except Exception as e:
        error_msg = (
            "I'm sorry, but I encountered an error while generating a response: "
            f"{str(e)}"
        )
        return {
            "response": error_msg,
            "response_tokens_per_second": None
        }
```

### 10.2 Configuration Updates

Update the configuration in `rag-app/server/src/config_loader.py`:

```python
# Remove OpenAI-specific config
# "openai_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
# "openai_api_key": os.getenv("OPENAI_API_KEY", ""),

# Add Ollama-specific config
"ollama_model": os.getenv("OLLAMA_MODEL", "llama2"),
"ollama_host": os.getenv("OLLAMA_HOST", "http://localhost:11434"),
```

### 10.3 Docker Configuration

Add Ollama service to `rag-app/deploy/docker/docker-compose.yaml`:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:11434/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  ollama_data:
```

### 10.4 Environment Variables

Update `.env` file to include Ollama-specific variables:

```env
# Remove OpenAI variables
# OPENAI_API_KEY=your-api-key
# OPENAI_MODEL=gpt-3.5-turbo

# Add Ollama variables
OLLAMA_MODEL=llama2
OLLAMA_HOST=http://localhost:11434
```

### 10.5 Dependencies Update

Update `rag-app/pyproject.toml` to replace OpenAI with Ollama client:

```toml
[tool.poetry.dependencies]
# Remove OpenAI
# openai = "^1.12.0"

# Add Ollama
ollama = "^0.1.6"
```

### 10.6 Test Updates

Update tests in `rag-app/tests/services/test_generation_service.py`:

```python
# Update mock responses to match Ollama format
mock_generate_response.return_value = {
    "response": "Test response from Ollama",
    "response_tokens_per_second": None
}
```

### 10.7 Documentation Updates

Update README.md to reflect Ollama usage:

1. Remove OpenAI setup instructions
2. Add Ollama installation and setup steps
3. Update API documentation for Ollama-specific parameters
4. Add troubleshooting section for common Ollama issues

### 10.8 Migration Steps

1. Install Ollama on the host machine
2. Pull the required model: `ollama pull llama2`
3. Start the Ollama service
4. Update environment variables
5. Run tests to verify the integration
6. Update deployment scripts to include Ollama service

### 10.9 Performance Considerations

1. Monitor local resource usage (CPU, memory) when running Ollama
2. Adjust model parameters based on available hardware
3. Consider using smaller models for development/testing
4. Implement proper error handling for local service availability

### 10.10 Security Implications

1. Remove OpenAI API key management
2. Add Ollama-specific security considerations
3. Update security documentation
4. Implement proper access controls for the Ollama service

