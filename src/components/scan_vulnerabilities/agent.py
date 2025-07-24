"""Vulnerability Agent - The Penetration Tester (Stub Implementation)"""

from agents import Agent
from .config import VULNERABILITY_AGENT_INSTRUCTIONS
from ...core.config import settings


class VulnerabilityAgent:
    """The Penetration Tester - Specialized agent for vulnerability assessment"""
    
    def __init__(self):
        self.agent = Agent(
            name="VulnerabilityAgent",
            instructions=VULNERABILITY_AGENT_INSTRUCTIONS,
            model=settings.OPENAI_MODEL
        ) 