from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Check if the API is running.
    
    Returns:
        dict: A simple status message
    """
    return {"status": "ok"}