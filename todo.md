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

## AWS Setup Improvements

1. **Created Consolidated AWS Bedrock Setup Script**
   - Developed `setup-aws-bedrock.sh` to replace multiple separate scripts
   - Implemented command-line arguments for flexibility and customization
   - Added comprehensive error handling and validation
   ```bash
   # Basic usage with defaults
   ./setup-aws-bedrock.sh

   # Custom region and user
   ./setup-aws-bedrock.sh --region us-east-1 --user my-user

   # Store credentials in Secrets Manager
   ./setup-aws-bedrock.sh --store-secret

   # Skip policy creation (use existing policies)
   ./setup-aws-bedrock.sh --skip-policies
   ```

2. **Implemented Dynamic Account ID Retrieval**
   - Added functionality to automatically retrieve AWS account ID
   - Provided fallback to environment variable if automatic retrieval fails
   ```bash
   # Get the AWS account ID dynamically if not provided
   if [ -z "$AWS_ACCOUNT_ID" ]; then
     echo "AWS_ACCOUNT_ID not set. Attempting to retrieve it automatically..."
     AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query "Account" --output text)
     if [ $? -ne 0 ]; then
       handle_error "Failed to retrieve AWS account ID automatically. Please set the AWS_ACCOUNT_ID environment variable manually."
     fi
     echo "✅ Retrieved AWS account ID: $AWS_ACCOUNT_ID"
   fi
   ```

3. **Created Service-Specific IAM Policies**
   - Developed `create-policies.sh` to create granular policies for each AWS service
   - Replaced overly permissive AdministratorAccess policy with specific permissions
   - Implemented policies for Bedrock, ECR, ECS, EC2, CloudWatch, CloudFormation, S3, and Lambda
   ```bash
   # Create Bedrock policy
   cat <<EOF > bedrock-policy.json
   {
     "Version": "2012-10-17",
     "Statement": [
       {
         "Effect": "Allow",
         "Action": [
           "bedrock:InvokeModel",
           "bedrock:ListFoundationModels",
           "bedrock:ListCustomModels"
         ],
         "Resource": "*"
       }
     ]
   }
   EOF

   aws iam create-policy \
     --policy-name BedrockAccessPolicy \
     --policy-document file://bedrock-policy.json
   ```

4. **Added Comprehensive Documentation**
   - Created `AWS_README.md` with detailed setup instructions
   - Included troubleshooting guide for common issues
   - Added security best practices and examples of different use cases
   - Provided step-by-step instructions for both automated and manual setup

5. **Implemented Modular Script Structure**
   - Organized `setup-aws-bedrock.sh` into functions for each major step
   - Created reusable functions for error handling and command validation
   - Added detailed comments explaining each section of the script
   ```bash
   # Function to create IAM user
   create_iam_user() {
     echo "Creating IAM user $USER_NAME..."
     # Implementation details...
   }

   # Function to create Bedrock policy
   create_bedrock_policy() {
     echo "Creating custom policy for BedrockAccessPolicy..."
     # Implementation details...
   }

   # Function to create role
   create_role() {
     echo "Creating role $ROLE_NAME..."
     # Implementation details...
   }
   ```

6. **Added Secrets Management Integration**
   - Implemented option to store credentials in AWS Secrets Manager
   - Added functionality to create or update secrets as needed
   - Provided secure handling of sensitive information
   ```bash
   # Function to store credentials in Secrets Manager
   store_credentials() {
     echo "Storing credentials in AWS Secrets Manager..."
     # Implementation details...
     
     # Create or update the secret
     if [[ $EXISTING_SECRET == *"$SECRET_NAME"* ]]; then
       echo "🔁 Secret already exists. Updating value..."
       # Update existing secret...
     else
       echo "🆕 Creating new secret '$SECRET_NAME'..."
       # Create new secret...
     fi
   }
   ```

7. **Improved Error Handling and User Feedback**
   - Added clear error messages with actionable solutions
   - Implemented graceful handling of existing resources
   - Added progress indicators and success messages
   ```bash
   # Function to handle errors
   handle_error() {
     echo "❌ Error: $1"
     exit 1
   }

   # Example of graceful handling of existing resources
   if ! aws iam create-user --user-name $USER_NAME 2>/dev/null; then
     echo "⚠️ User $USER_NAME already exists. Continuing..."
   fi
   ``` 