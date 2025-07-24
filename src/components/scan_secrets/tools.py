"""Function tools for secrets scanning agent"""

import asyncio
from typing import Dict, Any, Optional, List
from agents import function_tool

from .service import secrets_service
from .schema import ScanTarget


@function_tool
async def scan_html_content_for_secrets(html_content: str, source_location: str = "provided_content", verify_secrets: bool = False) -> str:
    """
    Scan HTML content for exposed API keys, tokens, and sensitive credentials.
    
    This tool analyzes pre-rendered HTML content for secrets. It should be used
    after crawl_website has rendered the page content with JavaScript.
    
    Args:
        html_content: The rendered HTML content to scan
        source_location: Description of where this content came from (for reporting)
        verify_secrets: Whether to attempt verification of found secrets (use carefully)
    
    Returns:
        Human-readable summary of found secrets with severity levels
    """
    try:
        if not html_content or not html_content.strip():
            return f"⚠️ No HTML content provided to scan"
        
        # Scan the HTML content directly
        matches = secrets_service.scanner.scan_content(html_content, source_location)
        
        if not matches:
            return f"✅ No exposed secrets found in HTML content from {source_location}"
        
        # Generate detailed summary
        total_matches = len(matches)
        matches_by_severity = {}
        for match in matches:
            severity = match.severity.value
            matches_by_severity[severity] = matches_by_severity.get(severity, 0) + 1
        
        summary = f"🚨 Found {total_matches} potential secrets in {source_location}"
        
        # Add severity breakdown
        if matches_by_severity:
            summary += f"\n\n🎯 Findings by Severity:"
            for severity, count in matches_by_severity.items():
                emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(severity, "📌")
                summary += f"\n- {emoji} {severity.title()}: {count}"
        
        # Add most critical findings
        critical_matches = [m for m in matches if m.severity.value == "critical"]
        if critical_matches:
            summary += f"\n\n🚨 CRITICAL FINDINGS (TOP 3):"
            for i, match in enumerate(critical_matches[:3], 1):
                summary += f"\n{i}. {match.secret_type.value.upper()}"
                summary += f" (confidence: {match.confidence:.0%})"
                if match.line_number:
                    summary += f" at line {match.line_number}"
        
        # Verification if requested
        if verify_secrets and critical_matches:
            summary += f"\n\n🔍 Verification Results:"
            for match in critical_matches[:3]:  # Only verify top 3 critical
                if match.secret_type.value in ["github_token", "openai_api_key"]:
                    try:
                        verification_client = secrets_service.verification_client
                        if match.secret_type.value == "github_token":
                            result = await verification_client.verify_github_token(match.matched_text)
                        else:
                            result = await verification_client.verify_openai_key(match.matched_text)
                        
                        status = "✅ VALID" if result.is_valid else "❌ INVALID"
                        summary += f"\n- {match.secret_type.value}: {status}"
                    except Exception as e:
                        summary += f"\n- {match.secret_type.value}: Verification failed ({str(e)})"
        
        # Add recommendations
        summary += f"\n\n💡 Recommendations:"
        if critical_matches:
            summary += f"\n- 🚨 IMMEDIATE ACTION: Revoke/rotate all critical secrets"
            summary += f"\n- 🔧 Remove secrets from code and use environment variables"
            summary += f"\n- 📋 Implement secret scanning in CI/CD pipeline"
        else:
            summary += f"\n- 🔍 Review detected patterns and improve secret handling"
        
        return summary
        
    except Exception as e:
        return f"❌ Error during HTML content scan: {str(e)}"


@function_tool
async def scan_javascript_content_for_secrets(js_content: str, js_file_url: str = "provided_js_file") -> str:
    """
    Scan JavaScript content for exposed secrets and credentials.
    
    Analyzes JavaScript code for API keys, tokens, and other sensitive data
    that might be exposed in client-side code.
    
    Args:
        js_content: The JavaScript content to scan
        js_file_url: The URL or identifier of the JS file (for reporting)
    
    Returns:
        Summary of secrets found in the JavaScript content
    """
    try:
        if not js_content or not js_content.strip():
            return f"⚠️ No JavaScript content provided to scan"
        
        # Scan the JavaScript content
        matches = secrets_service.scanner.scan_content(js_content, js_file_url)
        
        if not matches:
            return f"✅ No exposed secrets found in JavaScript file: {js_file_url}"
        
        summary = f"🔍 JavaScript Secrets Analysis for {js_file_url}:\n\n"
        summary += f"Found {len(matches)} potential secrets:\n"
        
        for match in matches:
            emoji = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}.get(match.severity.value, "📌")
            summary += f"{emoji} {match.secret_type.value.upper()}"
            summary += f" (confidence: {match.confidence:.0%})"
            if match.line_number:
                summary += f" at line {match.line_number}"
            summary += f"\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error scanning JavaScript content: {str(e)}"


