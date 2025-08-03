"""Database and crawling configuration constants"""

# Request/Crawl Status Constants
class RequestStatus:
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"


class CrawlStatus:
    PENDING = "pending"
    CRAWLING = "crawling"
    COMPLETED = "completed"
    FAILED = "failed"


# Content Type Constants
class ContentType:
    HTML = "html"
    JS = "js"






# All constants for easy import
__all__ = [
    "RequestStatus",
    "CrawlStatus", 
    "ContentType"
]