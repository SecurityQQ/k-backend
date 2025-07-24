"""FastAPI routes for website crawling component"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from .schema import (
    CrawlTarget,
    CrawlResult,
    CrawlChatRequest,
    CrawlChatResponse,
    QuickCrawlRequest,
    RenderPageRequest
)
from .service import crawl_service
from .agent import CrawlerAgent
from agents import Runner, SQLiteSession

# Create router for this component
router = APIRouter(prefix="/crawl_website", tags=["Website Crawling"])

# Initialize agent
crawler_agent = CrawlerAgent()


@router.post("/crawl", response_model=Dict[str, Any])
async def crawl_website_endpoint(target: CrawlTarget, background_tasks: BackgroundTasks):
    """
    Perform comprehensive website crawling with JavaScript rendering
    
    This endpoint initiates a full website crawl including:
    - JavaScript-enabled page rendering
    - Form discovery and analysis
    - JavaScript file enumeration
    - API endpoint detection
    - Link following with configurable depth
    """
    crawl_id = str(uuid.uuid4())
    
    try:
        # Start the crawl
        result = await crawl_service.crawl_website(target, crawl_id)
        
        return {
            "crawl_id": crawl_id,
            "status": result.status.value,
            "target_url": str(target.url),
            "pages_crawled": result.pages_crawled,
            "total_forms": result.total_forms,
            "total_js_files": result.total_js_files,
            "unique_js_files": result.unique_js_files,
            "unique_endpoints": result.unique_endpoints,
            "crawl_time": (result.end_time - result.start_time).total_seconds() if result.end_time else 0,
            "summary": result.get_summary(),
            "error": result.error,
            "errors": result.errors
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Crawl failed: {str(e)}")


@router.get("/crawl/{crawl_id}", response_model=Dict[str, Any])
async def get_crawl_result(crawl_id: str):
    """Get detailed results from a completed crawl"""
    result = crawl_service.get_crawl_result(crawl_id)
    if not result:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    # Include detailed page data
    detailed_pages = []
    for page in result.pages:
        detailed_pages.append({
            "url": page.url,
            "depth": page.depth,
            "html_length": page.html_length,
            "text_length": page.text_length,
            "html_content": page.html_content,
            "text_content": page.text_content,
            "forms_count": len(page.forms),
            "js_files_count": len(page.js_files),
            "links_count": len(page.links),
            "api_endpoints_count": len(page.api_endpoints),
            "status_code": page.status_code,
            "crawl_time": page.crawl_time.isoformat(),
            "forms": [{"action": f.action, "method": f.method, "inputs": len(f.inputs)} for f in page.forms],
            "js_files": page.js_files,
            "js_content": page.js_content,
            "api_endpoints": page.api_endpoints
        })
    
    return {
        "crawl_id": crawl_id,
        "target_url": str(result.target.url),
        "status": result.status.value,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "pages_crawled": result.pages_crawled,
        "total_forms": result.total_forms,
        "total_js_files": result.total_js_files,
        "unique_js_files": result.unique_js_files,
        "unique_endpoints": result.unique_endpoints,
        "pages": detailed_pages,
        "summary": result.get_summary(),
        "analysis": crawl_service.analyze_crawl_results(result),
        "errors": result.errors,
        "error": result.error
    }


@router.get("/crawl/{crawl_id}/content/{page_index}")
async def get_page_content(crawl_id: str, page_index: int, content_type: str = "html"):
    """
    Get specific content from a crawled page
    
    Args:
        crawl_id: The crawl ID
        page_index: Index of the page (0-based)
        content_type: Type of content to retrieve ("html", "text", "js")
    """
    result = crawl_service.get_crawl_result(crawl_id)
    if not result:
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    if page_index >= len(result.pages) or page_index < 0:
        raise HTTPException(status_code=404, detail="Page index out of range")
    
    page = result.pages[page_index]
    
    if content_type == "html":
        return {
            "url": page.url,
            "content_type": "html",
            "content": page.html_content,
            "length": len(page.html_content)
        }
    elif content_type == "text":
        return {
            "url": page.url,
            "content_type": "text",
            "content": page.text_content,
            "length": len(page.text_content)
        }
    elif content_type == "js":
        return {
            "url": page.url,
            "content_type": "javascript",
            "js_files": page.js_files,
            "js_content": page.js_content,
            "total_js_files": len(page.js_files)
        }
    else:
        raise HTTPException(status_code=400, detail="Invalid content_type. Use 'html', 'text', or 'js'")


@router.post("/quick_crawl", response_model=Dict[str, Any])
async def quick_crawl_endpoint(request: QuickCrawlRequest):
    """
    Perform a quick single-page crawl for immediate feedback
    
    This is a lightweight crawl that analyzes just the target page
    without following links, perfect for quick reconnaissance.
    """
    try:
        result = await crawl_service.quick_crawl(str(request.url))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick crawl failed: {str(e)}")


@router.post("/render", response_model=Dict[str, Any])
async def render_page_endpoint(request: RenderPageRequest):
    """
    Simple and fast page rendering using direct browserless content API
    
    This endpoint uses the most reliable approach to render JavaScript pages:
    - Direct browserless /content API call
    - No complex JavaScript injection
    - Fast and reliable for SPAs
    """
    try:
        result = await crawl_service.simple_render(str(request.url))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Page rendering failed: {str(e)}")


@router.post("/agent", response_model=CrawlChatResponse)
async def chat_with_crawler_agent(request: CrawlChatRequest):
    """
    Have a conversation with the specialized website crawler agent
    
    The agent can:
    - Perform targeted crawling based on natural language requests
    - Answer questions about website structure and content
    - Provide expert analysis of discovered pages and resources
    - Guide reconnaissance and mapping efforts
    """
    try:
        # Create or retrieve session
        session_id = request.session_id or str(uuid.uuid4())
        session = SQLiteSession(session_id)
        
        # Add context if provided
        context_message = ""
        if request.context:
            context_message = f"\nContext: {request.context}"
        
        full_message = request.message + context_message
        
        # Run the agent
        result = await Runner.run(crawler_agent.agent, full_message, session=session)
        
        # Extract any findings summary if the agent performed crawls
        pages_discovered = None
        forms_found = None
        actions_taken = []
        
        # Simple parsing to extract key information
        response_text = result.final_output
        if "pages crawled" in response_text.lower():
            actions_taken.append("website_crawled")
        if "forms" in response_text.lower():
            actions_taken.append("forms_discovered")
        if "javascript" in response_text.lower():
            actions_taken.append("javascript_analyzed")
        if "endpoint" in response_text.lower():
            actions_taken.append("endpoints_found")
        
        return CrawlChatResponse(
            response=response_text,
            session_id=session_id,
            pages_discovered=pages_discovered,
            forms_found=forms_found,
            actions_taken=actions_taken,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent conversation failed: {str(e)}")


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_crawler_capabilities():
    """Get information about the crawler agent's capabilities"""
    return {
        "agent": "CrawlerAgent - The Explorer",
        "description": "Specialized in intelligent website crawling and discovery",
        "capabilities": [
            "JavaScript-enabled page rendering",
            "Comprehensive form discovery",
            "JavaScript file enumeration",
            "API endpoint detection",
            "Intelligent link following",
            "Rate-limited respectful crawling",
            "Modern SPA support",
            "Technology stack detection",
            "Full HTML content storage",
            "JavaScript content extraction"
        ],
        "supported_features": [
            "Configurable crawl depth",
            "External link following",
            "Robots.txt respect",
            "Form parameter extraction",
            "Dynamic content analysis",
            "Content caching and retrieval"
        ],
        "use_cases": [
            "Website reconnaissance",
            "Attack surface mapping",
            "Form vulnerability assessment",
            "API endpoint discovery",
            "Technology stack analysis",
            "Source code analysis"
        ]
    }


