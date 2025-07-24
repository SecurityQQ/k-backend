"""Main FastAPI application for K-Scan Security Audit System"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import uuid

from .core.config import settings
from .core.orchestrator import orchestrator, AuditResult
from .components.scan_secrets.routes import router as secrets_router
from .components.crawl_website.routes import router as crawl_router


# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    description="""
    🔒 K-Scan Security Audit System
    
    An intelligent, multi-component security audit system built with OpenAI Agents SDK.
    The system automatically scans websites and web applications for vulnerabilities using
    specialized AI agents that can crawl content, detect security issues, and generate
    comprehensive reports.
    
    ## 🚀 Key Features
    
    - **🔑 Secrets Detection**: Find exposed API keys, tokens, and credentials
    - **🕸️ Intelligent Crawling**: JavaScript-enabled website exploration  
    - **🛡️ Vulnerability Testing**: XSS, SQL injection, CSRF detection
    - **📊 Security Headers**: OWASP compliance analysis
    - **📋 Smart Reporting**: AI-generated executive summaries
    
    ## 🤖 AI Agent Network
    
    - **SecretScanAgent**: The Paranoid Investigator (credential detection)
    - **CrawlerAgent**: The Explorer (website mapping)
    - **VulnerabilityAgent**: The Penetration Tester (security testing)
    - **HeaderAnalysisAgent**: The Configuration Expert (header analysis)
    - **ReportAgent**: The Communicator (intelligent reporting)
    
    ## 🔧 Usage
    
    1. **Quick Scan**: `/audit/quick?url=https://example.com`
    2. **Full Audit**: `POST /audit/complete` with detailed configuration
    3. **Component Access**: Use individual component endpoints for targeted scans
    4. **Agent Chat**: Conversational security analysis with specialized agents
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(secrets_router)
app.include_router(crawl_router)

# Store for ongoing audits
active_audits: Dict[str, AuditResult] = {}


@app.get("/")
async def root():
    """Welcome message and system status"""
    return {
        "message": "🔒 Welcome to K-Scan Security Audit System",
        "version": settings.VERSION,
        "status": "operational",
        "components": {
            "scan_secrets": "✅ Active - API key and credential detection",
            "crawl_website": "✅ Active - Intelligent website crawling",
            "scan_vulnerabilities": "🚧 Coming Soon - Vulnerability testing",
            "analyze_headers": "🚧 Coming Soon - Security header analysis", 
            "generate_report": "🚧 Coming Soon - AI report generation"
        },
        "capabilities": [
            "Multi-agent security orchestration",
            "JavaScript-enabled website crawling",
            "Comprehensive secrets detection",
            "Intelligent vulnerability assessment",
            "AI-powered report generation"
        ],
        "quick_start": {
            "quick_scan": "GET /audit/quick?url=https://example.com",
            "full_audit": "POST /audit/complete",
            "agent_chat": "POST /scan_secrets/agent",
            "crawl_website": "POST /crawl_website/quick_crawl",
            "test_crawler": "GET /crawl_website/test",
            "documentation": "/docs"
        }
    }


