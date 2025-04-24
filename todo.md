# MLOps AWS Project - Code Changes Made to Fix Issues

## Python Version and Dependencies

1. **Changed Python Version Constraint**
   - Modified `rag-app/pyproject.toml` to use Python 3.11 instead of 3.12
   - Reason: sentence-transformers and tensorflow don't work well with Python 3.12 yet
   ```toml
   [tool.poetry.dependencies]
   python = ">=3.11,<3.13"  # Changed from "^3.12"
   ```

2. **Updated Database Driver**
   - Changed from `psycopg2` to `psycopg2-binary` in `rag-app/pyproject.toml`
   - This avoids compilation issues on some platforms
   ```toml
   [tool.poetry.dependencies]
   psycopg2-binary = "^2.9.9"  # Changed from psycopg2
   ```

3. **Created Custom requirements.txt**
   - Created a new `rag-app/requirements.txt` file with specific versions
   - Used pip instead of poetry for package installation due to Zscaler certificate issues
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

## Embedding Model Changes

1. **Updated Embedding Model**
   - Changed the model in `rag-app/server/src/ingestion/embeddings.py` from `all-MiniLM-L6-v2` to `paraphrase-MiniLM-L6-v2`
   - This model is more compatible with the current setup
   ```python
   from sentence_transformers import SentenceTransformer
   
   model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Changed from all-MiniLM-L6-v2
   ```

2. **Standardized Embedding Model Across Application**
   - Updated the model in `rag-app/server/src/services/retrieval_service.py` to use `paraphrase-MiniLM-L6-v2`
   - This ensures consistency with the model used in embeddings.py
   - The 'paraphrase-MiniLM-L6-v2' model is specifically designed for paraphrase detection and semantic similarity tasks
   ```python
   def get_embeddings(self, text: str) -> List[float]:
       model = SentenceTransformer('paraphrase-MiniLM-L6-v2')  # Changed from all-MiniLM-L6-v2
       embedding = model.encode(text)
       return embedding.tolist()  # Added .tolist() for pgvector compatibility
   ```

## PostgreSQL Database Configuration

1. **Created Custom Dockerfile for PostgreSQL**
   - Created `pgvector2.Dockerfile` to handle Zscaler certificate issues
   - Implemented a multi-stage build process to handle certificates and build pgvector
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

2. **Fixed Locale Issues in PostgreSQL Container**
   - Added locale packages to the final PostgreSQL image
   - Set environment variables for default locale
   - This resolves the "no usable system locales were found" warning
   ```dockerfile
   RUN apk add --no-cache musl-locales musl-locales-lang tzdata
   ENV LANG=en_US.UTF-8 LANGUAGE=en_US:en LC_ALL=en_US.UTF-8
   ```

3. **Updated Docker Compose Configuration**
   - Modified `rag-app/deploy/docker/postgres/docker-compose.yaml` to use the new Dockerfile
   - Added proper environment variable handling and healthcheck
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

4. **Fixed Database Connection from Devcontainer**
   - Changed database host from `localhost` to `host.docker.internal`
   - This allows the application running in the devcontainer to connect to the PostgreSQL database running on the host machine
   ```env
   POSTGRES_USER=myuser
   POSTGRES_PASSWORD=mypassword
   POSTGRES_DB=mydb
   POSTGRES_PORT=5432
   POSTGRES_HOST=host.docker.internal  # Changed from localhost
   ```

## Retrieval Service Fixes

1. **Fixed Embedding Handling**
   - Ensured proper conversion of embeddings to list format
   - Added `.tolist()` to the embedding output for pgvector compatibility
   ```python
   def get_embeddings(self, text: str) -> List[float]:
       embedding = model.encode(text)
       return embedding.tolist()  # Added .tolist() for pgvector compatibility
   ```

2. **Improved Connection Handling**
   - Added proper try/finally blocks to ensure database connections are closed
   - This prevents connection leaks and resource exhaustion
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

## Generation Service Fixes

1. **Added Error Handling for OpenAI API**
   - Added fallback response in `call_llm` function when OpenAI API key is not available
   - This prevents the application from crashing when the API key is not configured
   ```python
   def call_llm(prompt: str) -> str:
       try:
           # OpenAI API call
           return response.choices[0].text
       except Exception as e:
           return f"Error calling OpenAI API: {str(e)}"
   ```

## Environment Configuration

1. **Added Zscaler Certificate Support**
   - Added Zscaler certificate to the devcontainer Dockerfile
   - Configured environment variables to respect custom certificates
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

## Deployment Steps

1. Build and start PostgreSQL:
   ```bash
   cd rag-app/deploy/docker/postgres
   docker-compose up -d
   ```

2. Run ingestion (inside devcontainer):
   ```bash
   cd rag-app
   python server/src/ingestion/ingest.py
   ```

3. Start FastAPI server (inside devcontainer):
   ```bash
   cd rag-app
   uvicorn server.src.main:app --host 0.0.0.0 --port 8000
   ```

4. Start Streamlit client (inside devcontainer):
   ```bash
   cd rag-app
   streamlit run client/streamlit_app.py
   ```

## Recently Completed Items

1. **Fixed Streamlit Client Response Handling**
   - Updated the Streamlit app to correctly parse the "response" key from the FastAPI backend
   - Fixed the mismatch between backend response format and client expectations
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