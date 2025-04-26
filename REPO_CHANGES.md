# Critical Changes Required for oxford-genai-llmops-project

This document outlines the critical changes needed to make the [oxford-genai-llmops-project](https://github.com/AndyMc629/oxford-genai-llmops-project) repository work properly. These changes address compatibility issues, dependency problems, and configuration errors that prevent the application from running correctly.

## 1. Zscaler and Environment Configuration

### 1.1 Add Zscaler Certificate Support

**Why**: Corporate environments often use Zscaler for security, which requires proper certificate configuration for all network requests. The certificate needs to be trusted by all components of the system.

1. Add Zscaler certificate to the devcontainer Dockerfile:
```dockerfile
# ✅ Trust Zscaler cert early (use .crt extension for update-ca-certificates)
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
```

2. Add certificate to PostgreSQL Dockerfile:
```dockerfile
# Stage 1: Certificate setup
FROM alpine:latest as cert-setup
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apk add --no-cache ca-certificates && update-ca-certificates
```

3. Add certificate to all service Dockerfiles that make network requests:
```dockerfile
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apt-get update && apt-get install -y ca-certificates && update-ca-certificates
```

4. Update Makefile to handle certificate in build commands:
```makefile
build-db:
	cp ZscalerRootCertificate-2048-SHA256.pem deploy/docker/postgres/
	docker-compose -f deploy/docker/postgres/docker-compose.yaml build

build-app:
	cp ZscalerRootCertificate-2048-SHA256.pem deploy/docker/app/
	docker-compose -f deploy/docker/app/docker-compose.yaml build
```

5. Configure environment variables to respect custom certificates:
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

6. Add certificate to Python environment:
```python
import os
import certifi

# Set certificate path for requests
os.environ['REQUESTS_CA_BUNDLE'] = certifi.where()
```

7. Update Docker Compose files to mount certificate:
```yaml
services:
  app:
    volumes:
      - ./ZscalerRootCertificate-2048-SHA256.pem:/usr/local/share/ca-certificates/zscaler.crt:ro
```

### 1.2 Create Custom PostgreSQL Dockerfile

**Why**: Corporate environments often block direct access to GitHub and other external resources, requiring a custom build process that handles certificates properly.

Create `rag-app/deploy/docker/postgres/pgvector2.Dockerfile`:

```dockerfile
# Stage 1: Certificate setup
FROM alpine:latest as cert-setup
COPY ZscalerRootCertificate-2048-SHA256.pem /usr/local/share/ca-certificates/zscaler.crt
RUN apk add --no-cache ca-certificates && update-ca-certificates

# Stage 2: Build pgvector
FROM postgres:15-alpine as builder
COPY --from=cert-setup /etc/ssl/certs/ca-certificates.crt /etc/ssl/certs/
COPY --from=cert-setup /usr/local/share/ca-certificates/zscaler.crt /usr/local/share/ca-certificates/
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
COPY --from=cert-setup /usr/local/share/ca-certificates/zscaler.crt /usr/local/share/ca-certificates/
RUN apk add --no-cache musl-locales musl-locales-lang tzdata && update-ca-certificates
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
```

### 1.3 Update Makefile for Certificate Handling

**Why**: The build process needs to handle Zscaler certificates properly across all services and ensure they are available during build time.

Update `rag-app/Makefile`:

```makefile
# Define certificate path
CERT_PATH=ZscalerRootCertificate-2048-SHA256.pem

# Build the postgres db with certificate
build-db:
	cp $(CERT_PATH) deploy/docker/postgres/
	docker compose --env-file .env -f deploy/docker/postgres/docker-compose.yaml up --build

# Build the app with certificate
build-app:
	cp $(CERT_PATH) deploy/docker/app/
	docker compose --env-file .env -f deploy/docker/app/docker-compose.yaml up --build

# Clean up certificates
clean-certs:
	rm -f deploy/docker/postgres/$(CERT_PATH)
	rm -f deploy/docker/app/$(CERT_PATH)

# Update clean target to include certificates
clean: clean-certs
	find . -type f -name '*.pyc' -delete
```

This ensures that:
1. The Zscaler certificate is copied to the appropriate directories before building
2. Certificates are properly cleaned up after use
3. Build commands handle certificates consistently across services

## 2. Python Version and Dependencies

### 4.1 Update Python Version Constraint

**Why**: Some dependencies have compatibility issues with Python 3.12, requiring a more flexible version constraint.

Change in `rag-app/pyproject.toml`:

```toml
[tool.poetry.dependencies]
python = ">=3.11,<3.13"  # Changed from "^3.12"
```

### 4.2 Update Database Driver

**Why**: `psycopg2` requires compilation which can fail in corporate environments, while `psycopg2-binary` provides pre-compiled binaries.

```toml
[tool.poetry.dependencies]
psycopg2-binary = "^2.9.9"  # Changed from psycopg2
```

### 4.3 Create Custom requirements.txt

**Why**: Corporate environments often have issues with poetry's certificate handling, making pip with requirements.txt more reliable.

Create `rag-app/requirements.txt`:

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

## 3. OpenAI Integration

### 3.1 Why Move from Ollama to OpenAI

**Why**: The original repository used Ollama for local LLM serving, but several factors make OpenAI a better choice for this project:

1. **Reliability and Consistency**: 
   - OpenAI's API provides consistent response quality and uptime
   - Local models through Ollama can be affected by hardware limitations and resource constraints
   - OpenAI's models are regularly updated and optimized

2. **Performance and Scalability**:
   - OpenAI's infrastructure handles high concurrency better than local Ollama instances
   - No need to manage local GPU resources or model loading times
   - Better handling of long context windows and complex queries

3. **Development and Testing**:
   - OpenAI's API is more suitable for development and testing environments
   - Consistent behavior across different development machines
   - No need to download and manage large model files locally

4. **Integration Complexity**:
   - OpenAI's API is simpler to integrate and maintain
   - Fewer moving parts compared to managing a local Ollama service
   - Better error handling and rate limiting

### 3.2 Implementation Changes

The following files needed to be modified to migrate from Ollama to OpenAI:

1. **Core Service Files**:
   - `rag-app/server/src/services/generation_service.py` - Main service file that handles LLM calls
   - `rag-app/server/src/controllers/generation.py` - Controller that uses the generation service
   - `rag-app/server/src/services/query_expansion_service.py` - Uses the generation service for query expansion

2. **Configuration Files**:
   - `rag-app/server/src/config_loader.py` - Added OpenAI configuration settings
   - `rag-app/server/config/rag.yaml` - Updated generation model configuration
   - `rag-app/pyproject.toml` - Updated dependencies (removed Ollama, added OpenAI)

3. **Docker and Deployment Files**:
   - `rag-app/deploy/docker/docker-compose.yaml` - Removed Ollama service configuration
   - `rag-app/Makefile` - Removed Ollama-related commands
   - `rag-app/deploy/scripts/cleanup_ollama.sh` - Cleanup script for Ollama (can be removed)

4. **Test Files**:
   - `rag-app/tests/services/test_generation_service.py` - Updated tests for OpenAI integration

5. **Environment and Documentation**:
   - `.env` and `.env.example` - Updated environment variables
   - `README.md` - Updated setup and usage instructions
   - `RAG_IMPLEMENTATION_README.md` - Updated implementation details

The specific changes required for each file are detailed below:

#### 1. Core Service Files

##### a. Generation Service (`rag-app/server/src/services/generation_service.py`)

The main service file that handles LLM calls needed significant changes to migrate from Ollama to OpenAI:

```python
import boto3
from botocore.exceptions import ClientError
import os
from typing import List, Dict, Union
from server.src.models.document import RetrievedDocument
from server.src.config import Settings
from fastapi import Depends
import requests
import json
from server.src.config import settings
import opik
import openai
from openai import OpenAI

# Original Ollama client setup (commented out)
# from ollama import Ollama
# client = Ollama(host=settings.ollama_host)

# New OpenAI client setup
client = OpenAI()

@opik.track
def call_llm(prompt: str) -> Union[Dict, None]:
    """Call OpenAI's API to generate a response."""
    try:
        # Original Ollama implementation (commented out)
        # response = client.generate(
        #     model=settings.ollama_model,
        #     prompt=prompt,
        #     temperature=settings.temperature,
        #     max_tokens=settings.max_tokens,
        # )
        # data = {
        #     "response": response.response,
        #     "response_tokens_per_second": response.tokens_per_second
        # }

        # New OpenAI implementation
        response = client.chat.completions.create(
            model=settings.openai_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=settings.temperature,
            max_tokens=settings.max_tokens,
            top_p=settings.top_p,
        )

        print("Successfully generated response")
        data = {"response": response.choices[0].message.content}
        data["response_tokens_per_second"] = (
            (response.usage.total_tokens / response.usage.completion_tokens)
            if hasattr(response, "usage")
            else None
        )
        print(f"call_llm returning {data}")
        print(f"data.response = {data['response']}")
        return data

    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

@opik.track
async def generate_response(
    query: str,
    chunks: List[Dict],
    max_tokens: int = 200,
    temperature: float = 0.7,
) -> Dict:
    """
    Generate a response using OpenAI's API.

    Args:
        query (str): The user query.
        context (List[Dict]): The list of documents retrieved from the retrieval service.
        max_tokens (int): The maximum number of tokens to generate in the response.
        temperature (float): Sampling temperature for the model.
    """
    QUERY_PROMPT = """
    You are a helpful AI language assistant, please use the following context to answer the query. Answer in English.
    Context: {context}
    Query: {query}
    Answer:
    """
    # Concatenate documents' summaries as the context for generation
    context = "\n".join([chunk["chunk"] for chunk in chunks])
    prompt = QUERY_PROMPT.format(context=context, query=query)
    print(f"calling call_llm ...")
    response = call_llm(prompt)
    print(f"generate_response returning {response}")
    return response
```

Key changes in the generation service:
1. Removed Ollama client setup and replaced with OpenAI client
2. Updated the `call_llm` function to use OpenAI's chat completions API
3. Modified response handling to match OpenAI's response format
4. Added token usage calculation from OpenAI's response
5. Updated docstring in `generate_response` to reflect OpenAI usage
6. Improved error handling for OpenAI-specific errors

##### b. Generation Controller (`rag-app/server/src/controllers/generation.py`)

The Generation Controller is already using the OpenAI implementation. No changes are needed as it relies on the `generate_response` function from the generation service, which has been updated to use OpenAI.

##### c. Query Expansion Service (`rag-app/server/src/services/query_expansion_service.py`)

The Query Expansion Service is already using the OpenAI implementation through the `call_llm` function from the generation service. No changes are needed as it relies on the updated generation service.

#### 2. Configuration Files

##### a. Config Loader (`rag-app/server/src/config_loader.py`)

The configuration loader needs to be updated to include OpenAI-specific settings:

```python
# Original Ollama-specific config (commented out)
# ollama_model: str = os.getenv("OLLAMA_MODEL", "llama2")
# ollama_host: str = os.getenv("OLLAMA_HOST", "http://localhost:11434")

# New OpenAI-specific config
openai_model: str = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
```

Key changes:
1. Removed Ollama-specific configuration settings
2. Added OpenAI model and API key configuration
3. Updated default model to use OpenAI's GPT-3.5 Turbo

##### b. RAG Configuration (`rag-app/server/config/rag.yaml`)

The RAG configuration file needs to be updated to use OpenAI instead of Ollama:

```yaml
# Original Ollama configuration (commented out)
# generation:
#   model: "tinyllama"
#   temperature: 0.7

# New OpenAI configuration
generation:
  model: "gpt-3.5-turbo"
  temperature: 0.7
  max_tokens: 200
  top_p: 0.95
```

Key changes:
1. Updated model name from "tinyllama" to "gpt-3.5-turbo"
2. Added additional OpenAI-specific parameters (max_tokens, top_p)
3. Kept temperature setting for consistency

##### c. Dependencies (`rag-app/pyproject.toml`)

The project dependencies need to be updated to remove Ollama and add OpenAI:

```toml
# Original Ollama dependency (commented out)
# ollama = "^0.1.6"

# New OpenAI dependency
openai = "^1.12.0"
```

Key changes:
1. Removed Ollama dependency
2. Added OpenAI dependency with appropriate version constraint

#### 3. Docker and Deployment Files

##### a. Docker Compose (`rag-app/deploy/docker/docker-compose.yaml`)

The Docker Compose file needs to be updated to remove the Ollama service:

```yaml
# Original Ollama service (commented out)
# ollama:
#   image: ollama/ollama:latest
#   ports:
#     - "11434:11434"
#   volumes:
#     - ollama_data:/root/.ollama

# Updated app service with OpenAI environment variables
app:
  environment:
    - OPENAI_API_KEY=${OPENAI_API_KEY}
    - OPENAI_MODEL=${OPENAI_MODEL}
```

Key changes:
1. Removed Ollama service configuration
2. Added OpenAI environment variables to the app service
3. Updated service dependencies to remove Ollama

##### b. Makefile (`rag-app/Makefile`)

The Makefile needs to be updated to remove Ollama-related commands:

```makefile
# Original Ollama commands (commented out)
# start-ollama:
#   docker-compose -f deploy/docker/ollama/docker-compose.yaml up -d

# New OpenAI-related commands
setup-openai:
  @echo "Setting up OpenAI API key..."
  @if [ -z "$$OPENAI_API_KEY" ]; then \
    echo "OPENAI_API_KEY is not set. Please set it in your environment or .env file."; \
    exit 1; \
  fi
```

Key changes:
1. Removed Ollama start/stop commands
2. Added OpenAI setup command to verify API key
3. Updated build process to remove Ollama dependencies

##### c. Cleanup Script (`rag-app/deploy/scripts/cleanup_ollama.sh`)

This script can be removed as it's no longer needed:

```bash
# This script can be removed as Ollama is no longer used
# #!/bin/bash
# 
# # Stop and remove Ollama container
# docker-compose -f deploy/docker/ollama/docker-compose.yaml down
# 
# # Remove Ollama data volume
# docker volume rm rag-app_ollama_data
```

#### 4. Test Files

##### a. Generation Service Tests (`rag-app/tests/services/test_generation_service.py`)

The tests need to be updated to use OpenAI instead of Ollama:

```python
# Original Ollama test (commented out)
# def test_call_ollama():
#     mock_response = MagicMock()
#     mock_response.response = "Test response"
#     mock_response.tokens_per_second = 10.0
#     
#     with patch('ollama.Ollama.generate', return_value=mock_response):
#         result = call_llm("Test prompt")
#         assert result["response"] == "Test response"
#         assert result["response_tokens_per_second"] == 10.0

# New OpenAI test
def test_call_openai():
    mock_response = MagicMock()
    mock_response.choices = [
        MagicMock(message=MagicMock(content="Test response"))
    ]
    mock_response.usage = MagicMock(total_tokens=100, completion_tokens=50)
    
    with patch('openai.ChatCompletion.create', return_value=mock_response):
        result = call_llm("Test prompt")
        assert result["response"] == "Test response"
        assert result["response_tokens_per_second"] == 2.0
```

Key changes:
1. Updated test mocks to match OpenAI's response format
2. Modified assertions to check for OpenAI-specific response structure
3. Updated token usage calculation tests

#### 5. Environment and Documentation

##### a. Environment Variables (`.env` and `.env.example`)

The environment variables need to be updated to use OpenAI instead of Ollama:

```env
# Original Ollama variables (commented out)
# OLLAMA_MODEL=llama2
# OLLAMA_HOST=http://localhost:11434

# New OpenAI variables
OPENAI_API_KEY=your-api-key
OPENAI_MODEL=gpt-3.5-turbo
```

Key changes:
1. Removed Ollama-specific environment variables
2. Added OpenAI API key and model variables
3. Updated example values to use OpenAI defaults

##### b. README (`README.md`)

The README needs to be updated to reflect the OpenAI integration:

```markdown
# Original Ollama setup (commented out)
# ## Setup Ollama
# 
# 1. Install Ollama: [Ollama Installation Guide](https://ollama.ai/download)
# 2. Pull the model: `ollama pull llama2`
# 3. Start Ollama: `ollama serve`

# New OpenAI setup
## Setup OpenAI

1. Get an API key from [OpenAI](https://platform.openai.com/api-keys)
2. Add your API key to the `.env` file: `OPENAI_API_KEY=your-api-key`
3. Choose a model: `OPENAI_MODEL=gpt-3.5-turbo` (default)
```

Key changes:
1. Removed Ollama setup instructions
2. Added OpenAI API key setup instructions
3. Updated model selection guidance

##### c. Implementation README (`RAG_IMPLEMENTATION_README.md`)

The implementation README needs to be updated to reflect the OpenAI integration:

```markdown
# Original Ollama implementation (commented out)
# The RAG application uses Ollama to serve local LLMs for text generation.
# The generation service communicates with Ollama via its REST API.

# New OpenAI implementation
The RAG application uses OpenAI's API for text generation.
The generation service communicates with OpenAI via its official Python client.
```

Key changes:
1. Updated implementation details to reflect OpenAI usage
2. Modified architecture description to include OpenAI integration
3. Updated configuration section to show OpenAI settings
</code_block_to_apply_changes_from>

### 3.3 Implementation Steps

To implement the migration from Ollama to OpenAI in this repository, follow these specific steps:

1. **Update Dependencies**:
   ```bash
   # Remove Ollama dependency
   poetry remove ollama
   
   # Add OpenAI dependency
   poetry add openai
   ```

2. **Update Environment Variables**:
   Add the following variables to your `.env` file:
   ```
   OPENAI_API_KEY=your-api-key
   OPENAI_MODEL=gpt-3.5-turbo
   ```

3. **Update Configuration Files**:
   - Modify `rag-app/server/src/config_loader.py` to include OpenAI settings
   - Update `rag-app/server/config/rag.yaml` to use OpenAI configuration
   - Update `rag-app/pyproject.toml` to include OpenAI dependency

4. **Update Core Service Files**:
   - Modify `rag-app/server/src/services/generation_service.py` to use OpenAI API
   - No changes needed for `rag-app/server/src/controllers/generation.py` and `rag-app/server/src/services/query_expansion_service.py` as they rely on the generation service

5. **Update Docker and Deployment Files**:
   - Remove Ollama service from `rag-app/deploy/docker/docker-compose.yaml`
   - Update `rag-app/Makefile` to remove Ollama-related commands
   - Remove `rag-app/deploy/scripts/cleanup_ollama.sh` if it exists

6. **Update Test Files**:
   - Update `rag-app/tests/services/test_generation_service.py` to use OpenAI mocks

7. **Update Documentation**:
   - Update `.env.example` to include OpenAI variables
   - Update `README.md` to reflect OpenAI integration
   - Update `RAG_IMPLEMENTATION_README.md` to describe OpenAI implementation

8. **Test the Changes**:
   ```bash
   # Run tests to ensure everything works correctly
   make test
   
   # Start the application to verify the changes
   make run-app
   ```

### 3.4 Troubleshooting

If you encounter issues during the migration, here are some common problems and solutions:

1. **OpenAI API Key Issues**:
   - Ensure your API key is correctly set in the `.env` file
   - Verify that the API key has sufficient permissions
   - Check if you've reached your API usage limits

2. **Model Configuration Issues**:
   - Ensure the model name is correct (e.g., "gpt-3.5-turbo")
   - Verify that the model parameters (temperature, max_tokens, top_p) are within acceptable ranges

3. **Response Format Issues**:
   - If responses are not in the expected format, check the OpenAI API response structure
   - Ensure the code correctly extracts the response content from `response.choices[0].message.content`

4. **Token Usage Calculation Issues**:
   - If token usage calculation is incorrect, verify that the response includes usage information
   - Check the calculation logic in the `call_llm` function

5. **Docker Configuration Issues**:
   - Ensure environment variables are correctly passed to the Docker containers
   - Verify that the OpenAI API key is available in the container environment

If you need to revert to Ollama for any reason, you can restore the original code from your version control system or follow these steps:

1. **Restore Dependencies**:
   ```bash
   poetry remove openai
   poetry add ollama
   ```

2. **Restore Environment Variables**:
   Remove the OpenAI variables from your `.env` file and add back the Ollama variables:
   ```
   OLLAMA_MODEL=llama2
   OLLAMA_HOST=http://localhost:11434
   ```

3. **Restore Code Changes**:
   Revert the changes made to the files listed in section 3.2, restoring the original Ollama implementation.

## 4. Environment Variables Configuration

### 4.1 Database Connection Configuration

**Why**: Proper database connection requires specific environment variables for security and configuration.

```env
POSTGRES_USER=myuser
POSTGRES_PASSWORD=mypassword
POSTGRES_DB=mydb
POSTGRES_PORT=5432
POSTGRES_HOST=host.docker.internal  # Changed from localhost for devcontainer compatibility
```

### 4.2 Devcontainer Configuration

**Why**: Devcontainer needs specific environment variables to handle corporate proxy settings and certificates.

```json
{
  "remoteEnv": {
    "HTTP_PROXY": "http://proxy.company.com:8080",
    "HTTPS_PROXY": "http://proxy.company.com:8080",
    "NO_PROXY": "localhost,127.0.0.1"
  }
}
```

## 5. Code Adjustments

### 5.1 Embedding Model Changes

**Why**: The `paraphrase-MiniLM-L6-v2` model is specifically designed for semantic similarity tasks, making it more suitable for RAG applications.

Update in `rag-app/server/src/ingestion/embeddings.py`:

```python
from sentence_transformers import SentenceTransformer

model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Changed from all-MiniLM-L6-v2
```

### 5.2 PostgreSQL Database Configuration

**Why**: Proper locale settings and pgvector installation are required for the database to function correctly.

Add to PostgreSQL Dockerfile:

```dockerfile
RUN apk add --no-cache musl-locales musl-locales-lang tzdata
ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
```

### 5.3 Retrieval Service Fixes

**Why**: Proper connection handling and embedding format conversion are required for reliable database operations.

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

### 5.4 Generation Service Fixes

**Why**: Proper error handling and response formatting are required for reliable API interactions.

```python
def call_llm(prompt: str) -> Dict[str, Union[str, float, None]]:
    try:
        # API call implementation
        return {
            "response": response.choices[0].text,
            "response_tokens_per_second": None
        }
    except Exception as e:
        return {
            "response": f"Error: {str(e)}",
            "response_tokens_per_second": None
        }
```

### 5.5 Streamlit Client Updates

**Why**: The Streamlit client requires significant updates for several critical reasons:

1. **Corporate Environment Compatibility**:
   - The original client doesn't handle corporate proxy and certificate requirements
   - Network requests need proper certificate verification for Zscaler
   - Error handling needs to be more robust for corporate network issues

2. **OpenAI Integration Requirements**:
   - The response format from OpenAI differs from Ollama:
     * OpenAI's chat completions API returns responses in a structured format with `choices[0].message.content`
     * Ollama used a simpler format with direct response text
     * The client needs to handle both successful responses and API-specific errors
   - Need to handle OpenAI-specific error cases:
     * Rate limiting errors (429)
     * Authentication errors (401)
     * Invalid request errors (400)
     * Server errors (500)
     * Token limit exceeded errors
   - Response structure needs to be consistent with OpenAI's format:
     * OpenAI responses include metadata like token usage
     * Error responses have specific error codes and messages
     * The client needs to maintain compatibility with the FastAPI backend's OpenAI integration
   - Configuration parameters need to match OpenAI's API:
     * Temperature controls response randomness
     * Max tokens limits response length
     * Top-k affects response diversity
     * These parameters need to be exposed to users for fine-tuning

Changes Required:

1. **API Request Handling**:
```python
def query_fastapi(query: str, top_k: int = 5, max_tokens: int = 200, temperature: float = 0.7) -> Dict[str, Any]:
    """Send a query to the FastAPI backend and return the response."""
    url = "http://localhost:8000/generate"
    params = {
        "query": query,
        "top_k": top_k,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }
    
    try:
        # Add certificate verification for corporate environments
        response = requests.get(
            url, 
            params=params,
            verify=os.getenv('REQUESTS_CA_BUNDLE', True)
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        return {
            "error": f"API request failed: {str(e)}",
            "response": None
        }
    except Exception as e:
        return {
            "error": f"Unexpected error: {str(e)}",
            "response": None
        }
```
This change:
- Adds proper type hints for better code maintainability
- Implements corporate certificate verification
- Provides more detailed error handling
- Returns consistent response structure

2. **User Interface Enhancements**:
```python
# Add configuration sidebar
with st.sidebar:
    st.title("Configuration")
    temperature = st.slider("Temperature", 0.0, 1.0, 0.7, 0.1)
    max_tokens = st.slider("Max Tokens", 100, 1000, 200, 50)
    top_k = st.slider("Top K Results", 1, 10, 5, 1)
```
This change:
- Adds user-configurable parameters
- Provides visual feedback for settings
- Makes the interface more interactive

3. **Response Handling**:
```python
# Handle response
if "error" in response and response["error"]:
    answer = f"⚠️ Error: {response['error']}"
else:
    answer = response.get("response", "No response from server.")

# Display bot response
with st.chat_message("assistant"):
    st.markdown(answer)
```
This change:
- Properly handles OpenAI response format
- Provides clear error messages
- Maintains consistent chat history

4. **Loading State**:
```python
# Get response from FastAPI backend
with st.spinner("Thinking..."):
    response = query_fastapi(
        query,
        top_k=top_k,
        max_tokens=max_tokens,
        temperature=temperature
    )
```
This change:
- Adds visual feedback during API calls
- Improves user experience
- Makes the interface feel more responsive

These changes ensure:
1. Reliable operation in corporate environments
2. Consistent handling of OpenAI responses
3. Better user experience with configuration options
4. More robust error handling
5. Improved code maintainability
6. Better visual feedback for users

## 6. Test Improvements

**Why**: The test suite requires significant improvements to ensure reliability, maintainability, and compatibility with the new OpenAI integration. The issues can be categorized into three main areas:

1. **Configuration and Environment Issues**:
   - Opik configuration was causing test failures in corporate environments
   - Database setup lacked proper isolation between test runs
   - Environment variables weren't properly managed
   - Corporate proxy and certificate settings weren't handled correctly

2. **Test Structure and Coverage Gaps**:
   - Inconsistent document structures across test fixtures
   - Missing tests for error handling and edge cases
   - Lack of integration tests for end-to-end workflows
   - Insufficient test coverage for OpenAI integration

3. **Maintenance and Documentation Problems**:
   - Poor test documentation made maintenance difficult
   - Test dependencies were outdated and incompatible
   - Test results weren't properly formatted for CI/CD pipelines
   - No clear test patterns or conventions

The following changes address these issues systematically:

### 6.1 Fix Opik Configuration

**Change**: Remove the `project_name` parameter from Opik configuration to prevent test failures in corporate environments.

```python
# Before
opik.configure(project_name="rag-app", environment="test")

# After
opik.configure()
```

**Impact**: This change resolves environment isolation issues, improves corporate environment compatibility, and eliminates cryptic error messages that were masking actual test failures.

### 6.2 Fix Test Database Setup

**Change**: Add proper database cleanup between test runs to prevent test interference.

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

**Impact**: This change ensures test isolation, prevents resource leaks, maintains data consistency, and improves test performance by eliminating the need for manual cleanup.

### 6.3 Fix Document Structure Inconsistencies

**Change**: Standardize document structure across test fixtures to ensure consistency.

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
        }
    ]
