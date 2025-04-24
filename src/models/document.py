from pydantic import BaseModel
from typing import List


class Document(BaseModel):
    """
    Document model representing a paper with its title, summary, and chunks.
    """
    title: str
    summary: str
    chunks: List[str] 