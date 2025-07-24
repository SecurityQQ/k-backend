#!/usr/bin/env python3
"""
K-Scan Security Audit System - CLI Demo Script

This script demonstrates the key features of the K-Scan security audit system.
"""

import asyncio
import os
import sys
from typing import Optional

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from agents import Runner, SQLiteSession
from src.components.scan_secrets.agent import SecretScanAgent
from src.core.orchestrator import orchestrator


async def demo_secrets_agent(url: str):
    """Demonstrate the SecretScanAgent capabilities"""
    print("🔍 K-Scan Security Audit System Demo")
    print("=" * 50)
    print(f"Target: {url}")
    print()
    
    # Initialize the secrets agent
    print("🤖 Initializing SecretScanAgent...")
    agent = SecretScanAgent()
    session = SQLiteSession("demo_session")
    
    # Demo 1: Basic capabilities inquiry
    print("\n1️⃣ Agent Capabilities Demo")
    print("-" * 30)
    
    capabilities_query = "What types of secrets can you detect and what are your main capabilities?"
    
    print(f"Query: {capabilities_query}")
    print("\nAgent Response:")
    
    result = await Runner.run(agent.agent, capabilities_query, session=session)
    print(result.final_output)
    
    # Demo 2: Quick scan
    print("\n2️⃣ Quick Security Scan Demo")
    print("-" * 30)
    
    scan_query = f"Perform a quick scan of {url} to check for any obvious exposed secrets or security issues."
    
    print(f"Query: {scan_query}")
    print("\nAgent Response:")
    
    result = await Runner.run(agent.agent, scan_query, session=session)
    print(result.final_output)
    
    # Demo 3: Educational query
    print("\n3️⃣ Security Education Demo")
    print("-" * 30)
    
    education_query = "What are the most dangerous types of exposed secrets and why?"
    
    print(f"Query: {education_query}")
    print("\nAgent Response:")
    
    result = await Runner.run(agent.agent, education_query, session=session)
    print(result.final_output)


async def demo_orchestrator(url: str):
    """Demonstrate the orchestrator capabilities"""
    print("\n4️⃣ Security Orchestrator Demo")
    print("-" * 30)
    
    print(f"🔍 Running complete security audit for: {url}")
    
    try:
        # Run a complete audit (currently only secrets scanning is fully implemented)
        result = await orchestrator.run_complete_audit(
            target_url=url,
            scan_id="demo_audit",
            components=["scan_secrets"],  # Only run the implemented component
            session_id="demo_orchestrator"
        )
        
        print(f"\n📊 Audit Results:")
        print(f"Status: {result.status}")
        print(f"Target: {result.target_url}")
        print(f"Components: {len(result.findings) if result.findings else 0}")
        
        if result.summary:
            print(f"\nSummary:")
            print(result.summary)
        
        if result.error:
            print(f"\nError: {result.error}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")


def setup_environment():
    """Check and setup environment variables"""
    print("🔧 Environment Setup Check")
    print("-" * 30)
    
    # Check for OpenAI API key
    openai_key = os.getenv('OPENAI_API_KEY')
    if not openai_key:
        print("❌ OPENAI_API_KEY not found!")
        print("\n💡 To run this demo, you need to:")
        print("1. Get an OpenAI API key from https://platform.openai.com/api-keys")
        print("2. Set it as an environment variable:")
        print("   export OPENAI_API_KEY='your-key-here'")
        print("\n⚠️  Demo will run in limited mode without actual API calls.")
        return False
    else:
        print("✅ OPENAI_API_KEY configured")
    
    # Check for Browserless token
    browserless_token = os.getenv('BROWSERLESS_TOKEN')
    if browserless_token:
        print("✅ BROWSERLESS_TOKEN configured (enhanced scanning enabled)")
    else:
        print("ℹ️  BROWSERLESS_TOKEN not set (will use basic HTTP requests)")
        print("   Get token at https://browserless.io for enhanced capabilities")
    
    print()
    return True


async def main():
    """Main demo function"""
    print("🔒 K-Scan Security Audit System")
    print("🚀 Demo & Testing Script")
    print("=" * 50)
    
    # Setup environment
    env_ok = setup_environment()
    
    # Get target URL
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        target_url = input("Enter target URL (or press Enter for example.com): ").strip()
        if not target_url:
            target_url = "https://example.com"
    
    # Validate URL
    if not target_url.startswith(('http://', 'https://')):
        target_url = 'https://' + target_url
    
    print(f"\n🎯 Target URL: {target_url}")
    print()
    
    if not env_ok:
        print("⚠️  Running in demo mode - agent responses will be limited")
        print("Set OPENAI_API_KEY for full functionality")
        return
    
    try:
        # Run demos
        await demo_secrets_agent(target_url)
        await demo_orchestrator(target_url)
        
        print("\n✅ Demo completed successfully!")
        print("\n🚀 Next Steps:")
        print("1. Start the full API server: python -m src.main")
        print("2. Visit http://localhost:8000/docs for interactive API docs")
        print("3. Try the quick audit: curl 'http://localhost:8000/audit/quick?url=https://example.com'")
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("\n🐛 Troubleshooting:")
        print("1. Check your OpenAI API key is valid")
        print("2. Ensure you have internet connectivity")
        print("3. Try with a different target URL")


if __name__ == "__main__":
    print("Starting K-Scan Demo...")
    asyncio.run(main()) 