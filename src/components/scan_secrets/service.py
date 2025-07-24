"""Business logic service for secrets scanning"""

import asyncio
import uuid
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import urljoin, urlparse

from .schema import SecretMatch, VerificationResult
from .client import SecretScanner, SecretVerificationClient
from ...core.config import settings


class SecretscanService:
    """Main service for coordinating secrets scanning operations"""
    
    def __init__(self):
        self.scanner = SecretScanner()
        self.verification_client = SecretVerificationClient()
    
    def scan_content_for_secrets(self, content: str, source_location: str = "provided_content") -> List[SecretMatch]:
        """
        Scan provided content for secrets
        
        Args:
            content: The content to scan for secrets
            source_location: Description of where the content came from
        
        Returns:
            List of SecretMatch objects found in the content
        """
        try:
            return self.scanner.scan_content(content, source_location)
        except Exception as e:
            print(f"❌ Error scanning content from {source_location}: {e}")
            return []
    
    def analyze_matches(self, matches: List[SecretMatch]) -> Dict[str, Any]:
        """
        Analyze secret matches and provide intelligence
        
        Args:
            matches: List of SecretMatch objects to analyze
        
        Returns:
            Analysis with insights and recommendations
        """
        analysis = {
            "risk_assessment": "low",
            "recommendations": [],
            "patterns": {},
            "most_critical": [],
        }
        
        if not matches:
            analysis["risk_assessment"] = "low"
            analysis["recommendations"].append("✅ No exposed secrets detected")
            return analysis
        
        critical_matches = [m for m in matches if m.severity.value == "critical"]
        
        if critical_matches:
            analysis["risk_assessment"] = "critical"
            analysis["most_critical"] = [
                {
                    "type": match.secret_type.value,
                    "location": match.location,
                    "confidence": match.confidence
                }
                for match in critical_matches[:5]  # Top 5 most critical
            ]
            
            analysis["recommendations"].extend([
                "🚨 IMMEDIATE ACTION REQUIRED: Critical secrets exposed",
                "1. Revoke/rotate all exposed API keys immediately",
                "2. Remove secrets from code and use environment variables",
                "3. Audit git history for secret exposure",
                "4. Implement secret scanning in CI/CD pipeline"
            ])
        
        elif any(m.severity.value == "high" for m in matches):
            analysis["risk_assessment"] = "high"
            analysis["recommendations"].extend([
                "⚠️  High-risk secrets detected",
                "1. Review and verify all detected secrets",
                "2. Implement proper secret management",
                "3. Add secrets to .gitignore patterns"
            ])
        
        else:
            analysis["risk_assessment"] = "medium"
            analysis["recommendations"].append("🔍 Review detected patterns and improve secret handling")
        
        # Analyze patterns
        secret_types = {}
        for match in matches:
            secret_type = match.secret_type.value
            if secret_type not in secret_types:
                secret_types[secret_type] = 0
            secret_types[secret_type] += 1
        
        analysis["patterns"] = secret_types
        
        return analysis


# Global service instance
secrets_service = SecretscanService() 