"""
Main entry point for the RAG application backend.

This module defines and instantiates the FastAPI server that uses the controllers,
models and services defined in the rest of the sub-repo. For development purposes
this will run on localhost:8000.
"""

# server/src/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from controllers import retrieval, health_check, generation
from sentence_transformers import SentenceTransformer
from server.src.config import Settings
import opik

# Create settings instance
settings = Settings()

@asynccontextmanager
async def lifespan_context(app: FastAPI):
    """Manage the application's lifespan and resource initialization.

    This context manager handles the initialization and cleanup of resources
    needed by the application, such as the embedding model and Opik configuration.

    Args:
        app (FastAPI): The FastAPI application instance.

    Yields:
        dict: A dictionary containing the initialized resources:
            - embedding_model: The loaded SentenceTransformer model

    Note:
        This function is used as a lifespan context manager for FastAPI,
        ensuring proper resource management throughout the application's lifecycle.
    """
    print("Spinning up lifespan context...")

    print("Configure opik...")
    try:
        opik.configure(
            api_key=settings.opik_api_key,
            workspace=settings.opik_workspace
        )
        print("Opik configuration successful")
    except Exception as e:
        print(f"Warning: Opik configuration failed: {str(e)}")
        print("Application will continue without Opik tracking")

    print("Loading embedding model...")
    embedding_model = SentenceTransformer("paraphrase-MiniLM-L6-v2")
    try:
        yield {
            "embedding_model": embedding_model
        }
    finally:
        print("Cleaning up embedding model...")
        del embedding_model

app = FastAPI(lifespan=lifespan_context)

# Include routers
app.include_router(retrieval.router)
app.include_router(health_check.router)
app.include_router(generation.router)

@app.get("/")
async def read_root():
    """Handle the root endpoint of the application.

    Returns:
        dict: A welcome message indicating the application is running.
    """
    return {"message": "Welcome to the RAG app!"}
