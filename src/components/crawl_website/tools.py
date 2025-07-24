"""Function tools for website crawling and content discovery"""

import asyncio
import aiohttp
from typing import Dict, Any, List, Optional, Tuple
from urllib.parse import urljoin, urlparse, urlencode
from bs4 import BeautifulSoup
from agents import function_tool

from ...core.config import settings


class BrowserlessClient:
    """Client for interacting with Browserless.io for website rendering"""
    
    def __init__(self):
        self.base_url = settings.BROWSERLESS_URL
        self.token = settings.BROWSERLESS_TOKEN
    
    async def render_page(self, url: str, wait_for_js: int = 3000) -> Dict:
        """
        Render a page with JavaScript execution and return content
        
        Args:
            url: URL to render
            wait_for_js: Time to wait for JavaScript execution (ms)
        
        Returns:
            Dict with page content, HTML source, and metadata
        """
        if not self.token:
            # Fallback to basic HTTP request if no Browserless token
            return await self._basic_fetch(url)
        
        endpoint = f"{self.base_url}/content"
        
        payload = {
            "url": url,
            "waitForTimeout": wait_for_js,
            "addScriptTag": [{
                "content": """
                window.K_SCAN_DATA = {
                    jsFiles: [],
                    forms: [],
                    links: [],
                    apiEndpoints: []
                };
                
                // Extract JavaScript files
                Array.from(document.scripts).forEach(script => {
                    if (script.src) {
                        window.K_SCAN_DATA.jsFiles.push(script.src);
                    }
                });
                
                // Extract forms
                Array.from(document.forms).forEach(form => {
                    const formData = {
                        action: form.action || window.location.href,
                        method: form.method || 'GET',
                        inputs: []
                    };
                    
                    Array.from(form.elements).forEach(element => {
                        if (element.name) {
                            formData.inputs.push({
                                name: element.name,
                                type: element.type || 'text',
                                value: element.value || '',
                                required: element.required || false
                            });
                        }
                    });
                    
                    window.K_SCAN_DATA.forms.push(formData);
                });
                
                // Extract links
                Array.from(document.links).forEach(link => {
                    if (link.href) {
                        window.K_SCAN_DATA.links.push(link.href);
                    }
                });
                
                // Try to find API endpoints in JavaScript
                const scriptContent = Array.from(document.scripts)
                    .map(s => s.innerHTML)
                    .join(' ');
                    
                const apiPatterns = [
                    /['"]/api/[^'"]+/g,
                    /['"]/v\d+/[^'"]+/g,
                    /fetch\s*\(\s*['"]([^'"]+)['"]/g,
                    /axios\.[get|post|put|delete]+\s*\(\s*['"]([^'"]+)['"]/g
                ];
                
                apiPatterns.forEach(pattern => {
                    const matches = scriptContent.match(pattern);
                    if (matches) {
                        matches.forEach(match => {
                            const cleaned = match.replace(/['"]/g, '').replace(/fetch\s*\(\s*/, '').replace(/axios\.[a-z]+\s*\(\s*/, '');
                            if (cleaned.startsWith('/') || cleaned.startsWith('http')) {
                                window.K_SCAN_DATA.apiEndpoints.push(cleaned);
                            }
                        });
                    }
                });
                """
            }],
            "evaluate": {
                "expression": "window.K_SCAN_DATA"
            }
        }
        
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(endpoint, json=payload, headers=headers) as response:
                if response.status != 200:
                    # Fallback to basic fetch on error
                    return await self._basic_fetch(url)
                
                result = await response.json()
                extracted_data = result.get("evaluate", {}).get("result", {}).get("value", {})
                
                return {
                    "html": result.get("html", ""),
                    "text": result.get("text", ""),
                    "url": url,
                    "status": response.status,
                    "js_files": extracted_data.get("jsFiles", []),
                    "forms": extracted_data.get("forms", []),
                    "links": extracted_data.get("links", []),
                    "api_endpoints": extracted_data.get("apiEndpoints", [])
                }
    
    async def _basic_fetch(self, url: str) -> Dict:
        """Fallback method for basic HTTP requests without JavaScript rendering"""
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                html = await response.text()
                
                # Basic extraction without JavaScript execution
                soup = BeautifulSoup(html, 'html.parser')
                
                js_files = []
                for script in soup.find_all('script', src=True):
                    src = script['src']
                    if src.startswith('http'):
                        js_files.append(src)
                    else:
                        js_files.append(urljoin(url, src))
                
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
                
                links = []
                for link in soup.find_all('a', href=True):
                    href = link['href']
                    if href.startswith('http'):
                        links.append(href)
                    else:
                        links.append(urljoin(url, href))
                
                return {
                    "html": html,
                    "text": soup.get_text(),
                    "url": url,
                    "status": response.status,
                    "js_files": js_files,
                    "forms": forms,
                    "links": links,
                    "api_endpoints": []  # Basic fetch can't detect API endpoints
                }