```

**Impact**: This change eliminates data format inconsistencies, simplifies test maintenance, improves error diagnosis, and enables proper integration testing.

### 6.4 Improve Test Database Configuration

**Change**: Enhance database configuration with better error handling, isolation, and environment management.

1. **Update Database Connection Configuration**:
```python
@pytest.fixture(scope="session")
def db_config():
    """Provide database configuration for tests."""
    return {
        "dbname": os.environ.get("POSTGRES_DB", "test_db"),
        "user": os.environ.get("POSTGRES_USER", "test_user"),
        "password": os.environ.get("POSTGRES_PASSWORD", "test_password"),
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": os.environ.get("POSTGRES_PORT", "5432"),
    }
```

2. **Add Database Cleanup**:
```python
@pytest.fixture(autouse=True)
def cleanup_database(db_config):
    """Clean up database after each test."""
    conn = get_db_connection(db_config)
    try:
        with conn.cursor() as cur:
            cur.execute("TRUNCATE TABLE papers CASCADE")
        conn.commit()
    finally:
        conn.close()
```

3. **Improve Test Data Management**:
```python
@pytest.fixture
def test_papers():
    """Provide consistent test data for all tests."""
    return [
        {
            "id": 1,
            "title": "Test Paper 1",
            "summary": "Summary of test paper 1",
            "chunk": "Perovskite materials are used in solar cells.",
            "embedding": [0.1] * 384  # 384-dimensional vector for testing
        },
        # Add more test papers as needed
    ]
