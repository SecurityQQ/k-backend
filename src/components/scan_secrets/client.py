"""External API client for secrets scanning"""

import asyncio
import aiohttp
import re
from typing import List, Dict, Optional, Tuple
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from .schema import SecretMatch, SecretType, SeverityLevel, VerificationResult
from ...core.config import settings


# BrowserlessClient moved to crawl_website component
# This maintains better separation of concerns between components


class SecretVerificationClient:
    """Client for verifying found secrets"""
    
    async def verify_github_token(self, token: str) -> VerificationResult:
        """Verify if a GitHub token is valid"""
        headers = {
            "Authorization": f"token {token}",
            "User-Agent": "K-Scan-Security-Audit"
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.github.com/user", headers=headers) as response:
                    is_valid = response.status == 200
                    return VerificationResult(
                        is_valid=is_valid,
                        confidence=1.0 if is_valid else 0.0,
                        method_used="GitHub API /user endpoint"
                    )
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                confidence=0.0,
                method_used="GitHub API /user endpoint",
                error=str(e)
            )
    
    async def verify_openai_key(self, api_key: str) -> VerificationResult:
        """Verify if an OpenAI API key is valid"""
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "test"}],
            "max_tokens": 1
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "https://api.openai.com/v1/chat/completions", 
                    json=payload, 
                    headers=headers
                ) as response:
                    is_valid = response.status in [200, 400]  # 400 means key is valid but request invalid
                    return VerificationResult(
                        is_valid=is_valid,
                        confidence=1.0 if is_valid else 0.0,
                        method_used="OpenAI API test request"
                    )
        except Exception as e:
            return VerificationResult(
                is_valid=False,
                confidence=0.0,
                method_used="OpenAI API test request",
                error=str(e)
            )


# WebCrawlerClient removed - crawling functionality moved to crawl_website component
# This maintains better separation of concerns between components


class SecretScanner:
    """Core secret scanning logic"""
    
    def scan_content(self, content: str, source_url: str) -> List[SecretMatch]:
        """
        Scan content for secrets using regex patterns
        
        Args:
            content: Text content to scan
            source_url: URL or location where content was found
        
        Returns:
            List of SecretMatch objects
        """
        matches = []
        
        # Import patterns from local config to avoid circular imports
        from .config import SECRETS_PATTERNS
        
        for secret_type, pattern in SECRETS_PATTERNS.items():
            regex_matches = re.finditer(pattern, content, re.IGNORECASE)
            
            for match in regex_matches:
                # Get context around the match
                start = max(0, match.start() - 50)
                end = min(len(content), match.end() + 50)
                context = content[start:end]
                
                # Calculate line number
                line_number = content[:match.start()].count('\n') + 1
                
                # Calculate confidence based on secret type and context
                confidence = self._calculate_confidence(secret_type, match.group(), context)
                
                # Determine severity
                severity = self._determine_severity(secret_type, confidence)
                
                secret_match = SecretMatch(
                    secret_type=SecretType(secret_type),
                    matched_text=match.group(),
                    confidence=confidence,
                    location=source_url,
                    line_number=line_number,
                    context=context,
                    severity=severity
                )
                
                matches.append(secret_match)
        
        return matches
    
    def _calculate_confidence(self, secret_type: str, matched_text: str, context: str) -> float:
        """Calculate confidence score for a secret match"""
        base_confidence = 0.7
        
        # Increase confidence for well-formed secrets
        if secret_type == "aws_access_key" and matched_text.startswith("AKIA"):
            base_confidence = 0.9
        elif secret_type == "github_token" and matched_text.startswith("gh"):
            base_confidence = 0.95
        elif secret_type == "openai_api_key" and matched_text.startswith("sk-"):
            base_confidence = 0.95
        
        # Decrease confidence if found in comments or documentation
        if any(indicator in context.lower() for indicator in ["example", "demo", "test", "placeholder"]):
            base_confidence *= 0.5
        
        # Increase confidence if in configuration contexts
        if any(indicator in context.lower() for indicator in ["config", "env", "key", "token", "secret"]):
            base_confidence = min(1.0, base_confidence * 1.2)
        
        return round(base_confidence, 2)
    
    def _determine_severity(self, secret_type: str, confidence: float) -> SeverityLevel:
        """Determine severity level for a secret match"""
        if confidence >= 0.8:
            if secret_type in ["aws_access_key", "aws_secret_key", "private_key"]:
                return SeverityLevel.CRITICAL
            elif secret_type in ["github_token", "openai_api_key", "stripe_key"]:
                return SeverityLevel.CRITICAL
            else:
                return SeverityLevel.HIGH
        elif confidence >= 0.6:
            return SeverityLevel.HIGH
        elif confidence >= 0.4:
            return SeverityLevel.MEDIUM
        else:
            return SeverityLevel.LOW 