@function_tool
async def verify_api_key(secret_type: str, secret_value: str) -> str:
    """
    Verify if a found API key or token is valid and active.
    
    CAUTION: This makes actual API calls to verify credentials.
    Only use when explicitly requested and with proper authorization.
    
    Args:
        secret_type: Type of secret (github_token, openai_api_key, etc.)
        secret_value: The secret value to verify
    
    Returns:
        Verification result with validity status
    """
    try:
        verification_client = secrets_service.verification_client
        
        if secret_type == "github_token":
            result = await verification_client.verify_github_token(secret_value)
        elif secret_type == "openai_api_key":
            result = await verification_client.verify_openai_key(secret_value)
        else:
            return f"⚠️  Verification not supported for {secret_type}"
        
        status = "✅ VALID" if result.is_valid else "❌ INVALID"
        confidence = f"{result.confidence:.0%}"
        method = result.method_used
        
        response = f"{status} - {secret_type}\n"
        response += f"Confidence: {confidence}\n"
        response += f"Method: {method}"
        
        if result.error:
            response += f"\nError: {result.error}"
        
        return response
        
    except Exception as e:
        return f"❌ Verification failed: {str(e)}"


@function_tool
async def check_git_exposure(base_url: str) -> str:
    """
    Check if a website has exposed .git directories or files.
    
    This is a critical security issue that can expose:
    - Source code history
    - Configuration files
    - Developer credentials
    - Internal system information
    
    Args:
        base_url: The base website URL to check for git exposure
    
    Returns:
        Results of git exposure check
    """
    try:
        import aiohttp
        
        base_url = base_url.rstrip('/')
        git_paths = [
            '/.git/config',
            '/.git/HEAD',
            '/.git/logs/HEAD',
            '/.git/refs/heads/master',
            '/.git/refs/heads/main',
            '/.git/index'
        ]
        
        exposed_files = []
        
        async with aiohttp.ClientSession() as session:
            for git_path in git_paths:
                try:
                    git_url = base_url + git_path
                    async with session.get(git_url, timeout=10) as response:
                        if response.status == 200:
                            content = await response.text()
                            if len(content) > 0 and not content.startswith('<!DOCTYPE'):
                                exposed_files.append({
                                    'path': git_path,
                                    'url': git_url,
                                    'size': len(content)
                                })
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception:
                    continue
        
        if exposed_files:
            result = f"🚨 CRITICAL: Exposed .git directory found!\n\n"
            result += f"Found {len(exposed_files)} exposed git files:\n"
            
            for file_info in exposed_files:
                result += f"- {file_info['path']} ({file_info['size']} bytes)\n"
            
            result += f"\n💥 IMMEDIATE ACTIONS REQUIRED:\n"
            result += f"1. Block access to /.git/ directory immediately\n"
            result += f"2. Review what sensitive data may be exposed\n"
            result += f"3. Rotate any credentials that might be in git history\n"
            result += f"4. Audit deployment process to prevent future exposure"
            
            return result
        else:
            return "✅ No .git directory exposure detected"
            
    except Exception as e:
        return f"❌ Error checking git exposure: {str(e)}"


@function_tool
async def scan_source_maps_for_secrets(js_file_urls: str) -> str:
    """
    Scan JavaScript source maps for exposed secrets and sensitive information.
    
    Source maps can accidentally expose:
    - Original source code with secrets
    - Development environment configurations
    - Internal API endpoints
    - Database connection strings
    
    Args:
        js_file_urls: Comma-separated list of JavaScript file URLs to check for source maps
    
    Returns:
        Results of source map analysis
    """
    try:
        js_files = [url.strip() for url in js_file_urls.split(',') if url.strip()]
        
        if not js_files:
            return "ℹ️  No JavaScript file URLs provided"
        
        source_maps_found = []
        secrets_in_maps = []
        
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            for js_url in js_files:
                try:
                    # Check for source map file
                    source_map_url = js_url + '.map'
                    
                    async with session.get(source_map_url, timeout=10) as response:
                        if response.status == 200:
                            map_content = await response.text()
                            source_maps_found.append(source_map_url)
                            
                            # Scan source map for secrets
                            matches = secrets_service.scanner.scan_content(map_content, source_map_url)
                            secrets_in_maps.extend(matches)
                    
                    # Rate limiting
                    await asyncio.sleep(0.5)
                    
                except Exception:
                    continue
        
        result = f"🗺️  Source Map Analysis Results:\n\n"
        result += f"JavaScript files checked: {len(js_files)}\n"
        result += f"Source maps found: {len(source_maps_found)}\n"
        
        if secrets_in_maps:
            result += f"\n🚨 SECRETS FOUND IN SOURCE MAPS ({len(secrets_in_maps)}):\n"
            
            for match in secrets_in_maps:
                result += f"- {match.secret_type.value.upper()}: {match.matched_text[:20]}..."
                result += f" (confidence: {match.confidence:.0%})\n"
                result += f"  Location: {match.location}\n"
            
            result += f"\n💡 Recommendations:\n"
            result += f"- Remove source maps from production\n"
            result += f"- Audit all found secrets and rotate if necessary\n"
            result += f"- Implement proper build process to exclude sensitive data"
        else:
            result += f"\n✅ No secrets detected in source maps"
        
        if source_maps_found:
            result += f"\n\n📋 Found source maps:\n"
            for map_url in source_maps_found:
                result += f"- {map_url}\n"
        
        return result
        
    except Exception as e:
        return f"❌ Error scanning source maps: {str(e)}"


