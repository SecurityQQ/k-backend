import asyncio
import aiohttp
import hashlib
import xml.etree.ElementTree as ET
import re
from typing import List, Dict, Set, Optional
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


from .config import HttpConfig, CrawlConfig, SitemapConfig
from .queries import (
    get_request, get_crawls_for_request, get_content_count_for_request,
    create_crawl, update_crawl_status, create_content, update_request_status
)
from ...db.config import RequestStatus, CrawlStatus, ContentType
from ...db import get_db


class CrawlWebsiteClient:
    def __init__(self):
        self.session = None
        self.robots_cache = {}  # Cache robots.txt per domain
        
    async def __aenter__(self):
        connector = aiohttp.TCPConnector(
            limit=CrawlConfig.CONNECTION_LIMIT, 
            limit_per_host=CrawlConfig.CONNECTION_LIMIT_PER_HOST
        )
        timeout = aiohttp.ClientTimeout(total=CrawlConfig.REQUEST_TIMEOUT_SECONDS)
        
        self.session = aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': HttpConfig.USER_AGENT}
        )
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def crawl(
        self, 
        request_id: str,
        max_pages: Optional[int] = None,
        max_depth: Optional[int] = None,
        delay_between_requests: Optional[float] = None,
        respect_robots_txt: Optional[bool] = None,
        follow_redirects: Optional[bool] = None
    ) -> Dict:
        """Main crawl method with configurable parameters"""
        # Set defaults
        max_pages = max_pages or CrawlConfig.DEFAULT_MAX_PAGES
        max_depth = max_depth or CrawlConfig.DEFAULT_MAX_DEPTH
        delay_between_requests = delay_between_requests or CrawlConfig.DEFAULT_DELAY_BETWEEN_REQUESTS
        respect_robots_txt = respect_robots_txt if respect_robots_txt is not None else CrawlConfig.DEFAULT_RESPECT_ROBOTS_TXT
        follow_redirects = follow_redirects if follow_redirects is not None else CrawlConfig.DEFAULT_FOLLOW_REDIRECTS
        
        async with get_db() as db:
            # Get and validate request
            request = await get_request(db, request_id)
            if not request:
                return {"error": "Request not found"}
            
            # Update status to crawling
            await update_request_status(db, request.id, RequestStatus.CRAWLING)
            
            try:
                # Discover URLs with depth tracking
                urls_to_crawl = await self._discover_urls_with_depth(
                    request.url, max_depth, respect_robots_txt
                )
                
                # Limit by max_pages
                urls_to_process = list(urls_to_crawl.items())[:max_pages]
                
                # Process each URL with delay
                for i, (url, depth) in enumerate(urls_to_process):
                    if i > 0:  # Don't delay before first request
                        await asyncio.sleep(delay_between_requests)
                    
                    await self._process_url(url, request_id, follow_redirects, respect_robots_txt)
                
                await update_request_status(db, request.id, RequestStatus.COMPLETED)
                
            except Exception as e:
                await update_request_status(db, request.id, RequestStatus.FAILED)
                print(f"Crawl failed: {e}")
            
            return await self.get_status(request_id)
    
    async def get_status(self, request_id: str) -> Dict:
        """Get crawl status and statistics"""
        async with get_db() as db:
            # Get request
            request = await get_request(db, request_id)
            if not request:
                return {"error": "Request not found"}
            
            # Get crawl stats
            crawls = await get_crawls_for_request(db, request_id)
            
            # Count content
            content_count = await get_content_count_for_request(db, request_id)
            
            return {
                "request_id": request_id,
                "status": request.status,
                "total_pages": len(crawls),
                "completed": len([c for c in crawls if c.status == CrawlStatus.COMPLETED]),
                "failed": len([c for c in crawls if c.status == CrawlStatus.FAILED]),
                "total_content": content_count,
                "created_at": request.created_at.isoformat() if request.created_at else None
            }
    
    async def _discover_urls_with_depth(self, start_url: str, max_depth: int, respect_robots_txt: bool) -> Dict[str, int]:
        """Discover URLs with depth tracking"""
        urls_with_depth = {start_url: 0}
        domain = urlparse(start_url).netloc
        
        # Get sitemap URLs (depth 0)
        sitemap_urls = await self._get_sitemap_urls(start_url)
        for url in sitemap_urls:
            if url not in urls_with_depth:
                urls_with_depth[url] = 0
        
        # Crawl pages level by level
        current_depth = 0
        while current_depth < max_depth:
            current_level_urls = [url for url, depth in urls_with_depth.items() if depth == current_depth]
            
            for url in current_level_urls[:10]:  # Limit URLs per level
                if respect_robots_txt and not await self._can_fetch(url):
                    continue
                    
                try:
                    discovered_urls = await self._extract_urls_from_page(url, domain)
                    for discovered_url in discovered_urls:
                        if discovered_url not in urls_with_depth:
                            urls_with_depth[discovered_url] = current_depth + 1
                except Exception as e:
                    print(f"Failed to discover URLs from {url}: {e}")
            
            current_depth += 1
        
        return urls_with_depth
    
    async def _get_sitemap_urls(self, base_url: str) -> Set[str]:
        """Get URLs from sitemaps"""
        domain = f"{urlparse(base_url).scheme}://{urlparse(base_url).netloc}"
        sitemap_urls = set()
        
        # Check robots.txt
        try:
            async with self.session.get(f"{domain}/robots.txt") as response:
                if response.status == HttpConfig.SUCCESS_STATUS:
                    robots_text = await response.text()
                    sitemaps = re.findall(r'Sitemap:\s*(.+)', robots_text, re.IGNORECASE)
                    sitemap_urls.update(url.strip() for url in sitemaps)
        except:
            pass
        
        # Check common locations
        for path in SitemapConfig.COMMON_SITEMAP_PATHS:
            try:
                sitemap_url = f"{domain}{path}"
                async with self.session.get(sitemap_url) as response:
                    if response.status == HttpConfig.SUCCESS_STATUS:
                        sitemap_urls.add(sitemap_url)
                        break  # Found one, that's enough
            except:
                continue
        
        # Parse sitemaps
        all_urls = set()
        for sitemap_url in sitemap_urls:
            urls = await self._parse_sitemap(sitemap_url)
            all_urls.update(urls)
        
        return all_urls
    
    async def _parse_sitemap(self, sitemap_url: str) -> Set[str]:
        """Parse XML sitemap"""
        try:
            async with self.session.get(sitemap_url) as response:
                if response.status != HttpConfig.SUCCESS_STATUS:
                    return set()
                
                xml_content = await response.text()
                root = ET.fromstring(xml_content)
                ns = {'ns': SitemapConfig.SITEMAP_NAMESPACE}
                
                # Extract URLs
                urls = set()
                for loc in root.findall('.//ns:url/ns:loc', ns):
                    if loc.text:
                        urls.add(loc.text)
                
                return urls
        except:
            return set()
    
    async def _extract_urls_from_page(self, url: str, target_domain: str) -> Set[str]:
        """Extract URLs from HTML page"""
        try:
            async with self.session.get(url) as response:
                if response.status != HttpConfig.SUCCESS_STATUS:
                    return set()
                
                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')
                
                urls = set()
                for link in soup.find_all(['a', 'area'], href=True):
                    full_url = urljoin(url, link['href'])
                    parsed = urlparse(full_url)
                    
                    if parsed.netloc == target_domain:
                        clean_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
                        if parsed.query:
                            clean_url += f"?{parsed.query}"
                        urls.add(clean_url)
                
                return urls
        except:
            return set()
    
    async def _process_url(self, url: str, request_id: str, follow_redirects: bool, respect_robots_txt: bool):
        """Process single URL - crawl and save content"""
        async with get_db() as db:
            # Check robots.txt if required
            if respect_robots_txt and not await self._can_fetch(url):
                print(f"Robots.txt disallows crawling {url}")
                return
            
            # Create crawl record
            crawl = await create_crawl(db, request_id, url)
            
            try:
                # Configure request options
                allow_redirects = follow_redirects
                
                # Fetch page
                async with self.session.get(url, allow_redirects=allow_redirects) as response:
                    # Check for success status
                    if response.status != HttpConfig.SUCCESS_STATUS:
                        await update_crawl_status(db, crawl, CrawlStatus.FAILED)
                        return
                    
                    html_content = await response.text()
                    
                    # Save HTML
                    await self._save_content(crawl.id, ContentType.HTML, html_content)
                    
                    # Extract and save JS files
                    soup = BeautifulSoup(html_content, 'html.parser')
                    for script in soup.find_all('script', src=True):
                        js_url = urljoin(url, script['src'])
                        await self._save_js_file(crawl.id, js_url)
                    
                    await update_crawl_status(db, crawl, CrawlStatus.COMPLETED)
                    
            except Exception as e:
                await update_crawl_status(db, crawl, CrawlStatus.FAILED)
                print(f"Failed to process {url}: {e}")
    
    async def _save_content(self, crawl_id: str, content_type: str, content: str):
        """Save content to database"""
        async with get_db() as db:
            content_hash = hashlib.sha256(content.encode()).hexdigest()
            await create_content(db, crawl_id, content_type, content_hash, content)
    
    async def _save_js_file(self, crawl_id: str, js_url: str):
        """Download and save JS file"""
        try:
            async with self.session.get(js_url) as response:
                if response.status == HttpConfig.SUCCESS_STATUS:
                    js_content = await response.text()
                    await self._save_content(crawl_id, ContentType.JS, js_content)
        except:
            pass  # Ignore JS download failures
    
    async def _can_fetch(self, url: str) -> bool:
        """Check if URL can be fetched according to robots.txt"""
        parsed_url = urlparse(url)
        domain = f"{parsed_url.scheme}://{parsed_url.netloc}"
        
        # Check cache first
        if domain in self.robots_cache:
            disallowed_paths = self.robots_cache[domain]
        else:
            # Fetch and parse robots.txt
            disallowed_paths = []
            robots_url = f"{domain}/robots.txt"
            
            try:
                async with self.session.get(robots_url) as response:
                    if response.status == HttpConfig.SUCCESS_STATUS:
                        robots_content = await response.text()
                        disallowed_paths = self._parse_robots_txt(robots_content)
            except:
                # If robots.txt can't be fetched, allow crawling
                pass
            
            self.robots_cache[domain] = disallowed_paths
        
        # Check if URL path is disallowed
        url_path = parsed_url.path
        for disallowed_path in disallowed_paths:
            if url_path.startswith(disallowed_path):
                return False
        
        return True
    
    def _parse_robots_txt(self, robots_content: str) -> List[str]:
        """Parse robots.txt content and return disallowed paths"""
        disallowed_paths = []
        lines = robots_content.strip().split('\n')
        current_user_agent = None
        applies_to_us = False
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line.lower().startswith('user-agent:'):
                user_agent = line.split(':', 1)[1].strip()
                applies_to_us = (user_agent == '*' or 
                               HttpConfig.USER_AGENT.lower() in user_agent.lower())
            elif line.lower().startswith('disallow:') and applies_to_us:
                disallowed_path = line.split(':', 1)[1].strip()
                if disallowed_path:
                    disallowed_paths.append(disallowed_path)
        
        return disallowed_paths
    
