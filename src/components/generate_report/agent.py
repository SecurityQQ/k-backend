"""Report Agent - The Communicator (Stub Implementation)"""

from agents import Agent
from .config import REPORT_AGENT_INSTRUCTIONS
from ...core.config import settings


class ReportAgent:
    """The Communicator - Specialized agent for intelligent report generation"""
    
    def __init__(self):
        self.agent = Agent(
            name="ReportAgent",
            instructions=REPORT_AGENT_INSTRUCTIONS,
            model=settings.OPENAI_MODEL
        ) 