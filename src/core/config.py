"""Core configuration for K-Scan Security Audit System"""

import os
from typing import Dict, List, Optional
from pydantic import validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Main application settings"""
    
    # API Configuration
    OPENAI_API_KEY: str
    BROWSERLESS_TOKEN: Optional[str] = None
    BROWSERLESS_URL: str = "https://production-sfo.browserless.io"
    
    # Application Settings
    APP_NAME: str = "K-Scan Security Audit System"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    
    # Security Settings
    MAX_SCAN_DEPTH: int = 3
    MAX_PAGES_PER_SCAN: int = 100
    SCAN_TIMEOUT: int = 300  # 5 minutes
    RATE_LIMIT_DELAY: float = 1.0  # seconds between requests
    
    # Component Settings
    ENABLE_SECRETS_SCAN: bool = True
    ENABLE_VULNERABILITY_SCAN: bool = True
    ENABLE_HEADER_ANALYSIS: bool = True
    ENABLE_CRAWLING: bool = True
    ENABLE_REPORTING: bool = True
    
    # Database Settings (for session storage)
    DATABASE_URL: str = "data/k_scan.db"
    
    # API Settings
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_RELOAD: bool = False
    
    # AI Model Settings
    OPENAI_MODEL: str = "gpt-4o"
    OPENAI_MODEL_TEMPERATURE: float = 0.1
    OPENAI_MAX_TOKENS: Optional[int] = None
    
    class Config:
        env_file = ".env"
        case_sensitive = True
    
    @validator('OPENAI_API_KEY')
    def validate_openai_key(cls, v):
        if not v:
            raise ValueError('OPENAI_API_KEY is required')
        return v


# Note: Component-specific configurations (secrets patterns, vulnerability payloads, etc.)
# are now located in their respective component config.py files:
# - src/components/scan_secrets/config.py - Secret patterns and scanning configuration
# - src/components/scan_vulnerabilities/config.py - Vulnerability payloads and testing config
# - src/components/analyze_headers/config.py - Security headers and SSL/TLS config
# - src/components/crawl_website/config.py - Crawling patterns and settings
# - src/components/generate_report/config.py - Report templates and risk scoring

# Initialize settings
settings = Settings()

# Configuration loaded successfully
print(f"🔧 K-Scan Config: {settings.APP_NAME} v{settings.VERSION}")
print(f"   - Browserless: {'✅' if settings.BROWSERLESS_TOKEN else '❌'} ({settings.BROWSERLESS_URL})")
print(f"   - OpenAI: {'✅' if settings.OPENAI_API_KEY else '❌'}") 