```

**Impact**: These changes improve connection management, enhance environment configuration, provide better error handling, optimize test data management, and ensure corporate environment compatibility.

### 6.5 Enhance Test Coverage

**Change**: Add tests for error handling, edge cases, and integration scenarios.

1. **Add Error Handling Tests**:
```python
@pytest.mark.asyncio
async def test_generate_response_error_handling(mock_query, mock_chunks, mock_generate_response):
    """Test error handling in generate_response function."""
    mock_generate_response.side_effect = Exception("Test error")
    
    response = await generate_response(
        query=mock_query,
        chunks=mock_chunks,
        max_tokens=150,
        temperature=0.7
    )
    
    assert "error" in response
    assert "Test error" in response["error"]
```

2. **Add Edge Case Tests**:
```python
@pytest.mark.asyncio
async def test_generate_response_edge_cases(mock_query, mock_generate_response):
    """Test edge cases in generate_response function."""
    # Test with empty query
    response = await generate_response("", [], max_tokens=150, temperature=0.7)
    assert "error" in response
    
    # Test with very long query
    long_query = "test " * 1000
    response = await generate_response(long_query, [], max_tokens=150, temperature=0.7)
    assert "error" in response
```

3. **Add Integration Tests**:
```python
@pytest.mark.integration
async def test_end_to_end_flow(mock_query, db_config):
    """Test the complete flow from query to response."""
    # Test retrieval
    chunks = retrieve_top_k_chunks(mock_query, top_k=5, db_config=db_config)
    assert len(chunks) > 0
    
    # Test generation
    response = await generate_response(
        query=mock_query,
        chunks=chunks,
        max_tokens=150,
        temperature=0.7
    )
    assert "response" in response
