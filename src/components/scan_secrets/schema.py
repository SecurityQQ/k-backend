"""Data models for secrets scanning component"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, HttpUrl, validator
from datetime import datetime
from enum import Enum


class SecretType(str, Enum):
    """Types of secrets that can be detected"""
    AWS_ACCESS_KEY = "aws_access_key"
    AWS_SECRET_KEY = "aws_secret_key"
    GITHUB_TOKEN = "github_token"
    OPENAI_API_KEY = "openai_api_key"
    STRIPE_KEY = "stripe_key"
    GOOGLE_API_KEY = "google_api_key"
    JWT_TOKEN = "jwt_token"
    PRIVATE_KEY = "private_key"
    DATABASE_URL = "database_url"
    API_KEY_GENERIC = "api_key_generic"


class SeverityLevel(str, Enum):
    """Severity levels for found secrets"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class SecretMatch(BaseModel):
    """Individual secret match found during scanning"""
    secret_type: SecretType
    matched_text: str
    confidence: float  # 0.0 to 1.0
    location: str  # URL or file path where found
    line_number: Optional[int] = None
    context: Optional[str] = None  # Surrounding text for context
    severity: SeverityLevel
    is_verified: bool = False
    verification_error: Optional[str] = None
    timestamp: datetime = datetime.now()
    
    @validator('confidence')
    def validate_confidence(cls, v):
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v


class ScanTarget(BaseModel):
    """Target for secrets scanning"""
    url: HttpUrl
    max_depth: int = 3
    include_subdomains: bool = False
    scan_js_files: bool = True
    scan_source_maps: bool = True
    scan_git_files: bool = True
    verify_secrets: bool = False  # Whether to attempt verification
    
    class Config:
        schema_extra = {
            "example": {
                "url": "https://example.com",
                "max_depth": 3,
                "include_subdomains": False,
                "scan_js_files": True,
                "scan_source_maps": True,
                "scan_git_files": True,
                "verify_secrets": False
            }
        }


class ScanResult(BaseModel):
    """Complete result from secrets scanning"""
    target: ScanTarget
    scan_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "in_progress"
    total_matches: int = 0
    matches_by_severity: Dict[SeverityLevel, int] = {}
    matches: List[SecretMatch] = []
    pages_scanned: int = 0
    files_scanned: int = 0
    error: Optional[str] = None
    
    def add_match(self, match: SecretMatch):
        """Add a secret match to the results"""
        self.matches.append(match)
        self.total_matches += 1
        
        # Update severity counts
        if match.severity not in self.matches_by_severity:
            self.matches_by_severity[match.severity] = 0
        self.matches_by_severity[match.severity] += 1
    
    def get_critical_matches(self) -> List[SecretMatch]:
        """Get only critical severity matches"""
        return [m for m in self.matches if m.severity == SeverityLevel.CRITICAL]
    
    def get_summary(self) -> str:
        """Get a human-readable summary of findings"""
        if self.total_matches == 0:
            return "✅ No exposed secrets found"
        
        critical = self.matches_by_severity.get(SeverityLevel.CRITICAL, 0)
        high = self.matches_by_severity.get(SeverityLevel.HIGH, 0)
        medium = self.matches_by_severity.get(SeverityLevel.MEDIUM, 0)
        
        summary = f"🚨 Found {self.total_matches} potential secrets"
        if critical > 0:
            summary += f" ({critical} critical"
            if high > 0 or medium > 0:
                summary += f", {high} high, {medium} medium"
            summary += ")"
        elif high > 0:
            summary += f" ({high} high, {medium} medium)"
        elif medium > 0:
            summary += f" ({medium} medium)"
        
        return summary


class VerificationRequest(BaseModel):
    """Request to verify if a found secret is valid"""
    secret_type: SecretType
    secret_value: str
    context: Optional[str] = None


class VerificationResult(BaseModel):
    """Result of secret verification"""
    is_valid: bool
    confidence: float
    method_used: str
    error: Optional[str] = None
    timestamp: datetime = datetime.now()


class ScanSecretsChatRequest(BaseModel):
    """Request for conversational interaction with secrets agent"""
    message: str
    session_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None


class ScanSecretsChatResponse(BaseModel):
    """Response from secrets agent conversation"""
    response: str
    session_id: str
    findings_summary: Optional[str] = None
    actions_taken: List[str] = []
    timestamp: datetime = datetime.now() 