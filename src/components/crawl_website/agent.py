"""Crawler Agent - The Explorer (Implementation)"""

from agents import Agent
from .config import CRAWLER_AGENT_INSTRUCTIONS
from .tools import (
    render_page_with_javascript,
    get_page_content,
    get_javascript_files,
    get_forms_data,
    crawl_website,
    get_crawl_data
)
from ...core.config import settings


class CrawlerAgent:
    """The Explorer - Specialized agent for website crawling and discovery"""
    
    def __init__(self):
        self.agent = Agent(
            name="CrawlerAgent", 
            instructions=CRAWLER_AGENT_INSTRUCTIONS,
            tools=[
                render_page_with_javascript,
                get_page_content,
                get_javascript_files,
                get_forms_data,
                crawl_website,
                get_crawl_data
            ],
            model=settings.OPENAI_MODEL
        ) 