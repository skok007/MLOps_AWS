# MLOps AWS Project - Code Changes Made to Fix Issues

## Python Version and Dependencies

1. **Changed Python Version Constraint**
   - Modified `rag-app/pyproject.toml` to use Python 3.11 instead of 3.12
   - Changed from `python = "^3.12"` to `python = ">=3.11,<3.13"`
   - Reason: sentence-transformers and tensorflow don't work well with Python 3.12 yet

2. **Updated Database Driver**
   - Changed from `psycopg2` to `psycopg2-binary` in `rag-app/pyproject.toml`
   - This avoids compilation issues on some platforms

3. **Created Custom requirements.txt**
   - Created a new `rag-app/requirements.txt` file with specific versions
   - Used pip instead of poetry for package installation due to Zscaler certificate issues

## Embedding Model Changes

1. **Updated Embedding Model**
   - Changed the model in `rag-app/server/src/ingestion/embeddings.py` from `all-MiniLM-L6-v2` to `paraphrase-MiniLM-L6-v2`
   - This model is more compatible with the current setup

2. **Standardized Embedding Model Across Application**
   - Updated the model in `rag-app/server/src/main.py` to use `paraphrase-MiniLM-L6-v2` instead of `all-MiniLM-L6-v2`
   - This ensures consistency with the model used in embeddings.py
   - The 'paraphrase-MiniLM-L6-v2' model is specifically designed for paraphrase detection and semantic similarity tasks

## PostgreSQL Database Configuration

1. **Created Custom Dockerfile for PostgreSQL**
   - Created `pgvector2.Dockerfile` to handle Zscaler certificate issues
   - Implemented a multi-stage build process:
     - Stage 1: Certificate setup with HTTP repo workaround
     - Stage 2: Build pgvector with Zscaler cert available
     - Stage 3: Final image with pgvector + Zscaler certs

2. **Updated Docker Compose Configuration**
   - Modified `rag-app/deploy/docker/postgres/docker-compose.yaml` to use the new Dockerfile
   - Added proper environment variable handling for database credentials
   - Added healthcheck to ensure database is ready before accepting connections

3. **Fixed Database Initialization**
   - Ensured `init_pgvector.sql` properly creates the vector extension
   - Set up the papers table with the correct vector dimension (384) for the embedding model

## Retrieval Service Fixes

1. **Fixed Embedding Handling**
   - Ensured proper conversion of embeddings to list format in `rag-app/server/src/services/retrieval_service.py`
   - Added `.tolist()` to the embedding output for pgvector compatibility

2. **Improved Connection Handling**
   - Added proper try/finally blocks to ensure database connections are closed
   - This prevents connection leaks and resource exhaustion

## Environment Configuration

1. **Added Zscaler Certificate Support**
   - Added Zscaler certificate to the devcontainer Dockerfile
   - Configured environment variables to respect custom certificates:
     - REQUESTS_CA_BUNDLE
     - NODE_EXTRA_CA_CERTS
     - SSL_CERT_FILE
     - PIP_CERT

2. **Created Python 3.11 Virtual Environment**
   - Created a dedicated virtual environment (`env_311`) for Python 3.11
   - This isolates the dependencies and avoids conflicts with system Python

## Deployment Workflow Changes

1. **Modified Deployment Order**
   - Changed the order of operations for local deployment:
     1. build-db (outside devcontainer)
     2. run-ingestion (inside devcontainer)
     3. run-app (inside devcontainer)
     4. run-client (inside devcontainer)

2. **Added Cleanup Commands**
   - Added commands to clean up the database when needed
   - This helps avoid stale data and configuration issues

## Troubleshooting Steps Taken

1. **Zscaler Certificate Issues**
   - Temporarily disabled Zscaler to install requirements
   - Added certificate to the trusted certificates list
   - Configured environment variables to use the Zscaler certificate

2. **Python Version Compatibility**
   - Created a Python 3.11 virtual environment
   - Updated pyproject.toml to specify Python version constraint
   - Installed dependencies in the Python 3.11 environment

3. **Package Installation Issues**
   - Switched from poetry to pip for package installation
   - Created a dedicated requirements.txt file with specific versions
   - Used pip with the `--cert` flag to respect the Zscaler certificate 