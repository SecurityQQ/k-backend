from src.db.models.user import User
from fastapi import APIRouter, Depends, HTTPException, Path
from .schema import CrawlRequest, CrawlResponse, CrawlStatusResponse
from .service import CrawlService
from src.db.database import get_user_from_request

router = APIRouter(prefix="/crawl", tags=["crawl"])


# Direct service endpoints
@router.post("/start", response_model=CrawlResponse)
async def start_crawl(request: CrawlRequest, user: User = Depends(get_user_from_request)):
    """
    Start a new website crawl job
    """
    try:
        service = CrawlService()
        return await service.start_crawl(request, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/status/{request_id}", response_model=CrawlStatusResponse)
async def get_crawl_status(
    request_id: str = Path(..., description="The crawl request ID"),
    user: User = Depends(get_user_from_request)
):
    """
    Get the status and statistics of a crawl job
    """
    try:
        service = CrawlService()
        return await service.get_crawl_status(request_id, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/restart/{request_id}", response_model=CrawlResponse)
async def restart_crawl(
    request_id: str = Path(..., description="The crawl request ID to restart"),
    user: User = Depends(get_user_from_request)
):
    """
    Restart a crawl job using the original parameters
    """
    try:
        service = CrawlService()
        return await service.restart_crawl(request_id, user)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Health check endpoint
@router.get("/health")
async def health_check():
    """
    Health check endpoint for the crawl service
    """
    return {"status": "healthy", "service": "crawl"}

