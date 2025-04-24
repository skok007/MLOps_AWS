import os
import json
import dotenv
from typing import List, Dict, Any
from utils import read_json_files, save_processed_papers_to_file

dotenv.load_dotenv()

DATA_PATH = os.getenv('DATA_PATH')


def process_papers(papers: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process papers by extracting relevant information.
    
    Args:
        papers (List[Dict[str, Any]]): List of papers to process
        
    Returns:
        List[Dict[str, Any]]: Processed papers with extracted information
    """
    processed_papers = []
    
    for paper in papers:
        processed_paper = {
            "title": paper.get("title", ""),
            "summary": paper.get("summary", ""),
            "metadata": {
                "source": "arxiv",
                "processed_date": "2024-03-01"
            }
        }
        processed_papers.append(processed_paper)
    
    return processed_papers


def run_ingestion_pipeline(
    input_dir: str,
    output_dir: str,
    save_intermediate: bool = True
) -> List[Dict[str, Any]]:
    """
    Run the complete ingestion pipeline.
    
    Args:
        input_dir (str): Directory containing input files
        output_dir (str): Directory to save output files
        save_intermediate (bool): Whether to save intermediate results
        
    Returns:
        List[Dict[str, Any]]: List of processed papers
    """
    # Read input files
    papers = read_json_files(input_dir)
    
    # Process papers
    processed_papers = process_papers(papers)
    
    # Save results if requested
    if save_intermediate:
        output_file = os.path.join(output_dir, "processed_papers.json")
        save_processed_papers_to_file(processed_papers, output_file)
    
    return processed_papers


if __name__ == "__main__":
    # Run the pipeline
    processed_papers = run_ingestion_pipeline(
        input_dir=DATA_PATH,
        output_dir=DATA_PATH
    )
    print(f"Successfully processed {len(processed_papers)} papers") 