@app.get("/audit/quick")
async def quick_security_audit(url: str):
    """
    Perform a quick security audit focusing on immediate risks
    
    This endpoint provides rapid assessment of obvious security issues:
    - Exposed API keys and credentials
    - Basic security header analysis
    - Git repository exposure check
    
    Perfect for initial triage and immediate risk assessment.
    """
    try:
        audit_id = str(uuid.uuid4())
        
        print(f"🚀 Starting quick audit for {url}")
        
        # For now, focus on secrets scanning as it's the most critical
        result = await orchestrator.run_single_component(
            "scan_secrets",
            url,
            f"Perform a quick security scan of {url}. Focus on finding any exposed "
            f"API keys, credentials, or obvious security issues. Check for git exposure "
            f"and provide immediate risk assessment.",
            session_id=audit_id
        )
        
        return {
            "audit_id": audit_id,
            "status": "completed",
            "target_url": url,
            "audit_type": "quick_scan",
            "components_run": ["scan_secrets"],
            "summary": result,
            "recommendations": [
                "Review any critical findings immediately",
                "Consider running a full comprehensive audit",
                "Implement secret scanning in CI/CD pipeline"
            ],
            "next_steps": {
                "full_audit": f"POST /audit/complete with target: {url}",
                "component_details": "GET /scan_secrets/capabilities"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick audit failed: {str(e)}")


@app.post("/audit/complete")
async def complete_security_audit(
    target_url: str,
    components: Optional[List[str]] = None,
    deep_scan: bool = True,
    verify_secrets: bool = False
):
    """
    Run a complete, comprehensive security audit
    
    This endpoint orchestrates all available security components for thorough analysis:
    - Website crawling and mapping
    - Comprehensive secrets detection  
    - Vulnerability testing (XSS, SQLi, CSRF)
    - Security header analysis
    - Intelligent report generation
    
    Args:
        target_url: The website URL to audit
        components: Optional list of specific components to run
        deep_scan: Whether to perform deep analysis (recommended)
        verify_secrets: Whether to verify found secrets (use carefully)
    """
    try:
        audit_id = str(uuid.uuid4())
        
        print(f"🔍 Starting complete security audit for {target_url}")
        
        # Run the complete audit through orchestrator
        result = await orchestrator.run_complete_audit(
            target_url=target_url,
            scan_id=audit_id,
            components=components,
            session_id=audit_id
        )
        
        # Store result
        active_audits[audit_id] = result
        
        return {
            "audit_id": audit_id,
            "status": result.status,
            "target_url": result.target_url,
            "start_time": result.start_time.isoformat(),
            "end_time": result.end_time.isoformat() if result.end_time else None,
            "audit_duration": (result.end_time - result.start_time).total_seconds() if result.end_time else None,
            "components_analyzed": len(result.findings) if result.findings else 0,
            "summary": result.summary,
            "findings_overview": result.findings if result.findings else {},
            "error": result.error,
            "next_steps": {
                "detailed_results": f"GET /audit/{audit_id}",
                "component_details": "Access individual component endpoints"
            }
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Complete audit failed: {str(e)}")


@app.get("/audit/{audit_id}")
async def get_audit_results(audit_id: str):
    """Get detailed results from a completed security audit"""
    if audit_id not in active_audits:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    result = active_audits[audit_id]
    
    return {
        "audit_id": audit_id,
        "target_url": result.target_url,
        "status": result.status,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "audit_duration": (result.end_time - result.start_time).total_seconds() if result.end_time else None,
        "findings": result.findings,
        "summary": result.summary,
        "report_url": result.report_url,
        "error": result.error
    }


@app.get("/components")
async def list_components():
    """Get information about all available security components"""
    return {
        "total_components": 5,
        "active_components": 2,
        "components": {
            "scan_secrets": {
                "status": "active",
                "name": "Secrets Scanner",
                "agent": "SecretScanAgent (The Paranoid Investigator)",
                "capabilities": ["API key detection", "Git exposure check", "Source map analysis"],
                "endpoints": ["/scan_secrets/scan", "/scan_secrets/agent", "/scan_secrets/quick_scan"]
            },
            "crawl_website": {
                "status": "active",
                "name": "Website Crawler",
                "agent": "CrawlerAgent (The Explorer)",
                "capabilities": ["JavaScript rendering", "Form discovery", "Endpoint enumeration"],
                "endpoints": ["/crawl_website/crawl", "/crawl_website/quick_crawl", "/crawl_website/render", "/crawl_website/agent", "/crawl_website/test"]
            },
            "scan_vulnerabilities": {
                "status": "coming_soon", 
                "name": "Vulnerability Scanner",
                "agent": "VulnerabilityAgent (The Penetration Tester)",
                "capabilities": ["XSS testing", "SQL injection", "CSRF analysis"],
                "endpoints": ["Coming soon"]
            },
            "analyze_headers": {
                "status": "coming_soon",
                "name": "Security Headers Analyzer", 
                "agent": "HeaderAnalysisAgent (The Configuration Expert)",
                "capabilities": ["OWASP compliance", "SSL analysis", "Cookie security"],
                "endpoints": ["Coming soon"]
            },
            "generate_report": {
                "status": "coming_soon",
                "name": "Report Generator",
                "agent": "ReportAgent (The Communicator)",
                "capabilities": ["Executive summaries", "Risk prioritization", "Remediation guidance"],
                "endpoints": ["Coming soon"]
            }
        }
    }


@app.get("/health")
async def health_check():
    """System health check"""
    return {
        "status": "healthy",
        "system": "K-Scan Security Audit System",
        "version": settings.VERSION,
        "active_components": ["scan_secrets", "crawl_website"],
        "active_audits": len(active_audits),
        "configuration": {
            "openai_configured": bool(settings.OPENAI_API_KEY),
            "browserless_configured": bool(settings.BROWSERLESS_TOKEN),
            "debug_mode": settings.DEBUG
        }
    }


@app.delete("/audit/{audit_id}")
async def delete_audit_result(audit_id: str):
    """Delete a stored audit result"""
    if audit_id not in active_audits:
        raise HTTPException(status_code=404, detail="Audit not found")
    
    del active_audits[audit_id]
    return {"message": f"Audit {audit_id} deleted successfully"}


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize the application"""
    print(f"🚀 Starting {settings.APP_NAME} v{settings.VERSION}")
    print(f"🔧 OpenAI API configured: {'✅' if settings.OPENAI_API_KEY else '❌'}")
    print(f"🌐 Browserless configured: {'✅' if settings.BROWSERLESS_TOKEN else '❌'}")
    print(f"📊 Debug mode: {'✅' if settings.DEBUG else '❌'}")
    
    # Initialize database
    await _initialize_database()
    
    print(f"🎯 Ready to perform security audits!")


async def _initialize_database():
    """Initialize SQLite database and ensure directory exists"""
    import os
    from pathlib import Path
    
    try:
        # Get database file path (now directly a path, not URL)
        db_path = settings.DATABASE_URL
        
        # Create directory if it doesn't exist
        db_file = Path(db_path)
        db_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Create database file if it doesn't exist
        if not db_file.exists():
            db_file.touch()
            print(f"📁 Created database file: {db_path}")
        else:
            print(f"📁 Database file exists: {db_path}")
            
        # Test database connection
        from agents import SQLiteSession
        test_session = SQLiteSession("startup_test", db_path)
        print(f"✅ Database connection verified")
        
    except Exception as e:
        print(f"⚠️  Database initialization warning: {e}")
        print(f"   The application will attempt to create the database on first use")


# CLI entry point
def main():
    """Main entry point for running the application"""
    uvicorn.run(
        "src.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_RELOAD or settings.DEBUG,
        log_level="info"
    )


if __name__ == "__main__":
    main() 