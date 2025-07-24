"""Service layer for website crawling operations"""

import asyncio
import aiohttp
from datetime import datetime
from typing import Dict, Any, List, Optional
from urllib.parse import urlparse
from urllib.parse import urljoin

from .schema import CrawlTarget, CrawlResult, CrawlStatus, PageData, FormData
from .tools import browserless_client
from .config import CRAWLING_CONFIG
from ...core.config import settings


class CrawlService:
    """Service for managing website crawling operations"""
    
    def __init__(self):
        self.active_crawls: Dict[str, CrawlResult] = {}
    
    async def crawl_website(self, target: CrawlTarget, crawl_id: str) -> CrawlResult:
        """
        Perform comprehensive website crawling
        
        Args:
            target: Crawl target configuration
            crawl_id: Unique identifier for this crawl
            
        Returns:
            Complete crawl results
        """
        crawl_result = CrawlResult(
            crawl_id=crawl_id,
            target=target,
            status=CrawlStatus.IN_PROGRESS,
            start_time=datetime.now(),
            pages=[]
        )
        
        try:
            visited_urls = set()
            to_visit = [(str(target.url), 0)]  # (url, depth)
            base_domain = urlparse(str(target.url)).netloc
            
            unique_js_files = set()
            unique_endpoints = set()
            
            while to_visit and len(visited_urls) < target.max_pages:
                current_url, depth = to_visit.pop(0)
                
                if current_url in visited_urls or depth > target.max_depth:
                    continue
                
                # Only crawl same domain unless external links allowed
                current_domain = urlparse(current_url).netloc
                if not target.follow_external_links and current_domain != base_domain:
                    continue
                    
                visited_urls.add(current_url)
                
                try:
                    # Render the page
                    page_result = await browserless_client.render_page(
                        current_url, 
                        target.javascript_timeout
                    )
                    
                    # Create page data
                    forms_data = []
                    for form in page_result.get("forms", []):
                        forms_data.append(FormData(
                            action=form["action"],
                            method=form["method"],
                            inputs=form["inputs"]
                        ))
                    
                    # Fetch JavaScript file contents
                    js_content = {}
                    for js_url in page_result.get("js_files", [])[:10]:  # Limit to first 10 JS files
                        try:
                            async with aiohttp.ClientSession() as session:
                                async with session.get(js_url, timeout=aiohttp.ClientTimeout(total=10)) as js_response:
                                    if js_response.status == 200:
                                        js_text = await js_response.text()
                                        js_content[js_url] = js_text[:50000]  # Limit to 50KB per file
                        except Exception as e:
                            js_content[js_url] = f"Error fetching: {str(e)}"
                        
                        # Rate limiting for JS file fetching
                        await asyncio.sleep(0.5)
                    
                    page_data = PageData(
                        url=current_url,
                        depth=depth,
                        html_length=len(page_result.get("html", "")),
                        text_length=len(page_result.get("text", "")),
                        html_content=page_result.get("html", ""),
                        text_content=page_result.get("text", ""),
                        forms=forms_data,
                        js_files=page_result.get("js_files", []),
                        js_content=js_content,
                        links=page_result.get("links", []),
                        api_endpoints=page_result.get("api_endpoints", []),
                        status_code=page_result.get("status", 200),
                        crawl_time=datetime.now()
                    )
                    
                    crawl_result.pages.append(page_data)
                    
                    # Update counters
                    crawl_result.pages_crawled += 1
                    crawl_result.total_forms += len(forms_data)
                    crawl_result.total_js_files += len(page_result.get("js_files", []))
                    crawl_result.total_api_endpoints += len(page_result.get("api_endpoints", []))
                    
                    unique_js_files.update(page_result.get("js_files", []))
                    unique_endpoints.update(page_result.get("api_endpoints", []))
                    
                    # Add discovered links for next depth level
                    if depth < target.max_depth:
                        for link in page_result.get("links", []):
                            link_domain = urlparse(link).netloc
                            if link not in visited_urls:
                                if target.follow_external_links or link_domain == base_domain:
                                    to_visit.append((link, depth + 1))
                    
                except Exception as e:
                    crawl_result.errors.append(f"Error crawling {current_url}: {str(e)}")
                
                # Rate limiting
                await asyncio.sleep(CRAWLING_CONFIG["rate_limit_delay"])
            
            crawl_result.unique_js_files = len(unique_js_files)
            crawl_result.unique_endpoints = len(unique_endpoints)
            crawl_result.status = CrawlStatus.COMPLETED
            crawl_result.end_time = datetime.now()
            
        except Exception as e:
            crawl_result.status = CrawlStatus.FAILED
            crawl_result.error = str(e)
            crawl_result.end_time = datetime.now()
        
        # Store the result
        self.active_crawls[crawl_id] = crawl_result
        return crawl_result
    
    async def quick_crawl(self, url: str) -> Dict[str, Any]:
        """
        Perform a quick single-page crawl
        
        Args:
            url: URL to crawl
            
        Returns:
            Quick crawl results
        """
        try:
            result = await browserless_client.render_page(url, 3000)
            
            # Fetch content of first few JavaScript files
            js_content = {}
            for js_url in result.get("js_files", [])[:3]:  # First 3 only for quick crawl
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(js_url, timeout=aiohttp.ClientTimeout(total=5)) as js_response:
                            if js_response.status == 200:
                                js_text = await js_response.text()
                                js_content[js_url] = js_text[:10000]  # Limit to 10KB per file for quick crawl
                except Exception as e:
                    js_content[js_url] = f"Error fetching: {str(e)}"
                
                # Short rate limiting for quick crawl
                await asyncio.sleep(0.2)
            
            return {
                "url": url,
                "status": "completed",
                "html_length": len(result.get("html", "")),
                "text_length": len(result.get("text", "")),
                "html_content": result.get("html", ""),
                "text_content": result.get("text", ""),
                "forms_found": len(result.get("forms", [])),
                "js_files_found": len(result.get("js_files", [])),
                "api_endpoints_found": len(result.get("api_endpoints", [])),
                "links_found": len(result.get("links", [])),
                "forms": result.get("forms", []),
                "js_files": result.get("js_files", [])[:5],  # First 5 only
                "js_content": js_content,
                "api_endpoints": result.get("api_endpoints", [])[:5],  # First 5 only
                "summary": f"Quick crawl found {len(result.get('forms', []))} forms, {len(result.get('js_files', []))} JS files, and {len(result.get('api_endpoints', []))} API endpoints"
            }
            
        except Exception as e:
            return {
                "url": url,
                "status": "failed",
                "error": str(e),
                "summary": f"Quick crawl failed: {str(e)}"
            }
    
    async def render_single_page(self, url: str, wait_time: int = 3000) -> Dict[str, Any]:
        """
        Render a single page with JavaScript
        
        Args:
            url: URL to render
            wait_time: Time to wait for JavaScript
            
        Returns:
            Page rendering results
        """
        try:
            result = await browserless_client.render_page(url, wait_time)
            
            # Fetch JavaScript file contents
            js_content = {}
            for js_url in result.get("js_files", [])[:5]:  # First 5 JS files
                try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(js_url, timeout=aiohttp.ClientTimeout(total=10)) as js_response:
                            if js_response.status == 200:
                                js_text = await js_response.text()
                                js_content[js_url] = js_text[:30000]  # Limit to 30KB per file
                except Exception as e:
                    js_content[js_url] = f"Error fetching: {str(e)}"
                
                # Rate limiting
                await asyncio.sleep(0.3)
            
            return {
                "url": url,
                "status": "completed",
                "html_length": len(result.get("html", "")),
                "text_length": len(result.get("text", "")),
                "html_content": result.get("html", ""),
                "text_content": result.get("text", ""),
                "forms": result.get("forms", []),
                "js_files": result.get("js_files", []),
                "js_content": js_content,
                "links": result.get("links", []),
                "api_endpoints": result.get("api_endpoints", []),
                "summary": f"Page rendered successfully with {len(result.get('forms', []))} forms and {len(result.get('js_files', []))} JS files"
            }
            
        except Exception as e:
            return {
                "url": url,
                "status": "failed",
                "error": str(e),
                "summary": f"Page rendering failed: {str(e)}"
            }
    
    def get_crawl_result(self, crawl_id: str) -> Optional[CrawlResult]:
        """Get crawl result by ID"""
        return self.active_crawls.get(crawl_id)
    
    def delete_crawl_result(self, crawl_id: str) -> bool:
        """Delete a crawl result"""
        if crawl_id in self.active_crawls:
            del self.active_crawls[crawl_id]
            return True
        return False
    
    async def simple_render(self, url: str) -> Dict[str, Any]:
        """
        Simple page rendering using direct browserless content API
        
        Args:
            url: URL to render
            
        Returns:
            Page rendering results with full HTML content
        """
        try:
            # Get token from settings or environment
            import os
            token = settings.BROWSERLESS_TOKEN or os.getenv('BROWSERLESS_TOKEN')
            
            # Force use of production-sfo endpoint (as in your working code)
            browserless_url = "https://production-sfo.browserless.io"
            
            if not token:
                return {
                    "url": url,
                    "status": "failed",
                    "error": "BROWSERLESS_TOKEN not configured",
                    "summary": "Browserless token required for rendering"
                }
            
            endpoint = f"{browserless_url}/content?token={token}"
            payload = {"url": url}
            
            async with aiohttp.ClientSession() as session:
                async with session.post(endpoint, json=payload, headers={"Content-Type": "application/json"}) as response:
                    if not response.ok:
                        # Get the error response for debugging
                        error_text = await response.text()
                        return {
                            "url": url,
                            "status": "failed",
                            "error": f"Browserless API error {response.status}: {error_text}",
                            "summary": f"Failed to fetch content: {response.status}",
                            "debug_info": {
                                "endpoint": endpoint,
                                "status_code": response.status,
                                "response_text": error_text,
                                "token_length": len(token) if token else 0
                            }
                        }
                    
                    html = await response.text()
                    
                    # Parse HTML to extract basic data
                    from bs4 import BeautifulSoup
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Extract JavaScript files
                    js_files = []
                    for script in soup.find_all('script', src=True):
                        src = script['src']
                        if src.startswith('http'):
                            js_files.append(src)
                        else:
                            js_files.append(urljoin(url, src))
                    
                    # Extract forms
                    forms = []
                    for form in soup.find_all('form'):
                        form_data = {
                            "action": form.get('action', url),
                            "method": form.get('method', 'GET').upper(),
                            "inputs": []
                        }
                        
                        for input_elem in form.find_all(['input', 'textarea', 'select']):
                            if input_elem.get('name'):
                                form_data["inputs"].append({
                                    "name": input_elem.get('name'),
                                    "type": input_elem.get('type', 'text'),
                                    "value": input_elem.get('value', ''),
                                    "required": input_elem.get('required', False)
                                })
                        
                        forms.append(form_data)
                    
                    # Extract links
                    links = []
                    for link in soup.find_all('a', href=True):
                        href = link['href']
                        if href.startswith('http'):
                            links.append(href)
                        else:
                            links.append(urljoin(url, href))
                    
                    # Fetch JavaScript content
                    js_content = {}
                    for js_url in js_files[:5]:  # First 5 JS files
                        try:
                            async with session.get(js_url, timeout=aiohttp.ClientTimeout(total=10)) as js_response:
                                if js_response.status == 200:
                                    js_text = await js_response.text()
                                    js_content[js_url] = js_text[:30000]  # Limit to 30KB
                        except Exception as e:
                            js_content[js_url] = f"Error fetching: {str(e)}"
                        
                        await asyncio.sleep(0.3)  # Rate limiting
                    
                    return {
                        "url": url,
                        "status": "completed",
                        "html_length": len(html),
                        "text_length": len(soup.get_text()),
                        "html_content": html,
                        "text_content": soup.get_text(),
                        "forms": forms,
                        "js_files": js_files,
                        "js_content": js_content,
                        "links": links,
                        "api_endpoints": [],  # Could add API endpoint extraction here
                        "rendering_method": "browserless_direct",
                        "summary": f"Page rendered successfully with {len(forms)} forms and {len(js_files)} JS files"
                    }
                    
        except Exception as e:
            return {
                "url": url,
                "status": "failed",
                "error": str(e),
                "summary": f"Page rendering failed: {str(e)}"
            }
    
    def analyze_crawl_results(self, crawl_result: CrawlResult) -> Dict[str, Any]:
        """
        Analyze crawl results for security insights
        
        Args:
            crawl_result: Completed crawl results
            
        Returns:
            Analysis insights
        """
        analysis = {
            "security_insights": [],
            "interesting_endpoints": [],
            "forms_analysis": [],
            "technology_stack": [],
            "recommendations": []
        }
        
        # Analyze forms for security testing opportunities
        high_value_forms = []
        for page in crawl_result.pages:
            for form in page.forms:
                # Look for interesting forms
                form_inputs = [inp.get("name", "").lower() for inp in form.inputs]
                if any(keyword in " ".join(form_inputs) for keyword in ["password", "login", "email", "user"]):
                    high_value_forms.append({
                        "url": page.url,
                        "action": form.action,
                        "method": form.method,
                        "inputs": len(form.inputs)
                    })
        
        if high_value_forms:
            analysis["forms_analysis"] = high_value_forms
            analysis["security_insights"].append("Authentication forms found - prime targets for testing")
        
        # Analyze API endpoints
        all_endpoints = []
        for page in crawl_result.pages:
            all_endpoints.extend(page.api_endpoints)
        
        interesting_endpoints = [ep for ep in all_endpoints if any(keyword in ep.lower() 
                               for keyword in ["api", "admin", "auth", "login", "user", "data"])]
        
        if interesting_endpoints:
            analysis["interesting_endpoints"] = list(set(interesting_endpoints))
            analysis["security_insights"].append("Interesting API endpoints discovered")
        
        # Technology stack detection
        all_js_files = []
        for page in crawl_result.pages:
            all_js_files.extend(page.js_files)
        
        frameworks = []
        for js_file in all_js_files:
            js_lower = js_file.lower()
            if "react" in js_lower:
                frameworks.append("React")
            elif "angular" in js_lower:
                frameworks.append("Angular")
            elif "vue" in js_lower:
                frameworks.append("Vue.js")
            elif "jquery" in js_lower:
                frameworks.append("jQuery")
        
        analysis["technology_stack"] = list(set(frameworks))
        
        # Recommendations
        if crawl_result.total_forms > 0:
            analysis["recommendations"].append("Test discovered forms for XSS and injection vulnerabilities")
        if crawl_result.unique_endpoints > 0:
            analysis["recommendations"].append("Scan API endpoints for authentication bypasses")
        if crawl_result.unique_js_files > 0:
            analysis["recommendations"].append("Analyze JavaScript files for exposed secrets and APIs")
        
        return analysis


# Global service instance
crawl_service = CrawlService() 