@router.get("/config", response_model=Dict[str, Any])
async def get_crawling_config():
    """Get current crawling configuration and limits"""
    from .config import CRAWLING_CONFIG, CRAWLABLE_EXTENSIONS, EXCLUDED_PATHS
    
    return {
        "default_config": CRAWLING_CONFIG,
        "crawlable_extensions": CRAWLABLE_EXTENSIONS,
        "excluded_paths": EXCLUDED_PATHS,
        "limits": {
            "max_depth": 5,
            "max_pages": 100,
            "max_timeout": 30000,
            "min_rate_limit": 0.5,
            "max_js_files_per_page": 10,
            "max_js_file_size": "50KB",
            "quick_crawl_js_limit": 3,
            "render_js_limit": 5
        },
        "features": {
            "javascript_rendering": True,
            "form_discovery": True,
            "api_endpoint_detection": True,
            "robots_txt_support": True,
            "external_links": "configurable",
            "content_storage": True,
            "js_content_extraction": True
        }
    }


@router.delete("/crawl/{crawl_id}")
async def delete_crawl_result(crawl_id: str):
    """Delete a stored crawl result"""
    if not crawl_service.delete_crawl_result(crawl_id):
        raise HTTPException(status_code=404, detail="Crawl not found")
    
    return {"message": f"Crawl {crawl_id} deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint for the crawler service"""
    from ...core.config import settings
    
    return {
        "status": "healthy",
        "component": "crawl_website",
        "active_crawls": len(crawl_service.active_crawls),
        "browserless_configured": bool(settings.BROWSERLESS_TOKEN),
        "capabilities": [
            "javascript_rendering",
            "form_discovery",
            "link_following",
            "api_detection",
            "intelligent_crawling",
            "content_storage",
            "js_extraction"
        ]
    }


@router.get("/test")
async def test_crawler():
    """Test endpoint to verify crawler functionality"""
    test_url = "https://httpbin.org/forms/post"
    
    try:
        result = await crawl_service.quick_crawl(test_url)
        
        return {
            "test_status": "passed" if result["status"] == "completed" else "failed",
            "test_url": test_url,
            "forms_found": result.get("forms_found", 0),
            "js_files_found": result.get("js_files_found", 0),
            "html_content_length": len(result.get("html_content", "")),
            "js_content_files": len(result.get("js_content", {})),
            "message": "Crawler is working correctly with content storage" if result["status"] == "completed" else "Crawler test failed",
            "details": result
        }
    except Exception as e:
        return {
            "test_status": "failed",
            "test_url": test_url,
            "error": str(e),
            "message": "Crawler test failed with error"
        } 