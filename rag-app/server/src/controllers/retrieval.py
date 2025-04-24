"""
Retrieval controller for handling document retrieval requests.

This module provides endpoints for retrieving relevant document chunks based on
user queries using semantic search functionality.
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List
from services.retrieval_service import retrieve_top_k_chunks
from models.document import RetrievedDocument
from dotenv import load_dotenv
import os
import opik

load_dotenv()

# Database connection configuration
db_config = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}

router = APIRouter()

@opik.track
@router.get("/retrieve", response_model=List[RetrievedDocument])
async def retrieve_top_k_chunks_endpoint(
    query: str = Query(..., description="The query text from the user"),
    top_k: int = Query(5, description="Number of top chunks to retrieve (default is 5)"),
):
    """Retrieve the top K relevant document chunks based on a query.

    This endpoint performs semantic search to find the most relevant document
    chunks for a given user query, using vector similarity search.

    Args:
        query (str): The query text from the user.
        top_k (int, optional): Number of top documents to retrieve. Defaults to 5.

    Returns:
        List[RetrievedDocument]: A list of the top retrieved chunks, each containing:
            - id: Document identifier
            - title: Document title
            - summary: Document summary
            - chunk: Text content
            - similarity_score: Relevance score

    Raises:
        HTTPException:
            - 404: If no chunks are found for the query
            - 500: If there's an error during retrieval
    """
    try:
        chunks = retrieve_top_k_chunks(query, top_k, db_config=db_config)
        if not chunks:
            raise HTTPException(status_code=404, detail="No chunks found.")
        return chunks
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"Error retrieving chunks: {str(e)}"
        )