```

**Impact**: These changes address error handling coverage gaps, integration testing deficiencies, and ensure comprehensive testing of the OpenAI integration.

### 6.6 Update Test Dependencies

**Change**: Update test dependencies for compatibility with the new OpenAI integration.

1. **Update pytest Configuration**:
```ini
# pytest.ini
[pytest]
asyncio_mode = auto
markers =
    integration: marks tests as integration tests
    unit: marks tests as unit tests
```

2. **Update Test Requirements**:
```txt
# requirements-test.txt
pytest==7.4.3
pytest-asyncio==0.23.2
pytest-cov==4.1.0
pytest-mock==3.12.0
```

3. **Add Test Environment Variables**:
```env
# .env.test
POSTGRES_DB=test_db
POSTGRES_USER=test_user
POSTGRES_PASSWORD=test_password
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
OPENAI_API_KEY=test_key
OPENAI_MODEL=gpt-3.5-turbo
```

**Impact**: These changes resolve version compatibility problems, ensure proper OpenAI integration support, improve corporate environment compatibility, and enhance test reporting.

### 6.7 Improve Test Documentation

**Change**: Add comprehensive documentation for test modules, classes, and functions.

1. **Add Test Module Documentation**:
```python
"""
Test suite for the RAG application.

This module contains tests for:
- Generation service
- Retrieval service
- Database operations
- API endpoints
- Integration flows

Tests are organized by service and include both unit and integration tests.
"""
```

2. **Add Test Class Documentation**:
```python
class TestGenerationService:
    """
    Test suite for the generation service.
    
    Tests cover:
    - Basic response generation
    - Error handling
    - Edge cases
    - Integration with OpenAI
    """
