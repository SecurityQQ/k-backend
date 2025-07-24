"""FastAPI routes for secrets scanning component"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

from .schema import (
    ScanTarget, 
    ScanResult, 
    ScanSecretsChatRequest, 
    ScanSecretsChatResponse,
    VerificationRequest,
    VerificationResult
)
from .service import secrets_service
from .agent import SecretScanAgent
from agents import Runner, SQLiteSession

# Create router for this component
router = APIRouter(prefix="/scan_secrets", tags=["Secrets Scanning"])

# Initialize agent
secrets_agent = SecretScanAgent()

# Store for ongoing scans
active_scans: Dict[str, ScanResult] = {}


@router.post("/scan", response_model=Dict[str, Any])
async def scan_for_secrets_endpoint(target: ScanTarget, background_tasks: BackgroundTasks):
    """
    Perform comprehensive secrets scanning on a target URL
    
    This endpoint initiates a full secrets scan including:
    - Main page analysis
    - JavaScript file scanning
    - Source map analysis
    - Git exposure checking
    - Optional secret verification
    """
    scan_id = str(uuid.uuid4())
    
    try:
        # Start the scan
        result = await secrets_service.scan_for_secrets(target, scan_id)
        
        # Store result for potential retrieval
        active_scans[scan_id] = result
        
        return {
            "scan_id": scan_id,
            "status": result.status,
            "target_url": str(target.url),
            "total_matches": result.total_matches,
            "matches_by_severity": result.matches_by_severity,
            "summary": result.get_summary(),
            "scan_time": (result.end_time - result.start_time).total_seconds() if result.end_time else 0,
            "pages_scanned": result.pages_scanned,
            "files_scanned": result.files_scanned,
            "critical_findings": len(result.get_critical_matches()),
            "error": result.error
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@router.get("/scan/{scan_id}", response_model=Dict[str, Any])
async def get_scan_result(scan_id: str):
    """Get detailed results from a completed scan"""
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    result = active_scans[scan_id]
    
    # Include detailed matches for completed scans
    detailed_matches = []
    for match in result.matches:
        detailed_matches.append({
            "secret_type": match.secret_type.value,
            "confidence": match.confidence,
            "location": match.location,
            "line_number": match.line_number,
            "context": match.context,
            "severity": match.severity.value,
            "is_verified": match.is_verified,
            "verification_error": match.verification_error,
            "timestamp": match.timestamp.isoformat()
        })
    
    return {
        "scan_id": scan_id,
        "target_url": str(result.target.url),
        "status": result.status,
        "start_time": result.start_time.isoformat(),
        "end_time": result.end_time.isoformat() if result.end_time else None,
        "total_matches": result.total_matches,
        "matches_by_severity": result.matches_by_severity,
        "matches": detailed_matches,
        "pages_scanned": result.pages_scanned,
        "files_scanned": result.files_scanned,
        "summary": result.get_summary(),
        "analysis": secrets_service.analyze_findings(result),
        "error": result.error
    }


@router.post("/quick_scan", response_model=Dict[str, Any])
async def quick_scan_endpoint(url: str):
    """
    Perform a quick scan for immediate feedback
    
    This is a lightweight scan that checks for obvious exposures
    without deep analysis of all JavaScript files and source maps.
    """
    try:
        result = await secrets_service.quick_scan(url)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Quick scan failed: {str(e)}")


@router.post("/verify", response_model=Dict[str, Any])
async def verify_secret_endpoint(request: VerificationRequest):
    """
    Verify if a found secret is valid and active
    
    CAUTION: This makes actual API calls to verify credentials.
    Only use with proper authorization and for legitimate security testing.
    """
    try:
        verification_client = secrets_service.verification_client
        
        if request.secret_type.value == "github_token":
            result = await verification_client.verify_github_token(request.secret_value)
        elif request.secret_type.value == "openai_api_key":
            result = await verification_client.verify_openai_key(request.secret_value)
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Verification not supported for {request.secret_type.value}"
            )
        
        return {
            "secret_type": request.secret_type.value,
            "is_valid": result.is_valid,
            "confidence": result.confidence,
            "method_used": result.method_used,
            "error": result.error,
            "timestamp": result.timestamp.isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Verification failed: {str(e)}")


@router.post("/agent", response_model=ScanSecretsChatResponse)
async def chat_with_secrets_agent(request: ScanSecretsChatRequest):
    """
    Have a conversation with the specialized secrets scanning agent
    
    The agent can:
    - Perform targeted scans based on natural language requests
    - Answer questions about secret detection capabilities
    - Provide expert analysis of findings
    - Guide remediation efforts
    """
    try:
        # Create or retrieve session
        session_id = request.session_id or str(uuid.uuid4())
        session = SQLiteSession(session_id)
        
        # Add context if provided
        context_message = ""
        if request.context:
            context_message = f"\nContext: {request.context}"
        
        full_message = request.message + context_message
        
        # Run the agent
        result = await Runner.run(secrets_agent.agent, full_message, session=session)
        
        # Extract any findings summary if the agent performed scans
        findings_summary = None
        actions_taken = []
        
        # Simple parsing to extract key information
        response_text = result.final_output
        if "🚨" in response_text or "CRITICAL" in response_text.upper():
            findings_summary = "Critical security issues detected"
            actions_taken.append("critical_findings_detected")
        elif "⚠️" in response_text or "HIGH" in response_text.upper():
            findings_summary = "High-priority security issues found"
            actions_taken.append("high_priority_findings")
        elif "✅" in response_text or "NO" in response_text.upper():
            findings_summary = "No security issues detected"
            actions_taken.append("clean_scan_completed")
        
        return ScanSecretsChatResponse(
            response=response_text,
            session_id=session_id,
            findings_summary=findings_summary,
            actions_taken=actions_taken,
            timestamp=datetime.now()
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent conversation failed: {str(e)}")


@router.get("/capabilities", response_model=Dict[str, Any])
async def get_agent_capabilities():
    """Get information about the secrets scanning agent's capabilities"""
    return secrets_agent.get_capabilities()


