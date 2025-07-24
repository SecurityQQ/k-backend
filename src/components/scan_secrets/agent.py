"""Specialized agent for secrets scanning and detection"""

from agents import Agent
from typing import Optional

from .tools import (
    scan_html_content_for_secrets,
    scan_javascript_content_for_secrets,
    verify_api_key,
    check_git_exposure,
    scan_source_maps_for_secrets,
    get_secret_patterns,
    analyze_secrets_in_content
)
from ..crawl_website.tools import (
    get_page_content,
    get_javascript_files,
    get_crawl_data,
    render
)
from .config import SECRETS_AGENT_INSTRUCTIONS
from ...core.config import settings


class SecretScanAgent:
    """The Paranoid Investigator - Specialized agent for finding exposed credentials"""
    
    def __init__(self):
        self.agent = Agent(
            name="SecretScanAgent",
            instructions=SECRETS_AGENT_INSTRUCTIONS,
            tools=[
                # Content analysis tools
                scan_html_content_for_secrets,
                scan_javascript_content_for_secrets,
                analyze_secrets_in_content,
                # Content retrieval tools (from crawl_website)
                # get_page_content,
                # get_javascript_files,
                # get_crawl_data,
                render,
                # Security testing tools
                verify_api_key,
                check_git_exposure,
                scan_source_maps_for_secrets,
                # Information tools
                get_secret_patterns
            ],
            model=settings.OPENAI_MODEL
        )
    
    def get_capabilities(self) -> dict:
        """Get information about this agent's capabilities"""
        return {
            "name": "SecretScanAgent",
            "role": "The Paranoid Investigator",
            "specialization": "API Key and Credential Detection",
            "primary_focus": "Finding exposed credentials and sensitive data",
            "personality": "Thorough, suspicious, never misses obvious exposures",
            "strengths": ["Pattern recognition", "Evidence gathering", "Critical risk identification"],
            "tools": [
                {
                    "name": "scan_for_secrets",
                    "description": "Comprehensive secrets scanning with multiple detection methods",
                    "use_case": "Primary tool for finding exposed API keys and credentials"
                },
                {
                    "name": "verify_api_key", 
                    "description": "Verify if found secrets are valid and active",
                    "use_case": "Confirm critical findings and assess real impact"
                },
                {
                    "name": "check_git_exposure",
                    "description": "Check for exposed .git directories",
                    "use_case": "Critical security issue - exposed source code"
                },
                {
                    "name": "scan_source_maps",
                    "description": "Analyze JavaScript source maps for secrets",
                    "use_case": "Find secrets in development artifacts"
                },
                {
                    "name": "get_secret_patterns",
                    "description": "Information about detectable secret types",
                    "use_case": "Understanding detection capabilities"
                },
                {
                    "name": "quick_secret_check",
                    "description": "Fast initial assessment for obvious exposures",
                    "use_case": "Rapid triage and initial scanning"
                }
            ],
            "typical_workflow": [
                "1. Quick initial scan to assess obvious exposures",
                "2. Deep comprehensive scan of all resources",
                "3. Git exposure check for critical findings",
                "4. Source map analysis for development secrets",
                "5. Verification of critical findings (if requested)",
                "6. Risk assessment and prioritized recommendations"
            ]
        }


# Example usage and testing functions
async def test_secret_agent():
    """Test function for the SecretScanAgent"""
    from agents import Runner, SQLiteSession
    
    agent = SecretScanAgent()
    session = SQLiteSession("test_secrets_scan")
    
    # Test query
    test_message = "Scan https://example.com for any exposed API keys or credentials. Focus on JavaScript files and check for git exposure."
    
    result = await Runner.run(agent.agent, test_message, session=session)
    print("Secret Scan Agent Test Result:")
    print(result.final_output)
    
    return result


if __name__ == "__main__":
    import asyncio
    asyncio.run(test_secret_agent()) 