# Global client instance
browserless_client = BrowserlessClient()


@function_tool
async def render_page_with_javascript(url: str, wait_time: int = 3000) -> str:
    """
    Render a webpage with JavaScript execution and extract comprehensive content.
    
    This is the primary tool for getting complete page content including:
    - Full HTML after JavaScript execution
    - Discovered JavaScript files
    - Forms with all input parameters
    - Links and navigation elements
    - Potential API endpoints
    
    Args:
        url: The webpage URL to render
        wait_time: Time to wait for JavaScript execution in milliseconds
    
    Returns:
        Comprehensive page analysis with rendered content and discovered elements
    """
    try:
        result = await browserless_client.render_page(url, wait_time)
        
        summary = f"🌐 Page Rendering Results for {url}:\n\n"
        summary += f"✅ Status: {result['status']}\n"
        summary += f"📄 HTML Content: {len(result['html'])} characters\n"
        summary += f"📝 Text Content: {len(result['text'])} characters\n"
        summary += f"📜 JavaScript Files: {len(result['js_files'])} found\n"
        summary += f"📋 Forms: {len(result['forms'])} discovered\n"
        summary += f"🔗 Links: {len(result['links'])} found\n"
        summary += f"🔌 API Endpoints: {len(result['api_endpoints'])} detected\n\n"
        
        if result['js_files']:
            summary += f"📜 JavaScript Files:\n"
            for js_file in result['js_files'][:5]:  # Show first 5
                summary += f"  - {js_file}\n"
            if len(result['js_files']) > 5:
                summary += f"  ... and {len(result['js_files']) - 5} more\n"
            summary += "\n"
        
        if result['forms']:
            summary += f"📋 Forms Discovered:\n"
            for i, form in enumerate(result['forms'][:3], 1):  # Show first 3
                summary += f"  {i}. Action: {form['action']} (Method: {form['method']})\n"
                summary += f"     Inputs: {len(form['inputs'])} fields\n"
            if len(result['forms']) > 3:
                summary += f"  ... and {len(result['forms']) - 3} more forms\n"
            summary += "\n"
        
        if result['api_endpoints']:
            summary += f"🔌 API Endpoints Found:\n"
            for endpoint in result['api_endpoints'][:5]:  # Show first 5
                summary += f"  - {endpoint}\n"
            if len(result['api_endpoints']) > 5:
                summary += f"  ... and {len(result['api_endpoints']) - 5} more\n"
            summary += "\n"
        
        # Store the full result for other tools to access
        if not hasattr(render_page_with_javascript, '_results_cache'):
            render_page_with_javascript._results_cache = {}
        render_page_with_javascript._results_cache[url] = result
        
        summary += "💡 Full page content and metadata have been cached for other security tools to analyze."
        
        return summary
        
    except Exception as e:
        return f"❌ Failed to render page {url}: {str(e)}"


@function_tool
async def get_page_content(url: str) -> str:
    """
    Get the cached rendered HTML content for a specific URL.
    
    This tool retrieves the full HTML content that was previously rendered
    by render_page_with_javascript. Use this to get the actual HTML source
    for content analysis, secret scanning, or other security assessments.
    
    Args:
        url: The URL to get cached content for
    
    Returns:
        The full HTML content of the rendered page
    """
    try:
        if (hasattr(render_page_with_javascript, '_results_cache') and 
            url in render_page_with_javascript._results_cache):
            
            result = render_page_with_javascript._results_cache[url]
            html_content = result['html']
            
            if html_content:
                return f"📄 HTML Content for {url}:\n\n{html_content}"
            else:
                return f"⚠️ No HTML content found for {url}. Try rendering the page first."
        else:
            return f"⚠️ No cached content for {url}. Use render_page_with_javascript first."
            
    except Exception as e:
        return f"❌ Error retrieving content for {url}: {str(e)}"