@router.get("/patterns", response_model=Dict[str, Any])
async def get_detection_patterns():
    """Get information about the types of secrets that can be detected"""
    from .config import SECRETS_PATTERNS
    
    patterns_info = {}
    for pattern_name, regex in SECRETS_PATTERNS.items():
        patterns_info[pattern_name] = {
            "regex": regex,
            "description": _get_pattern_description(pattern_name),
            "risk_level": _get_pattern_risk_level(pattern_name)
        }
    
    return {
        "total_patterns": len(SECRETS_PATTERNS),
        "patterns": patterns_info,
        "coverage": [
            "HTML source code",
            "JavaScript files",
            "Source maps", 
            "Configuration files",
            "Git repositories"
        ]
    }


@router.delete("/scan/{scan_id}")
async def delete_scan_result(scan_id: str):
    """Delete a stored scan result"""
    if scan_id not in active_scans:
        raise HTTPException(status_code=404, detail="Scan not found")
    
    del active_scans[scan_id]
    return {"message": f"Scan {scan_id} deleted successfully"}


@router.get("/health")
async def health_check():
    """Health check endpoint for the secrets scanning service"""
    return {
        "status": "healthy",
        "component": "scan_secrets",
        "active_scans": len(active_scans),
        "capabilities": [
            "secrets_detection",
            "git_exposure_check", 
            "source_map_scanning",
            "credential_verification",
            "ai_agent_conversation"
        ]
    }


# Helper functions
def _get_pattern_description(pattern_name: str) -> str:
    """Get human-readable description for a pattern"""
    descriptions = {
        "aws_access_key": "AWS Access Key (AKIA...)",
        "aws_secret_key": "AWS Secret Key (40 chars base64)",
        "github_token": "GitHub Personal Access Token",
        "openai_api_key": "OpenAI API Key (sk-...)",
        "stripe_key": "Stripe Secret Key",
        "google_api_key": "Google API Key",
        "jwt_token": "JWT Token",
        "private_key": "Private Key",
        "database_url": "Database Connection String",
        "api_key_generic": "Generic API Key Pattern"
    }
    return descriptions.get(pattern_name, "Unknown pattern")


def _get_pattern_risk_level(pattern_name: str) -> str:
    """Get risk level for a pattern"""
    from .config import SECRET_RISK_LEVELS
    return SECRET_RISK_LEVELS.get(pattern_name, "medium") 