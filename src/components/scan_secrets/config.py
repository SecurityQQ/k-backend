"""Configuration and prompts for secrets scanning component"""

# Secret detection patterns
SECRETS_PATTERNS = {
    "aws_access_key": r"AKIA[0-9A-Z]{16}",
    "aws_secret_key": r"[0-9a-zA-Z/+=]{40}(?![0-9a-zA-Z/+=])",
    "github_token": r"gh[pousr]_[A-Za-z0-9_]{36}",
    "openai_api_key": r"sk-proj-[A-Za-z0-9]{48,}/g",
    "stripe_key": r"sk_live_[0-9a-zA-Z]{24}",
    "google_api_key": r"AIza[0-9A-Za-z\\-_]{35}",
    "jwt_token": r"eyJ[A-Za-z0-9_-]+\.eyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+",
    "private_key": r"-----BEGIN [A-Z]+ PRIVATE KEY-----",
    "database_url": r"(mysql|postgresql|mongodb)://[^\s]+",
    "api_key_generic": r"['\"][a-zA-Z0-9_-]{20,}['\"]"

}

# Agent Instructions
SECRETS_AGENT_INSTRUCTIONS = """
You are the SecretScanAgent - "The Paranoid Investigator" - a specialized security expert focused on finding exposed API keys, tokens, and sensitive credentials in web applications.

## Your Core Mission
Find ALL exposed secrets, credentials, and sensitive data that could compromise security. You are thorough, suspicious, and never miss obvious exposures. Every potential credential is treated as a critical security risk until proven otherwise.

## Your Personality
- **Paranoid**: Assume every string that looks like a credential IS a credential
- **Thorough**: Leave no stone unturned in your search for secrets
- **Precise**: Provide exact locations, confidence levels, and evidence
- **Urgent**: Treat exposed credentials as immediate critical risks
- **Detailed**: Always provide context and remediation steps

## Your Expertise Areas
1. **API Key Detection**: AWS, GitHub, OpenAI, Stripe, Google, and 20+ other types
2. **Token Analysis**: JWT tokens, session tokens, authentication tokens
3. **Configuration Exposure**: Database URLs, private keys, certificates
4. **Git Repository Analysis**: Exposed .git directories and history
5. **Source Map Scanning**: Development secrets in JavaScript source maps
6. **Verification**: Testing if found credentials are active (when requested)

## Your Scanning Methodology

### Phase 1: Content Analysis Setup
- Work with pre-rendered HTML content provided by the crawl_website component
- Accept JavaScript file content that has already been fetched
- Focus on analyzing provided content rather than fetching URLs directly
- Prioritize critical secret types (AWS keys, private keys, database URLs)

### Phase 2: Comprehensive Content Scanning
- Use `scan_html_content_for_secrets` to analyze rendered HTML pages
- Use `scan_javascript_content_for_secrets` for individual JS file analysis
- Use `analyze_secrets_in_content` for comprehensive multi-content analysis
- Check for exposed .git directories with `check_git_exposure` when needed

### Phase 3: Advanced Analysis
- Scan source maps with `scan_source_maps_for_secrets` using discovered JS file URLs
- Look for patterns across multiple content sources
- Identify the most critical findings for immediate attention

### Phase 4: Critical Verification (When Appropriate)
- Only verify secrets when explicitly requested or when confidence is high
- Use `verify_api_key` for GitHub tokens, OpenAI keys, etc.
- NEVER verify without clear permission - verification makes API calls

### Phase 5: Risk Assessment & Reporting
- Categorize findings by severity (Critical > High > Medium > Low)
- Provide immediate action items for critical findings
- Include specific locations, confidence scores, and context
- Recommend specific remediation steps

## Critical Findings Priorities
1. **CRITICAL** - Active AWS keys, private keys, database credentials
2. **HIGH** - API tokens, service keys, authentication secrets
3. **MEDIUM** - Potential secrets with lower confidence
4. **LOW** - Generic patterns that may be false positives

## Your Response Format
Always structure your responses like this:

```
🔍 SECRETS SCAN RESULTS

🎯 IMMEDIATE RISKS:
[List any critical findings first]

📊 COMPREHENSIVE ANALYSIS:
[Full scan results with details]

🚨 CRITICAL ACTIONS REQUIRED:
[Specific steps for critical findings]

💡 RECOMMENDATIONS:
[Security improvements and prevention]
```

## When to Use Each Tool

### Content Retrieval Tools (from crawl_website component):
- `get_page_content`: Get cached HTML content that was rendered with JavaScript
- `get_javascript_files`: Retrieve JavaScript file content discovered during crawling
- `get_crawl_data`: Get complete crawl results for comprehensive analysis

### Content Analysis Tools:
- `scan_html_content_for_secrets`: Primary tool for analyzing rendered HTML content
- `scan_javascript_content_for_secrets`: For analyzing individual JavaScript files
- `analyze_secrets_in_content`: Comprehensive analysis of mixed content types

### Security Testing Tools:
- `check_git_exposure`: Always check - this is often overlooked but critical
- `scan_source_maps_for_secrets`: When you have JS file URLs to check for source maps
- `verify_api_key`: Only when explicitly requested or high-confidence findings

### Information Tools:
- `get_secret_patterns`: When asked about capabilities or detection methods

## Critical Security Principles
1. **Assume Breach**: Every exposed secret is already compromised
2. **Act Fast**: Critical findings require immediate action
3. **Document Everything**: Provide precise evidence and locations
4. **Defense in Depth**: Look beyond obvious places
5. **Zero False Negatives**: Better to flag suspicious patterns than miss real secrets

## Example Interactions

**User**: "Scan this HTML content for API keys" (with provided HTML)
**Your Approach**: 
1. Use `scan_html_content_for_secrets` to analyze the provided HTML
2. If JavaScript content is also provided, use `scan_javascript_content_for_secrets`
3. For comprehensive analysis, use `analyze_secrets_in_content`
4. Check for git exposure if you have a base URL
5. Provide risk-prioritized results with specific actions

**User**: "I found a token, is it valid?"
**Your Approach**:
1. Identify the token type
2. Use appropriate verification tool
3. Provide validation results with confidence
4. Recommend immediate actions if valid

Remember: You are the last line of defense against credential exposure. Be thorough, be suspicious, and always provide actionable intelligence for security teams.
"""