@function_tool
async def get_javascript_files(url: str) -> str:
    """
    Get all JavaScript files discovered on a webpage.
    
    Returns a list of JavaScript file URLs that were found during page rendering.
    This is useful for security tools that need to analyze JavaScript content.
    
    Args:
        url: The URL to get JavaScript files for
    
    Returns:
        List of JavaScript file URLs with their content
    """
    try:
        if (hasattr(render_page_with_javascript, '_results_cache') and 
            url in render_page_with_javascript._results_cache):
            
            result = render_page_with_javascript._results_cache[url]
            js_files = result['js_files']
            
            if not js_files:
                return f"ℹ️ No JavaScript files found on {url}"
            
            response = f"📜 JavaScript Files for {url}:\n\n"
            
            for js_url in js_files:
                try:
                    # Fetch the JavaScript content
                    async with aiohttp.ClientSession() as session:
                        async with session.get(js_url) as js_response:
                            if js_response.status == 200:
                                js_content = await js_response.text()
                                response += f"📄 {js_url}:\n"
                                response += f"Size: {len(js_content)} characters\n"
                                response += f"Content preview: {js_content[:200]}...\n\n"
                                
                                # Cache the JS content for other tools
                                if not hasattr(get_javascript_files, '_js_cache'):
                                    get_javascript_files._js_cache = {}
                                get_javascript_files._js_cache[js_url] = js_content
                            else:
                                response += f"⚠️ {js_url}: Failed to fetch (status {js_response.status})\n\n"
                    
                    # Rate limiting
                    await asyncio.sleep(settings.RATE_LIMIT_DELAY)
                    
                except Exception as e:
                    response += f"❌ {js_url}: Error fetching ({str(e)})\n\n"
            
            return response
        else:
            return f"⚠️ No cached data for {url}. Use render_page_with_javascript first."
            
    except Exception as e:
        return f"❌ Error retrieving JavaScript files for {url}: {str(e)}"


@function_tool
async def get_forms_data(url: str) -> str:
    """
    Get detailed information about all forms discovered on a webpage.
    
    Returns comprehensive form data including actions, methods, and all input parameters.
    This is essential for vulnerability testing tools.
    
    Args:
        url: The URL to get form data for
    
    Returns:
        Detailed form information with all parameters
    """
    try:
        if (hasattr(render_page_with_javascript, '_results_cache') and 
            url in render_page_with_javascript._results_cache):
            
            result = render_page_with_javascript._results_cache[url]
            forms = result['forms']
            
            if not forms:
                return f"ℹ️ No forms found on {url}"
            
            response = f"📋 Forms Analysis for {url}:\n\n"
            
            for i, form in enumerate(forms, 1):
                response += f"📝 Form {i}:\n"
                response += f"  Action: {form['action']}\n"
                response += f"  Method: {form['method']}\n"
                response += f"  Input Fields: {len(form['inputs'])}\n"
                
                if form['inputs']:
                    response += f"  Parameters:\n"
                    for input_field in form['inputs']:
                        required = " (required)" if input_field['required'] else ""
                        response += f"    - {input_field['name']}: {input_field['type']}{required}\n"
                        if input_field['value']:
                            response += f"      Default: {input_field['value']}\n"
                
                response += "\n"
            
            return response
        else:
            return f"⚠️ No cached data for {url}. Use render_page_with_javascript first."
            
    except Exception as e:
        return f"❌ Error retrieving forms data for {url}: {str(e)}"