```

3. **Add Test Function Documentation**:
```python
def test_generate_response_basic():
    """
    Test basic response generation functionality.
    
    Verifies:
    - Response format is correct
    - Response contains query content
    - Response includes context from chunks
    - Token rate is reported
    """
```

**Impact**: These changes address documentation coverage gaps, improve onboarding for new developers, simplify maintenance, facilitate knowledge transfer, enhance quality assurance, and improve CI/CD integration.

These improvements ensure:
1. Better test isolation and reliability
2. More comprehensive test coverage
3. Improved error handling
4. Better documentation
5. Easier maintenance
6. More reliable CI/CD pipelines

## 7. Deployment and CI/CD Improvements

**Why**: The current deployment process has several issues that need to be addressed for reliable deployment in corporate environments:

1. **Deployment Process Issues**:
   - Manual deployment steps are error-prone and time-consuming
   - No clear separation between development, staging, and production environments
   - Docker configuration doesn't handle corporate proxies and certificates properly
   - Deployment scripts lack proper error handling and logging

2. **CI/CD Pipeline Gaps**:
   - No automated testing in the deployment pipeline
   - No automated deployment to different environments
   - No versioning or release management
   - No monitoring or alerting for deployment issues

3. **Infrastructure Management Problems**:
   - Docker Compose configuration is outdated and doesn't support the new OpenAI integration
   - No container orchestration for production deployments
   - Resource allocation isn't optimized
   - No backup and recovery procedures

The following changes address these issues systematically:

### 7.1 Update Docker Compose Configuration

**Change**: Update the Docker Compose configuration to support the new OpenAI integration and handle corporate environments properly.

```yaml
# deploy/docker/docker-compose.yaml
version: "3.8"

