"""
Generation controller for handling text generation requests.

This module provides endpoints for generating text responses based on user queries
and retrieved document chunks using the OpenAI API.
"""

from fastapi import APIRouter, HTTPException, Query
from services.generation_service import generate_response
from services.retrieval_service import retrieve_top_k_chunks
import os
import opik


router = APIRouter()

# Database configuration for document retrieval
db_config = {
    "dbname": os.environ.get("POSTGRES_DB"),
    "user": os.environ.get("POSTGRES_USER"),
    "password": os.environ.get("POSTGRES_PASSWORD"),
    "host": os.environ.get("POSTGRES_HOST"),
    "port": os.environ.get("POSTGRES_PORT"),
}


@opik.track
@router.get("/generate")
async def generate_answer_endpoint(
    query: str = Query(..., description="The query text from the user"),
    top_k: int = Query(5, description="Number of top chunks to retrieve"),
    max_tokens: int = Query(200, description="The maximum number of tokens to generate"),
    temperature: float = Query(0.7, description="Sampling temperature for the model"),
):
    """Generate a response based on retrieved document chunks and user query.

    This endpoint retrieves relevant document chunks based on the user's query,
    then uses these chunks as context to generate a response using the OpenAI API.

    Args:
        query (str): The query text from the user.
        top_k (int, optional): Number of top chunks to retrieve. Defaults to 5.
        max_tokens (int, optional): Maximum number of tokens to generate in the response. Defaults to 200.
        temperature (float, optional): Temperature setting for the generation model. Defaults to 0.7.

    Returns:
        dict: A dictionary containing the generated response and metadata.

    Raises:
        HTTPException: 
            - 404: If no documents are found for the query
            - 500: If there's an error generating the response
    """
    try:
        chunks = retrieve_top_k_chunks(query, top_k, db_config=db_config)
        if not chunks:
            raise HTTPException(status_code=404, detail="No documents found.")

        generated_response = await generate_response(
            query, chunks, max_tokens, temperature
        )
        
        if generated_response is None:
            raise HTTPException(
                status_code=500,
                detail="Failed to generate response from the language model."
            )
        
        print(f"Generated response {generated_response}")
        return generated_response

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )
