from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Union
import numpy as np


class Document(BaseModel):
    """Base document model."""

    id: Optional[int] = None
    title: str
    summary: str
    chunk: str
    embedding: Optional[List[float]] = None

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class RetrievedDocument(Document):
    """Document model with similarity score for retrieved documents."""

    similarity_score: float

    class Config:
        """Pydantic model configuration."""

        from_attributes = True


class GenerationRequest(BaseModel):
    """Request model for text generation."""

    query: str
    chunks: List[RetrievedDocument]
    max_tokens: Optional[int] = 200
    temperature: Optional[float] = 0.7


class GenerationResponse(BaseModel):
    """Response model for text generation."""

    response: str
    response_tokens_per_second: Optional[float] = None
