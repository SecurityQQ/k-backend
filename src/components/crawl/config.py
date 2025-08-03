# HTTP Configuration
class HttpConfig:
    USER_AGENT = "CrawlBot/1.0"
    SUCCESS_STATUS = 200
# Crawling Limits and Timeouts
class CrawlConfig:
    MAX_URLS_PER_REQUEST = 100
    CONNECTION_LIMIT = 10
    CONNECTION_LIMIT_PER_HOST = 5
    REQUEST_TIMEOUT_SECONDS = 30
    
    # Default crawling parameters
    DEFAULT_MAX_PAGES = 50
    DEFAULT_MAX_DEPTH = 3
    DEFAULT_DELAY_BETWEEN_REQUESTS = 1.0  # seconds
    DEFAULT_RESPECT_ROBOTS_TXT = True
    DEFAULT_FOLLOW_REDIRECTS = True


# Sitemap Discovery Configuration
class SitemapConfig:
    COMMON_SITEMAP_PATHS = [
        "/sitemap.xml",
        "/sitemap_index.xml", 
        "/sitemaps.xml",
        "/sitemap1.xml",
        "/wp-sitemap.xml",  # WordPress
        "/sitemap-index.xml"
    ]
    SITEMAP_NAMESPACE = "http://www.sitemaps.org/schemas/sitemap/0.9"
    ROBOTS_TXT_PATH = "/robots.txt"
