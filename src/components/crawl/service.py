from typing import Dict, Any
from .schema import CrawlRequest, CrawlResponse, CrawlStatusResponse
from .tasks import crawl_website_task
from ...db.config import RequestStatus
from ...db import get_db
import uuid
from src.components.auth.lib.token_service import TokenService
from src.db.models.user import User
from ...db.queries import get_request_by_id

class CrawlService:
    """Service layer for website crawling - handles dispatching tasks"""
    
    def _dispatch_crawl_task(self, user_id: int, url: str, params: dict, request_id: str = None) -> any:
        """Helper to dispatch the Celery task"""
        return crawl_website_task.delay(
            user_id=user_id,
            url=url,
            max_pages=params.get("max_pages"),
            max_depth=params.get("max_depth"),
            delay_between_requests=params.get("delay_between_requests"),
            respect_robots_txt=params.get("respect_robots_txt"),
            follow_redirects=params.get("follow_redirects"),
            request_id=request_id
        )

    async def start_crawl(self, request: CrawlRequest, user: User) -> CrawlResponse:
        """Dispatch a crawl job to Celery and return a response"""
        try:
            print("Starting crawl service, user_id: ", user.id)
            params = request.model_dump(exclude={"url"})
            task = self._dispatch_crawl_task(user.id, str(request.url), params)
            return CrawlResponse(
                success=True,
                request_id=task.id,
                message="Crawl job has been queued",
                status="pending",
            )
        except Exception as e:
            return CrawlResponse(
                success=False,
                request_id="n/a",
                message=f"Failed to queue crawl job: {str(e)}",
                status="failed",
            )
    
    async def get_crawl_status(self, request_id: str, user: User) -> CrawlStatusResponse:
        """Get status and statistics for a crawl job"""
        try:
            # First, check the task in Celery
            task_result = crawl_website_task.AsyncResult(request_id)

            # If task is still running or pending, get db status
            if task_result.state in ['PENDING', 'STARTED', 'RETRY']:
                 async with get_db() as db:
                    db_status = await get_request_by_id(db, request_id, user.id)
                    if db_status:
                        return CrawlStatusResponse(
                            request_id=request_id,
                            status=db_status.status.value,
                            total_pages=0,  # These stats are not available until task completion
                            completed=0,
                            failed=0,
                            total_content=0,
                            created_at=db_status.created_at
                        )

            # If the task has finished, you can return more detailed info
            if task_result.state == 'SUCCESS':
                # Assuming the task returns a dictionary with the final stats
                result_data = task_result.result or {}
                return CrawlStatusResponse(
                    request_id=request_id,
                    status="completed",
                    total_pages=result_data.get("total_pages", 0),
                    completed=result_data.get("completed", 0),
                    failed=result_data.get("failed", 0),
                    total_content=result_data.get("total_content", 0),
                    created_at=result_data.get("created_at")
                )

            if task_result.state == 'FAILURE':
                return CrawlStatusResponse(request_id=request_id, status="failed", message="Crawl failed to execute.")

            # Fallback for unknown states or if request not in DB yet
            return CrawlStatusResponse(request_id=request_id, status=task_result.state.lower())
            
        except Exception as e:
            return CrawlStatusResponse(
                request_id=request_id,
                status="error",
                message=str(e)
            )

    async def restart_crawl(self, request_id: str, user: User) -> CrawlResponse:
        """Restart a crawl job using the original parameters"""
        try:
            # Get the original request to retrieve parameters
            async with get_db() as db:

                print("[LOGS] Restarting crawl, user_id: ", user.id, request_id)
                original_request = await get_request_by_id(db, request_id, user.id)
                print("[LOGS] Original request: ", original_request)
                if not original_request:
                    return CrawlResponse(
                        success=False,
                        request_id="n/a",
                        message="Original request not found",
                        status="failed",
                    )
                
                # Extract parameters from the original request
                params = original_request.params or {}
                print("[LOGS] Params: ", params)
                # Start new crawl task with original parameters
                self._dispatch_crawl_task(user.id, original_request.url, params, request_id=original_request.id)
                
                return CrawlResponse(
                    success=True,
                    request_id=request_id,
                    message="Crawl job has been restarted",
                    status="pending",
                )
                
        except Exception as e:
            return CrawlResponse(
                success=False,
                request_id="n/a",
                message=f"Failed to restart crawl job: {str(e)}",
                status="failed",
            )

    def _extract_metadata(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract metadata from raw crawl response"""
        return {
            "crawl_time": raw_data.get('timestamp'),
            "pages_crawled": raw_data.get('total_pages', 0),
            "content_items": raw_data.get('total_content', 0)
        }

