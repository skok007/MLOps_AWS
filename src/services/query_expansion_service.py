from typing import List


def expand_query(query: str) -> List[str]:
    """
    Expand a user query into multiple variations to improve retrieval.
    
    Args:
        query (str): The original user query
        
    Returns:
        List[str]: List of expanded queries
    """
    expanded_queries = [
        query,  # Original query
        f"Find information about {query}",  # Descriptive variation
        f"What are the key aspects of {query}",  # Key aspects
        f"Explain {query} in detail"  # Detailed explanation request
    ]
    
    return expanded_queries 