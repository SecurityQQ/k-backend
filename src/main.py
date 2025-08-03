"""Main FastAPI application for K-Scan Security Audit System"""

import asyncio
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Any, Optional, List
import uuid

from .core.config import settings
from .components.auth.routes import router as auth_router
from .components.crawl.routes import router as crawl_router
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

app.include_router(auth_router)
app.include_router(crawl_router)
@app.get("/")
async def root():
    """Welcome message and system status"""
    return {
        "message": "🔒 Welcome to K-Scan Security Audit System",
        "version": settings.VERSION,
        "status": "operational",
        "components": {
        },
        "capabilities": [
        ],
        "quick_start": {
        }
    }

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