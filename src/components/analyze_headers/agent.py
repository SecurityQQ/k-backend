"""Header Analysis Agent - The Configuration Expert (Stub Implementation)"""

from agents import Agent
from .config import HEADER_ANALYSIS_AGENT_INSTRUCTIONS
from ...core.config import settings


class HeaderAnalysisAgent:
    """The Configuration Expert - Specialized agent for security header analysis"""
    
    def __init__(self):
        self.agent = Agent(
            name="HeaderAnalysisAgent",
            instructions=HEADER_ANALYSIS_AGENT_INSTRUCTIONS,
            model=settings.OPENAI_MODEL
        ) 