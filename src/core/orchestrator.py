"""Main Orchestrator Agent for K-Scan Security Audit System"""

import asyncio
from typing import Dict, List, Optional, Any
from agents import Agent, Runner, SQLiteSession
from dataclasses import dataclass
from datetime import datetime

from ..components.scan_secrets.agent import SecretScanAgent
from ..components.crawl_website.agent import CrawlerAgent
from ..components.scan_vulnerabilities.agent import VulnerabilityAgent
from ..components.analyze_headers.agent import HeaderAnalysisAgent
from ..components.generate_report.agent import ReportAgent
from .config import settings


@dataclass
class AuditResult:
    """Complete audit result from all components"""
    target_url: str
    scan_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"
    findings: Dict[str, Any] = None
    summary: Optional[str] = None
    report_url: Optional[str] = None
    error: Optional[str] = None


class SecurityAuditOrchestrator:
    """Main orchestrator that coordinates all security audit agents"""
    
    def __init__(self):
        self.crawler_agent = CrawlerAgent()
        self.secrets_agent = SecretScanAgent()
        self.vulnerability_agent = VulnerabilityAgent()
        self.header_agent = HeaderAnalysisAgent()
        self.report_agent = ReportAgent()
        
        # Main orchestrator agent
        self.orchestrator = Agent(
            name="Security Audit Orchestrator",
            instructions=self._get_orchestrator_instructions(),
            model=settings.OPENAI_MODEL,
        )
    
    def _get_orchestrator_instructions(self) -> str:
        """Get orchestrator agent instructions"""
        return """
        You are the master coordinator for K-Scan security audits.
        
        Your responsibilities:
        1. Coordinate the security audit workflow across all specialized agents
        2. Make intelligent decisions about scan scope and priorities
        3. Handle errors and retries gracefully
        4. Provide clear status updates throughout the process
        5. Ensure comprehensive coverage while respecting rate limits
        
        Workflow:
        1. First, use the crawler to map the target application
        2. Based on findings, coordinate parallel security scans:
           - Secret scanning (highest priority - run immediately)
           - Vulnerability testing (focus on discovered forms/endpoints)
           - Header analysis (run on all discovered pages)
        3. Aggregate all findings and generate comprehensive report
        4. Provide executive summary with prioritized recommendations
        
        Always prioritize critical security issues and provide actionable insights.
        """
    
    async def run_complete_audit(
        self, 
        target_url: str, 
        scan_id: str,
        components: Optional[List[str]] = None,
        session_id: Optional[str] = None
    ) -> AuditResult:
        """
        Run a complete security audit with all components
        
        Args:
            target_url: The URL to audit
            scan_id: Unique identifier for this scan
            components: Optional list of specific components to run
            session_id: Optional session ID for conversation history
        
        Returns:
            AuditResult with complete findings
        """
        result = AuditResult(
            target_url=target_url,
            scan_id=scan_id,
            start_time=datetime.now()
        )
        
        try:
            # Create session for this audit
            print(f"🔍 Starting security audit for {target_url}")
            print(f"📋 Scan ID: {scan_id}")
            print(f"🔍 Database URL: {settings.DATABASE_URL}")
            session = SQLiteSession(session_id or scan_id, settings.DATABASE_URL)
            
            # Phase 1: Discovery and Crawling
            print(f"🔍 Starting security audit for {target_url}")
            print(f"📋 Scan ID: {scan_id}")
            
            if not components or "crawl_website" in components:
                print("🕸️  Phase 1: Website Discovery")
                crawl_result = await Runner.run(
                    self.crawler_agent.agent,
                    f"Crawl and analyze the website: {target_url}. "
                    f"Use crawl_website to discover all pages, forms, endpoints, and JavaScript content. "
                    f"Render all pages with JavaScript and cache the content for security analysis. "
                    f"Map the complete attack surface for security testing.",
                    session=session
                )
                
                result.findings = result.findings or {}
                result.findings["crawl"] = {
                    "status": "completed",
                    "summary": crawl_result.final_output,
                    "timestamp": datetime.now().isoformat()
                }
            
            # Phase 2: Parallel Security Scans
            print("🔐 Phase 2: Security Analysis")
            scan_tasks = []
            
            if not components or "scan_secrets" in components:
                print("  🔑 Scanning for exposed secrets...")
                scan_tasks.append(self._run_secrets_scan(target_url, session))
            
            if not components or "scan_vulnerabilities" in components:
                print("  🛡️  Testing for vulnerabilities...")
                scan_tasks.append(self._run_vulnerability_scan(target_url, session))
            
            if not components or "analyze_headers" in components:
                print("  📊 Analyzing security headers...")
                scan_tasks.append(self._run_header_analysis(target_url, session))
            
            # Run all security scans in parallel
            if scan_tasks:
                scan_results = await asyncio.gather(*scan_tasks, return_exceptions=True)
                
                # Process results
                for i, task_result in enumerate(scan_results):
                    if isinstance(task_result, Exception):
                        print(f"⚠️  Warning: Scan task {i} failed: {task_result}")
                    else:
                        component_name, findings = task_result
                        result.findings[component_name] = findings
            
            # Phase 3: Report Generation
            if not components or "generate_report" in components:
                print("📋 Phase 3: Report Generation")
                report_result = await Runner.run(
                    self.report_agent.agent,
                    f"Generate a comprehensive security audit report for {target_url}. "
                    f"Analyze all findings: {result.findings}. "
                    f"Provide executive summary, technical details, and prioritized recommendations.",
                    session=session
                )
                
                result.findings["report"] = {
                    "status": "completed",
                    "content": report_result.final_output,
                    "timestamp": datetime.now().isoformat()
                }
                result.summary = report_result.final_output
            
            result.status = "completed"
            result.end_time = datetime.now()
            
            # Generate final summary
            duration = (result.end_time - result.start_time).total_seconds()
            print(f"✅ Security audit completed in {duration:.1f} seconds")
            print(f"📊 Results: {len(result.findings)} components analyzed")
            
            return result
            
        except Exception as e:
            result.status = "failed"
            result.error = str(e)
            result.end_time = datetime.now()
            print(f"❌ Audit failed: {e}")
            return result
    
    async def _run_secrets_scan(self, target_url: str, session) -> tuple[str, Dict]:
        """Run secrets scanning component"""
        try:
            scan_result = await Runner.run(
                self.secrets_agent.agent,
                f"Analyze {target_url} for exposed API keys, tokens, and sensitive credentials. "
                f"Use the render tool to get the complete HTML content with JavaScript executed, "
                f"then analyze it using your secrets scanning tools. "
                f"Also check for git exposure using check_git_exposure with the base URL. "
                f"Focus on rendering the page directly and analyzing the resulting HTML content.",
                session=session
            )
            return "secrets", {
                "status": "completed",
                "summary": scan_result.final_output,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return "secrets", {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_vulnerability_scan(self, target_url: str, session) -> tuple[str, Dict]:
        """Run vulnerability scanning component"""
        try:
            vuln_result = await Runner.run(
                self.vulnerability_agent.agent,
                f"Test {target_url} for common web vulnerabilities. "
                f"Focus on XSS, SQL injection, CSRF, and input validation issues. "
                f"Test all discovered forms and endpoints thoroughly.",
                session=session
            )
            return "vulnerabilities", {
                "status": "completed",
                "summary": vuln_result.final_output,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return "vulnerabilities", {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def _run_header_analysis(self, target_url: str, session) -> tuple[str, Dict]:
        """Run security header analysis component"""
        try:
            header_result = await Runner.run(
                self.header_agent.agent,
                f"Analyze security headers and SSL configuration for {target_url}. "
                f"Check OWASP security header compliance, SSL certificate validity, "
                f"and overall security posture.",
                session=session
            )
            return "headers", {
                "status": "completed",
                "summary": header_result.final_output,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return "headers", {
                "status": "failed",
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            }
    
    async def run_single_component(
        self, 
        component: str, 
        target_url: str, 
        message: str,
        session_id: Optional[str] = None
    ) -> str:
        """
        Run a single security component
        
        Args:
            component: Component name (scan_secrets, crawl_website, etc.)
            target_url: Target URL
            message: Specific instructions for the agent
            session_id: Optional session ID
        
        Returns:
            Agent response
        """
        session = SQLiteSession(session_id or f"{component}_{datetime.now().timestamp()}")
        
        agent_map = {
            "scan_secrets": self.secrets_agent.agent,
            "crawl_website": self.crawler_agent.agent,
            "scan_vulnerabilities": self.vulnerability_agent.agent,
            "analyze_headers": self.header_agent.agent,
            "generate_report": self.report_agent.agent
        }
        
        if component not in agent_map:
            raise ValueError(f"Unknown component: {component}")
        
        result = await Runner.run(agent_map[component], message, session=session)
        return result.final_output


# Global orchestrator instance
orchestrator = SecurityAuditOrchestrator() 