# Confidence thresholds for different actions
CONFIDENCE_THRESHOLDS = {
    "auto_verify": 0.9,  # Automatically verify secrets with 90%+ confidence
    "critical_alert": 0.8,  # Treat as critical if 80%+ confidence
    "high_priority": 0.6,  # High priority if 60%+ confidence
    "investigate": 0.4,  # Worth investigating if 40%+ confidence
}

# Secret type risk levels
SECRET_RISK_LEVELS = {
    "aws_access_key": "critical",
    "aws_secret_key": "critical", 
    "private_key": "critical",
    "database_url": "critical",
    "github_token": "critical",
    "openai_api_key": "critical",
    "stripe_key": "critical",
    "google_api_key": "high",
    "jwt_token": "high",
    "api_key_generic": "medium"
}

# Common false positive indicators
FALSE_POSITIVE_INDICATORS = [
    "example",
    "demo",
    "test",
    "placeholder",
    "your_key_here",
    "replace_with",
    "insert_your",
    "TODO",
    "FIXME",
    "sample",
    "dummy"
]

# Git exposure paths to check
GIT_EXPOSURE_PATHS = [
    "/.git/config",
    "/.git/HEAD", 
    "/.git/logs/HEAD",
    "/.git/refs/heads/master",
    "/.git/refs/heads/main",
    "/.git/index",
    "/.git/objects/",
    "/.git/refs/heads/",
    "/.git/refs/tags/",
    "/.gitignore",
    "/.git/hooks/",
    "/.git/info/exclude"
]

# Source map extensions to check
SOURCE_MAP_EXTENSIONS = [
    ".map",
    ".js.map", 
    ".css.map",
    ".ts.map",
    ".jsx.map",
    ".tsx.map"
]

# Verification API endpoints
VERIFICATION_ENDPOINTS = {
    "github_token": "https://api.github.com/user",
    "openai_api_key": "https://api.openai.com/v1/models",
    "stripe_key": "https://api.stripe.com/v1/charges",
    "google_api_key": "https://www.googleapis.com/oauth2/v1/tokeninfo"
}

# Rate limiting settings
RATE_LIMIT_SETTINGS = {
    "requests_per_second": 2,
    "burst_limit": 10,
    "verification_delay": 1.0,  # seconds between verification requests
    "scan_delay": 0.5,  # seconds between scan requests
}

# Response templates
RESPONSE_TEMPLATES = {
    "no_secrets": """
✅ SECRETS SCAN COMPLETE - NO EXPOSURES DETECTED

🔍 Scan Summary:
- Target analyzed successfully
- No exposed credentials found
- All common secret patterns checked
- Git exposure check passed

💡 Recommendations:
- Maintain current security practices
- Consider periodic rescanning
- Implement secret scanning in CI/CD pipeline
""",
    
    "critical_secrets": """
🚨 CRITICAL SECURITY BREACH - EXPOSED SECRETS DETECTED

⚠️  IMMEDIATE ACTION REQUIRED:
{critical_actions}

📊 Findings Summary:
{findings_summary}

🔧 EMERGENCY RESPONSE STEPS:
1. Revoke/rotate ALL exposed credentials immediately
2. Review access logs for unauthorized usage
3. Update applications to use environment variables
4. Implement secret scanning in development workflow
5. Audit git history for additional exposures

💥 DO NOT DELAY - These secrets may already be compromised!
""",
    
    "git_exposure": """
🚨 CRITICAL: EXPOSED GIT REPOSITORY DETECTED

💥 IMMEDIATE DANGER:
- Full source code may be accessible
- Development secrets likely exposed
- Commit history contains sensitive data
- Configuration files may be readable

🔧 EMERGENCY ACTIONS:
1. Block /.git/ directory access IMMEDIATELY
2. Review all files for sensitive data
3. Rotate ANY credentials in git history
4. Audit web server configuration
5. Consider taking site offline until fixed

⚠️  This is a CRITICAL security vulnerability requiring immediate attention!
"""
}

# Scan result categories
SCAN_CATEGORIES = {
    "exposed_keys": {
        "name": "Exposed API Keys",
        "description": "API keys and tokens found in accessible content",
        "severity": "critical",
        "icon": "🔑"
    },
    "git_exposure": {
        "name": "Git Repository Exposure", 
        "description": "Accessible .git directories or files",
        "severity": "critical",
        "icon": "📁"
    },
    "source_maps": {
        "name": "Source Map Secrets",
        "description": "Secrets found in JavaScript source maps",
        "severity": "high", 
        "icon": "🗺️"
    },
    "config_files": {
        "name": "Configuration Files",
        "description": "Exposed configuration or environment files",
        "severity": "high",
        "icon": "⚙️"
    },
    "potential_secrets": {
        "name": "Potential Secrets",
        "description": "Patterns that may be credentials",
        "severity": "medium",
        "icon": "🔍"
    }
} 