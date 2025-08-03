#!/usr/bin/env python3
"""
Database setup script for K-Backend
Run this after setting your DATABASE_URL environment variable
"""

import os
import subprocess
import sys
from pathlib import Path
from dotenv import load_dotenv

# Get the project root directory (two levels up from this script)
PROJECT_ROOT = Path(__file__).parent.parent.parent
os.chdir(PROJECT_ROOT)

load_dotenv()

def main():
    # Check if DATABASE_URL is set
    if not os.getenv("DATABASE_URL"):
        print("❌ DATABASE_URL environment variable is not set")
        return 1
    
    print("✅ DATABASE_URL found")
    print(f"📁 Working directory: {os.getcwd()}")
    
    try:
        # Check if migrations directory has any files
        from pathlib import Path
        versions_dir = Path("alembic/versions")
        migration_files = [f for f in versions_dir.glob("*.py") if f.name != "__init__.py" and not f.name.startswith("__pycache__")]
        
        if not migration_files:
            # Create initial migration only if none exist
            print("📝 Creating initial migration...")
            result = subprocess.run([
                "alembic", "revision", "--autogenerate", "-m", "Initial migration"
            ], check=True, capture_output=True, text=True)
            print("✅ Initial migration created")
        else:
            print("📝 Found existing migration, skipping creation...")
        
        # Run migration
        print("🚀 Running migration...")
        result = subprocess.run([
            "alembic", "upgrade", "head"
        ], check=True, capture_output=True, text=True)
        print("✅ Database tables created successfully!")
        
        print("\n🎉 Database setup complete! Your tables are ready to use.")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        print(f"Command output: {e.stdout}")
        print(f"Command error: {e.stderr}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())