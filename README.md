# 🔒 K-Scan Security Audit System

An intelligent, multi-component security audit system built with OpenAI Agents SDK. The system automatically scans websites and web applications for vulnerabilities using specialized AI agents that can crawl content, detect security issues, and generate comprehensive reports.

## 🚀 Key Features

- **🔑 Secrets Detection**: Find exposed API keys, tokens, and credentials
- **🕸️ Intelligent Crawling**: JavaScript-enabled website exploration  
- **🛡️ Vulnerability Testing**: XSS, SQL injection, CSRF detection
- **📊 Security Headers**: OWASP compliance analysis
- **📋 Smart Reporting**: AI-generated executive summaries

## 🤖 AI Agent Network

The system uses specialized AI agents, each with distinct personalities and expertise:

- **SecretScanAgent**: "The Paranoid Investigator" - Credential detection expert
- **CrawlerAgent**: "The Explorer" - Website mapping specialist *(Coming Soon)*
- **VulnerabilityAgent**: "The Penetration Tester" - Security testing expert *(Coming Soon)*
- **HeaderAnalysisAgent**: "The Configuration Expert" - Security header analyst *(Coming Soon)*
- **ReportAgent**: "The Communicator" - Intelligent report generator *(Coming Soon)*

## 🏗️ Component-Based Architecture

Each security capability is implemented as an independent component with:

1. **schema.py** - Data models and types
2. **client.py** - External API interactions  
3. **service.py** - Business logic and orchestration
4. **tools.py** - Agent function wrappers
5. **agent.py** - Specialized AI agent
6. **routes.py** - HTTP API endpoints
7. **config.py** - Prompts, patterns, and settings

## 📋 Current Status

### ✅ Active Components
- **scan_secrets**: Complete implementation with comprehensive API key detection

### 🚧 Coming Soon
- **crawl_website**: Intelligent website discovery
- **scan_vulnerabilities**: Web application security testing
- **analyze_headers**: Security configuration analysis
- **generate_report**: AI-powered reporting

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- OpenAI API key
- Optional: Browserless.io token for enhanced JavaScript rendering

### Installation

1. **Clone the repository**
```bash
git clone <repository-url>
cd k-backend
```

2. **Install dependencies**
```bash
pip install -r requirements.txt
```

3. **Configure environment**
```bash
cp .env.example .env
# Edit .env with your API keys
```

4. **Set required environment variables**
```bash
export OPENAI_API_KEY="your-openai-api-key"
export BROWSERLESS_TOKEN="your-browserless-token"  # Optional
```

## 🚀 Usage

### Quick Start

1. **Start the server**
```bash
python -m src.main
```

2. **Access the API documentation**
Open http://localhost:8000/docs

### API Endpoints

#### Quick Security Audit
```bash
curl "http://localhost:8000/audit/quick?url=https://example.com"
```

#### Complete Security Audit
```bash
curl -X POST "http://localhost:8000/audit/complete" \
  -H "Content-Type: application/json" \
  -d '{"target_url": "https://example.com", "deep_scan": true}'
```

#### Direct Component Access
```bash
# Secrets scanning
curl -X POST "http://localhost:8000/scan_secrets/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "scan_js_files": true}'

# Agent conversation
curl -X POST "http://localhost:8000/scan_secrets/agent" \
  -H "Content-Type: application/json" \
  -d '{"message": "Scan example.com for exposed API keys"}'
```

### Example Workflows

#### 1. Initial Security Assessment
```python
import requests

# Quick scan for immediate risks
response = requests.get("http://localhost:8000/audit/quick?url=https://target.com")
print(response.json()["summary"])
```

#### 2. Comprehensive Security Audit
```python
# Full audit with all components
response = requests.post("http://localhost:8000/audit/complete", json={
    "target_url": "https://target.com",
    "deep_scan": True,
    "verify_secrets": False  # Use carefully
})

audit_id = response.json()["audit_id"]
results = requests.get(f"http://localhost:8000/audit/{audit_id}")
```

#### 3. Conversational Security Analysis
```python
# Chat with specialized agents
response = requests.post("http://localhost:8000/scan_secrets/agent", json={
    "message": "What types of API keys can you detect?",
    "session_id": "my-session"
})
print(response.json()["response"])
```

## 🔧 Configuration

### Environment Variables

Key configuration options in `.env`:

```bash
# Required
OPENAI_API_KEY=your_key_here

# Optional but recommended for enhanced scanning
BROWSERLESS_TOKEN=your_token_here

# Security settings
MAX_SCAN_DEPTH=3
MAX_PAGES_PER_SCAN=100
RATE_LIMIT_DELAY=1.0

# Component toggles
ENABLE_SECRETS_SCAN=true
ENABLE_VULNERABILITY_SCAN=true
```

### Browserless.io Integration

For enhanced JavaScript rendering and crawling:

1. Sign up at [browserless.io](https://browserless.io)
2. Get your API token
3. Set `BROWSERLESS_TOKEN` in `.env`

Without Browserless, the system falls back to basic HTTP requests.

## 📊 Security Components Deep Dive

### Secrets Scanner (Active)

**Capabilities:**
- 20+ secret pattern detection (AWS, GitHub, OpenAI, Stripe, etc.)
- JavaScript file and source map analysis
- Git repository exposure detection
- Optional credential verification
- Confidence scoring and risk assessment

**Usage:**
```python
from agents import Runner, SQLiteSession
from src.components.scan_secrets.agent import SecretScanAgent

agent = SecretScanAgent()
session = SQLiteSession("secrets_scan")

result = await Runner.run(
    agent.agent,
    "Scan https://example.com for exposed API keys",
    session=session
)
```

### Other Components (Coming Soon)

The system is designed for easy expansion. Each new component follows the same 7-file structure and integrates automatically with the orchestrator.

## 🛡️ Security Best Practices

### For Users
1. **Never verify secrets** without explicit permission
2. **Use rate limiting** to respect target servers
3. **Follow responsible disclosure** for found vulnerabilities
4. **Keep API keys secure** and rotate regularly

### For Developers
1. **Input validation** on all endpoints
2. **Rate limiting** implemented throughout
3. **Secure session storage** with SQLite
4. **Error handling** prevents information leakage

## 🐛 Troubleshooting

### Common Issues

1. **OpenAI API Key Missing**
```bash
export OPENAI_API_KEY="your-key-here"
```

2. **Browserless Connection Issues**
- Check token validity
- Verify network connectivity
- System falls back to basic HTTP

3. **Rate Limiting**
- Adjust `RATE_LIMIT_DELAY` in `.env`
- Respect target server limits

### Debug Mode
```bash
export DEBUG=true
python -m src.main
```

## 🤝 Contributing

### Adding New Components
1. Create component directory: `src/components/new_component/`
2. Implement the 7 required files
3. Add agent to orchestrator
4. Include router in main app
5. Update documentation

### Development Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Run tests
pytest

# Code formatting
black src/
isort src/

# Type checking
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙋 Support

- **Documentation**: `/docs` endpoint when running
- **Health Check**: `/health` endpoint
- **Component Status**: `/components` endpoint

## 🚀 Future Roadmap

- [ ] Complete all 5 security components
- [ ] Advanced authentication bypass techniques  
- [ ] PDF report generation
- [ ] Integration with CI/CD pipelines
- [ ] Multi-target batch scanning
- [ ] Machine learning for false positive reduction
- [ ] Custom vulnerability signatures
- [ ] Integration with security orchestration platforms

---

**⚠️ Important**: This tool is for authorized security testing only. Always obtain proper permission before scanning systems you do not own. 