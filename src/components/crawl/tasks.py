from src.celery import celery_app
from src.components.crawl.client import CrawlWebsiteClient
from src.components.crawl.queries import create_request, update_request_status
from src.db import get_db
from src.db.config import RequestStatus
import asyncio
import uuid


@celery_app.task(bind=True)
def crawl_website_task(self, user_id: int, url: str, max_pages: int, max_depth: int, delay_between_requests: float, respect_robots_txt: bool, follow_redirects: bool, request_id: str = None):
    """
    Celery task to crawl a website.
    """
    
    async def _crawl():
        final_request_id = request_id if request_id else self.request.id
        print("Starting crawl task, request_id: ", final_request_id)
        
        # Collect all parameters
        params = {
            "max_pages": max_pages,
            "max_depth": max_depth,
            "delay_between_requests": delay_between_requests,
            "respect_robots_txt": respect_robots_txt,
            "follow_redirects": follow_redirects
        }
        
        async with get_db() as db:
            try:
                if not request_id:
                    await create_request(db, final_request_id, url, user_id, params)
                await update_request_status(db, final_request_id, RequestStatus.CRAWLING)

                client = CrawlWebsiteClient()
                async with client as c:
                    result = await c.crawl(
                        request_id=final_request_id,
                        max_pages=max_pages,
                        max_depth=max_depth,
                        delay_between_requests=delay_between_requests,
                        respect_robots_txt=respect_robots_txt,
                        follow_redirects=follow_redirects,
                    )

                if "error" in result:
                    await update_request_status(db, final_request_id, RequestStatus.FAILED)
                else:
                    await update_request_status(db, final_request_id, RequestStatus.COMPLETED)
                return result

            except Exception as e:
                await update_request_status(db, final_request_id, RequestStatus.FAILED)
                self.update_state(state='FAILURE', meta={'exc_type': type(e).__name__, 'exc_message': str(e)})
                raise
    
    return asyncio.run(_crawl())