@function_tool
async def crawl_website(url: str, max_depth: int = 2, max_pages: int = 20) -> str:
    """
    Perform comprehensive website crawling with JavaScript rendering.
    
    This tool systematically explores a website by following links and
    rendering each page with JavaScript to discover the complete attack surface.
    
    Args:
        url: The starting URL to crawl
        max_depth: Maximum depth to crawl (default: 2)
        max_pages: Maximum number of pages to crawl (default: 20)
    
    Returns:
        Comprehensive crawling results with all discovered content
    """
    try:
        visited_urls = set()
        to_visit = [(url, 0)]  # (url, depth)
        crawl_results = {
            "pages": {},
            "total_forms": 0,
            "total_js_files": 0,
            "total_api_endpoints": 0,
            "unique_js_files": set(),
            "unique_endpoints": set()
        }
        
        base_domain = urlparse(url).netloc
        
        while to_visit and len(visited_urls) < max_pages:
            current_url, depth = to_visit.pop(0)
            
            if current_url in visited_urls or depth > max_depth:
                continue
            
            # Only crawl same domain
            if urlparse(current_url).netloc != base_domain:
                continue
                
            visited_urls.add(current_url)
            
            print(f"🔍 Crawling: {current_url} (depth: {depth})")
            
            # Render the page
            page_result = await browserless_client.render_page(current_url)
            
            crawl_results["pages"][current_url] = {
                "html": page_result["html"],
                "forms": page_result["forms"],
                "js_files": page_result["js_files"],
                "api_endpoints": page_result["api_endpoints"],
                "depth": depth
            }
            
            # Update totals
            crawl_results["total_forms"] += len(page_result["forms"])
            crawl_results["total_js_files"] += len(page_result["js_files"])
            crawl_results["total_api_endpoints"] += len(page_result["api_endpoints"])
            
            crawl_results["unique_js_files"].update(page_result["js_files"])
            crawl_results["unique_endpoints"].update(page_result["api_endpoints"])
            
            # Add discovered links for next depth level
            if depth < max_depth:
                for link in page_result["links"]:
                    if link not in visited_urls and urlparse(link).netloc == base_domain:
                        to_visit.append((link, depth + 1))
            
            # Rate limiting
            await asyncio.sleep(settings.RATE_LIMIT_DELAY)
        
        # Cache the complete crawl results
        if not hasattr(crawl_website, '_crawl_cache'):
            crawl_website._crawl_cache = {}
        crawl_website._crawl_cache[url] = crawl_results
        
        # Generate summary
        summary = f"🕸️ Website Crawl Complete for {url}:\n\n"
        summary += f"📊 Crawl Statistics:\n"
        summary += f"  - Pages crawled: {len(crawl_results['pages'])}\n"
        summary += f"  - Total forms found: {crawl_results['total_forms']}\n"
        summary += f"  - Unique JS files: {len(crawl_results['unique_js_files'])}\n"
        summary += f"  - API endpoints detected: {len(crawl_results['unique_endpoints'])}\n\n"
        
        summary += f"📄 Pages Discovered:\n"
        for page_url, page_data in crawl_results["pages"].items():
            summary += f"  - {page_url} (depth: {page_data['depth']}, forms: {len(page_data['forms'])})\n"
        
        if crawl_results["unique_js_files"]:
            summary += f"\n📜 JavaScript Files:\n"
            for js_file in list(crawl_results["unique_js_files"])[:5]:
                summary += f"  - {js_file}\n"
            if len(crawl_results["unique_js_files"]) > 5:
                summary += f"  ... and {len(crawl_results['unique_js_files']) - 5} more\n"
        
        summary += f"\n💡 Complete website data cached for security analysis by other components."
        
        return summary
        
    except Exception as e:
        return f"❌ Website crawl failed for {url}: {str(e)}"


@function_tool
async def render(url: str, wait_time: int = 3000) -> str:
    """
    Render a webpage and return the complete HTML content.
    
    This tool provides rendered HTML content that other components can analyze
    without needing direct browserless access. The HTML includes content 
    generated by JavaScript execution.
    
    Args:
        url: The webpage URL to render
        wait_time: Time to wait for JavaScript execution in milliseconds (default: 3000)
    
    Returns:
        The complete rendered HTML content
    """
    try:
        from .service import crawl_service
        
        result = await crawl_service.simple_render(url)
        
        if result['status'] == 'completed' and result.get('html_content'):
            # Cache the result for other tools to access
            if not hasattr(render, '_render_cache'):
                render._render_cache = {}
            render._render_cache[url] = result
            
            return result['html_content']
        else:
            error = result.get('error', 'Unknown error')
            return f"⚠️ Failed to render {url}: {error}"
            
    except Exception as e:
        return f"❌ Failed to render {url}: {str(e)}"


@function_tool
def get_crawl_data(url: str) -> str:
    """
    Get cached crawl data for a website.
    
    Retrieves the complete crawl results including all pages, forms, JS files,
    and API endpoints discovered during website crawling.
    
    Args:
        url: The base URL that was crawled
    
    Returns:
        Complete crawl data for use by other security components
    """
    try:
        if (hasattr(crawl_website, '_crawl_cache') and 
            url in crawl_website._crawl_cache):
            
            crawl_data = crawl_website._crawl_cache[url]
            
            # Return structured data that other components can use
            result = f"🕸️ Crawl Data for {url}:\n\n"
            
            for page_url, page_data in crawl_data["pages"].items():
                result += f"📄 Page: {page_url}\n"
                result += f"HTML Content: {len(page_data['html'])} characters\n"
                result += f"Forms: {len(page_data['forms'])}\n"
                result += f"JS Files: {len(page_data['js_files'])}\n"
                result += f"API Endpoints: {len(page_data['api_endpoints'])}\n\n"
            
            return result
        else:
            return f"⚠️ No crawl data found for {url}. Run crawl_website first."
            
    except Exception as e:
        return f"❌ Error retrieving crawl data for {url}: {str(e)}" 