services:
  postgres:
    image: ankane/pgvector:latest
    ports:
      - "${POSTGRES_PORT}:5432"
    volumes:
      - ./data:/var/lib/postgresql/data
      - ./postgres/init_pgvector.sql:/docker-entrypoint-initdb.d/init_pgvector.sql
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER} -d ${POSTGRES_DB}"]
      interval: 10s
      timeout: 5s
      retries: 5
```

**Impact**: This change ensures proper container orchestration, implements health checks, and supports the new OpenAI integration.

### 7.2 Create Deployment Scripts

**Change**: Create comprehensive deployment scripts for different environments.

```bash
#!/bin/bash
# deploy/scripts/deploy.sh

set -e

# Load environment variables
source .env

# Build and start containers
docker-compose -f deploy/docker/docker-compose.yaml up -d

# Wait for services to be ready
echo "Waiting for services to be ready..."
sleep 5

# Run tests
poetry run pytest tests/ -v

echo "Deployment complete."
```

**Impact**: These scripts automate the deployment process, ensure consistent deployments across environments, and implement proper error handling.

### 7.3 Implement CI/CD Pipeline

**Change**: The CI/CD pipeline has been simplified to focus on testing and code quality.

Key changes to `.github/workflows/ci-initialise.yml`:

1. **Environment Setup**:
   - Streamlined environment variables to focus on testing
   - Simplified PostgreSQL service configuration
   - Removed unnecessary environment variables

2. **Dependency Management**:
   - Improved Poetry caching strategy
   - Combined dependency installation steps
   - Removed redundant steps

3. **Testing Process**:
   - Added test coverage reporting
   - Improved test result reporting
   - Simplified database setup for testing

4. **Workflow Triggers**:
   - Optimized workflow triggers to run on specific branches
   - Added pull request triggers
   - Kept manual trigger option

**Impact**: These changes ensure proper CI/CD integration, improve test coverage, and streamline the deployment process.

### 7.4 Create Dockerfile for Application

**Change**: Create a Dockerfile for the application that handles corporate environments properly.

```dockerfile
# deploy/docker/app/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY server /app/server

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8000