@function_tool
def get_secret_patterns() -> str:
    """
    Get information about the types of secrets that can be detected.
    
    Returns:
        List of all secret patterns that the scanner can detect
    """
    from .config import SECRETS_PATTERNS
    
    result = "🔍 Secret Detection Patterns:\n\n"
    
    patterns_info = {
        "aws_access_key": "AWS Access Key (AKIA...)",
        "aws_secret_key": "AWS Secret Key (40 chars base64)",
        "github_token": "GitHub Personal Access Token (gh*_...)",
        "openai_api_key": "OpenAI API Key (sk-...)",
        "stripe_key": "Stripe Secret Key (sk_live_...)",
        "google_api_key": "Google API Key (AIza...)",
        "jwt_token": "JWT Token (eyJ...)",
        "private_key": "Private Key (-----BEGIN...)",
        "database_url": "Database Connection String",
        "api_key_generic": "Generic API Key Pattern"
    }
    
    for pattern_name, description in patterns_info.items():
        regex_pattern = SECRETS_PATTERNS.get(pattern_name, "Unknown")
        result += f"• {description}\n"
        result += f"  Pattern: {regex_pattern}\n\n"
    
    result += "💡 These patterns are used to detect exposed credentials in:\n"
    result += "- HTML source code\n"
    result += "- JavaScript files\n" 
    result += "- Source maps\n"
    result += "- Configuration files\n"
    result += "- Git repositories\n"
    
    return result


@function_tool
async def analyze_secrets_in_content(all_content: str, content_description: str = "provided content") -> str:
    """
    Perform comprehensive analysis of all provided content for exposed secrets.
    
    This tool analyzes multiple types of content (HTML, JS, etc.) and provides
    a comprehensive security assessment with prioritized findings.
    
    Args:
        all_content: All content to analyze (can be HTML, JS, or mixed)
        content_description: Description of what content is being analyzed
    
    Returns:
        Comprehensive security analysis of all content
    """
    try:
        if not all_content or not all_content.strip():
            return f"⚠️ No content provided for analysis"
        
        # Scan all content for secrets
        matches = secrets_service.scanner.scan_content(all_content, content_description)
        
        if not matches:
            return f"✅ No exposed secrets found in {content_description}"
        
        # Analyze findings
        critical_matches = [m for m in matches if m.severity.value == "critical"]
        high_matches = [m for m in matches if m.severity.value == "high"]
        medium_matches = [m for m in matches if m.severity.value == "medium"]
        low_matches = [m for m in matches if m.severity.value == "low"]
        
        # Build comprehensive summary
        summary = f"🔍 COMPREHENSIVE SECRETS ANALYSIS\n"
        summary += f"Content: {content_description}\n"
        summary += f"Total potential secrets found: {len(matches)}\n\n"
        
        # Risk assessment
        if critical_matches:
            summary += f"🚨 CRITICAL RISK LEVEL - Immediate action required\n"
        elif high_matches:
            summary += f"⚠️ HIGH RISK LEVEL - Prompt attention needed\n"  
        elif medium_matches:
            summary += f"⚡ MEDIUM RISK LEVEL - Review recommended\n"
        else:
            summary += f"ℹ️ LOW RISK LEVEL - Monitor and improve\n"
        
        summary += f"\n📊 FINDINGS BREAKDOWN:\n"
        if critical_matches:
            summary += f"🚨 Critical: {len(critical_matches)} findings\n"
        if high_matches:
            summary += f"⚠️ High: {len(high_matches)} findings\n"
        if medium_matches:
            summary += f"⚡ Medium: {len(medium_matches)} findings\n"
        if low_matches:
            summary += f"ℹ️ Low: {len(low_matches)} findings\n"
        
        # Show top critical findings
        if critical_matches:
            summary += f"\n🚨 TOP CRITICAL FINDINGS:\n"
            for i, match in enumerate(critical_matches[:3], 1):
                summary += f"{i}. {match.secret_type.value.upper()}"
                if match.line_number:
                    summary += f" (line {match.line_number})"
                summary += f" - {match.confidence:.0%} confidence\n"
        
        # Security recommendations
        summary += f"\n💡 SECURITY RECOMMENDATIONS:\n"
        if critical_matches:
            summary += f"1. 🚨 URGENT: Revoke and rotate all critical secrets immediately\n"
            summary += f"2. 🔧 Remove hardcoded secrets from code\n"
            summary += f"3. 🔐 Implement proper secret management (env variables, vaults)\n"
            summary += f"4. 📋 Add secret scanning to CI/CD pipeline\n"
        else:
            summary += f"1. 🔍 Review flagged patterns for false positives\n"
            summary += f"2. 🔐 Implement proactive secret management practices\n"
            summary += f"3. 📋 Consider automated secret scanning\n"
        
        return summary
        
    except Exception as e:
        return f"❌ Error during content analysis: {str(e)}" 