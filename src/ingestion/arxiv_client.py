import requests
import xml.etree.ElementTree as ET
import json
import time
import dotenv
import os
from typing import List, Dict

dotenv.load_dotenv()

ARXIV_API_URL = os.getenv("ARXIV_API_URL")  
DATA_PATH = os.getenv("DATA_PATH")  


def parse_arxiv_response(response: requests.Response) -> List[Dict[str, str]]:
    """
    Parse the arXiv response and extract the paper titles and summaries.

    Args:
        response (requests.Response): The response object from the arXiv API.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with paper titles and 
        summaries.
    """
    response.raise_for_status()  # Raise an error for bad responses

    # Parse the XML response
    root = ET.fromstring(response.content)
    papers = []

    # Iterate over each entry in the XML feed
    for entry in root.findall("{http://www.w3.org/2005/Atom}entry"):
        title = entry.find("{http://www.w3.org/2005/Atom}title").text
        summary = entry.find("{http://www.w3.org/2005/Atom}summary").text
        papers.append({"title": title.strip(), "summary": summary.strip()})

    return papers


def fetch_papers(query: str, max_results: int = 10) -> List[Dict[str, str]]:
    """
    Fetch papers from the arXiv API based on a query.

    Args:
        query (str): The search query.
        max_results (int): The maximum number of results to fetch.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with paper titles and 
        summaries.
    """
    params = {"search_query": query, "start": 0, "max_results": max_results}

    response = requests.get(ARXIV_API_URL, params=params)
    return parse_arxiv_response(response)


def fetch_papers_paginated(
    query: str,
    max_results: int = 20,
    results_per_page: int = 5,
    wait_time: int = 5,
    save_local: bool = True,
) -> List[Dict[str, str]]:
    """
    Fetch papers from arXiv API with pagination.

    Args:
        query (str): The search query.
        max_results (int): Maximum number of results to fetch.
        results_per_page (int): Number of results per page.
        wait_time (int): Time to wait between requests.
        save_local (bool): Whether to save results locally.

    Returns:
        List[Dict[str, str]]: A list of dictionaries with paper titles and 
        summaries.
    """
    start = 0
    papers = []
    for i in range(start, max_results, results_per_page):
        params = {"search_query": query, "start": i, "max_results": max_results}

        response = requests.get(ARXIV_API_URL, params=params)
        subset_papers = parse_arxiv_response(response)
        if save_local:
            output_file = f"{DATA_PATH}/papers_{i}_{i+results_per_page}.json"
            with open(output_file, "w") as f:
                json.dump(subset_papers, f)
        papers += subset_papers
        time.sleep(wait_time)
    return papers


if __name__ == "__main__":
    # Example queries for different search scenarios
    papers = fetch_papers_paginated(
        query="ti:perovskite",
        max_results=20,
        results_per_page=5,
        wait_time=5
    )
    
    # Query Variant 1: Basic title-only search
    # papers = fetch_papers_paginated(
    #     query="ti:perovskite",
    #     max_results=20,
    #     results_per_page=5,
    #     wait_time=5
    # )

    # Query Variant 2: Title or abstract contains "perovskite"
    # papers = fetch_papers_paginated(
    #     query="ti:perovskite OR abs:perovskite",
    #     max_results=20,
    #     results_per_page=5,
    #     wait_time=5
    # )

    # Query Variant 3: Filter to category - materials science
    # papers = fetch_papers_paginated(
    #     query="(ti:perovskite OR abs:perovskite) AND cat:cond-mat.mtrl-sci",
    #     max_results=20,
    #     results_per_page=5,
    #     wait_time=5
    # )

    # Query Variant 4: Keyword combo (solar + perovskite in title)
    # papers = fetch_papers_paginated(
    #     query="ti:perovskite AND ti:solar",
    #     max_results=20,
    #     results_per_page=5,
    #     wait_time=5
    # )

    # Query Variant 5: Specific author (Michael Grätzel as example)
    # papers = fetch_papers_paginated(
    #     query="ti:perovskite AND au:Grätzel",
    #     max_results=20,
    #     results_per_page=5,
    #     wait_time=5
    # )
    
    print(papers) 