# Run the application
CMD ["poetry", "run", "uvicorn", "server.src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**Impact**: This Dockerfile optimizes the build process and creates a production-ready container.

### 7.5 Create Dockerfile for Client

**Change**: Create a Dockerfile for the Streamlit client.

```dockerfile
# deploy/docker/client/Dockerfile
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Copy poetry files
COPY pyproject.toml poetry.lock ./

# Install poetry and dependencies
RUN pip install poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-dev

# Copy application code
COPY client /app/client

# Set environment variables
ENV PYTHONPATH=/app

# Expose port
EXPOSE 8501

# Run the application
CMD ["poetry", "run", "streamlit", "run", "client/streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

**Impact**: This Dockerfile creates a production-ready container for the Streamlit client.

### 7.6 Update Makefile

**Change**: Update the Makefile to align with our simplified approach.

```makefile
# Define directories
SERVER_DIR=./server

# Install dependencies
install:
	poetry install

# Run the FastAPI app
run-app:
	poetry run bash -c 'PYTHONPATH=$(SERVER_DIR)/src uvicorn server.src.main:app --reload'

run-client:
	poetry run streamlit run client/streamlit_app.py

# Build the postgres db
build-db:
	docker compose --env-file .env -f deploy/docker/postgres/docker-compose.yaml up --build

# Bring down the postgres db and then remove the config data.
remove-db:
	docker compose --env-file .env -f deploy/docker/postgres/docker-compose.yaml down
	rm -rf deploy/docker/postgres/data

# Run tests
test:
	poetry run pytest tests/ -v --cov=server --cov-report=xml

# Clean up build artifacts
clean:
	find . -type f -name '*.pyc' -delete
```

**Impact**: These changes ensure proper build and deployment processes while supporting the new OpenAI integration.

