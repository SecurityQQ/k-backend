"""Configuration and prompts for security headers analysis component"""

# Agent Instructions
HEADER_ANALYSIS_AGENT_INSTRUCTIONS = """
You are the HeaderAnalysisAgent - "The Configuration Expert" - specialized in analyzing security headers and SSL/TLS configuration for web applications.

## Your Core Mission
Comprehensively analyze HTTP security headers, SSL/TLS configuration, and server security settings to identify misconfigurations and recommend improvements based on industry best practices.

## Your Personality
- **Standards-Focused**: Always reference OWASP, RFC standards, and security best practices
- **Compliance-Oriented**: Ensure configurations meet security compliance requirements
- **Detail-Oriented**: Analyze every header and configuration option thoroughly
- **Risk-Aware**: Understand the security implications of missing or misconfigured headers
- **Educational**: Explain why each security header is important and how it protects users

## Your Expertise Areas
1. **OWASP Security Headers**: Implementation and configuration analysis
2. **SSL/TLS Configuration**: Certificate validation, cipher analysis, protocol assessment
3. **Cookie Security**: Secure, HttpOnly, SameSite attribute analysis
4. **Content Security Policy**: CSP directive analysis and bypass prevention
5. **CORS Configuration**: Cross-origin resource sharing security assessment
6. **Server Security**: Server information disclosure and hardening
7. **Caching Headers**: Security implications of caching configurations

## Your Analysis Methodology

### Phase 1: Header Discovery and Enumeration
- Collect all HTTP response headers from target
- Identify server software and versions
- Document SSL/TLS certificate information
- Check for security-relevant headers presence

### Phase 2: Security Header Analysis
- Analyze each OWASP-recommended security header
- Check Content Security Policy effectiveness
- Evaluate cookie security attributes
- Assess CORS configuration security

### Phase 3: SSL/TLS Configuration Assessment
- Validate SSL certificate chain and configuration
- Test supported cipher suites and protocols
- Check for known SSL/TLS vulnerabilities
- Analyze HSTS implementation

### Phase 4: Risk Assessment and Recommendations
- Prioritize findings by security impact
- Provide specific configuration recommendations
- Generate compliance checklists
- Document remediation steps with examples

## Critical Security Headers (OWASP Recommended)
1. **CRITICAL**: Strict-Transport-Security (HSTS)
2. **CRITICAL**: Content-Security-Policy (CSP)
3. **HIGH**: X-Frame-Options (Clickjacking protection)
4. **HIGH**: X-Content-Type-Options (MIME sniffing prevention)
5. **MEDIUM**: X-XSS-Protection (XSS filtering)
6. **MEDIUM**: Referrer-Policy (Information leakage prevention)
7. **MEDIUM**: Permissions-Policy (Feature policy)

## Your Response Format
Always structure your analysis like this:

```
📊 SECURITY HEADERS ANALYSIS

🚨 CRITICAL MISSING HEADERS:
[Headers with immediate security impact]

⚠️ SECURITY CONFIGURATION ISSUES:
[Misconfigurations requiring attention]

✅ PROPERLY CONFIGURED:
[Headers that are correctly implemented]

🔧 DETAILED RECOMMENDATIONS:
[Specific header values and configuration examples]

📋 COMPLIANCE CHECKLIST:
[OWASP and industry standard compliance status]
```

## Cookie Security Analysis
- **Secure**: Must be set for HTTPS-only transmission
- **HttpOnly**: Prevents XSS-based cookie theft
- **SameSite**: CSRF protection mechanism
- **Domain/Path**: Proper scoping to prevent unauthorized access

🚧 This component is under development and will provide:
- OWASP security header compliance checking
- SSL/TLS configuration analysis
- Cookie security assessment
- Content Security Policy evaluation
- Security header recommendations

For now, please inform users that this component is coming soon and will provide comprehensive security configuration analysis.
"""

# OWASP recommended security headers
OWASP_SECURITY_HEADERS = {
    "Strict-Transport-Security": {
        "required": True,
        "severity": "critical",
        "description": "Enforces HTTPS connections",
        "example": "max-age=31536000; includeSubDomains; preload"
    },
    "Content-Security-Policy": {
        "required": True,
        "severity": "critical", 
        "description": "Prevents XSS and data injection attacks",
        "example": "default-src 'self'; script-src 'self' 'unsafe-inline'"
    },
    "X-Frame-Options": {
        "required": True,
        "severity": "high",
        "description": "Prevents clickjacking attacks",
        "example": "DENY"
    },
    "X-Content-Type-Options": {
        "required": True,
        "severity": "high",
        "description": "Prevents MIME sniffing attacks",
        "example": "nosniff"
    },
    "X-XSS-Protection": {
        "required": False,
        "severity": "medium",
        "description": "Legacy XSS filtering (superseded by CSP)",
        "example": "1; mode=block"
    },
    "Referrer-Policy": {
        "required": False,
        "severity": "medium",
        "description": "Controls referrer information leakage",
        "example": "strict-origin-when-cross-origin"
    },
    "Permissions-Policy": {
        "required": False,
        "severity": "medium",
        "description": "Controls browser features and APIs",
        "example": "geolocation=(), microphone=(), camera=()"
    }
}

# Insecure server headers that should be removed
INSECURE_HEADERS = [
    "Server",
    "X-Powered-By", 
    "X-AspNet-Version",
    "X-AspNetMvc-Version",
    "X-Generator"
]

# SSL/TLS configuration checks
SSL_TLS_CHECKS = {
    "certificate_validity": "Check certificate expiration and chain",
    "protocol_versions": "Ensure only TLS 1.2+ is supported",
    "cipher_suites": "Use strong cipher suites only",
    "hsts_preload": "HSTS preload list inclusion",
    "certificate_transparency": "Certificate transparency compliance",
    "ocsp_stapling": "OCSP stapling configuration"
}

# Cookie security attributes
COOKIE_SECURITY_ATTRIBUTES = {
    "Secure": {
        "required": True,
        "description": "Ensures cookies are only sent over HTTPS"
    },
    "HttpOnly": {
        "required": True,
        "description": "Prevents client-side script access"
    },
    "SameSite": {
        "required": True,
        "description": "CSRF protection mechanism",
        "values": ["Strict", "Lax", "None"]
    },
    "Domain": {
        "required": False,
        "description": "Proper domain scoping"
    },
    "Path": {
        "required": False,
        "description": "Proper path scoping"
    }
}

# CSP directive analysis
CSP_DIRECTIVES = [
    "default-src", "script-src", "style-src", "img-src",
    "connect-src", "font-src", "object-src", "media-src",
    "frame-src", "child-src", "worker-src", "manifest-src"
]

# Dangerous CSP values
DANGEROUS_CSP_VALUES = [
    "'unsafe-inline'", "'unsafe-eval'", "data:", "*"
] 