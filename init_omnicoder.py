#!/usr/bin/env python3
"""
OmniCoder-AGI Initialization Script

This script initializes the OmniCoder-AGI system with:
- GitHub PAT token configuration
- Initial AGI engine setup
- MCP server initialization
- First training cycle
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def main():
    print("=" * 60)
    print("  OmniCoder-AGI Initialization")
    print("  The World's Most Advanced Coding Automation Agent")
    print("=" * 60)
    print()
    
    # Import after path setup
    from cli.omnicoder_agi import (
        OmniCoderAGI, SettingsManager, ensure_dirs,
        REPO_ROOT, SETTINGS_PATH
    )
    
    # Ensure directories exist
    ensure_dirs()
    
    # Initialize settings
    settings = SettingsManager()
    
    print("📦 Initializing settings...")
    
    # Configure GitHub
    print("🔐 Configuring GitHub integration...")
    settings.set("github.username", "pythpythpython")
    settings.set("github.email", "pyth.pyth.python@gmail.com")
    
    # Note: The user provided their PAT token in the request
    # In production, this should be securely stored
    github_token = os.environ.get("GITHUB_PAT", "")
    if github_token:
        settings.set_github_pat(github_token)
        print("  ✅ GitHub PAT configured from environment")
    else:
        print("  ⚠️  No GITHUB_PAT environment variable found")
        print("     Set it with: export GITHUB_PAT=your_token")
        print("     Or use: omnicoder-agi github login --token YOUR_TOKEN")
    
    # Initialize AGI
    print()
    print("🤖 Initializing AGI engines...")
    agi = OmniCoderAGI(github_token=settings.get_github_pat())
    
    stats = agi.get_statistics()
    print(f"  ✅ {stats['total_engines']} engines loaded")
    print(f"  ✅ {stats['total_boards']} AGI boards available")
    print(f"  ✅ {stats['mcp_servers']} MCP servers configured")
    print(f"  📊 Current quality: {stats['current_quality'] * 100:.2f}%")
    print(f"  🎯 Target quality: {stats['target_quality'] * 100:.2f}%")
    
    # Check GitHub connection
    print()
    print("🔗 Checking GitHub connection...")
    if stats['github_connected']:
        user = agi.github.get_user()
        print(f"  ✅ Connected as: {user.get('login', 'unknown')}")
    else:
        print("  ⚠️  Not connected to GitHub")
    
    # List MCP servers
    print()
    print("🔌 MCP Servers:")
    for name, server in agi.mcp_router.list_servers().items():
        print(f"  - {name}: {server.name}")
    
    # Run initial training
    print()
    print("🏋️ Running initial training cycle...")
    
    metrics = agi.train_engines(
        problems=[
            "Create a REST API with authentication",
            "Implement a caching system",
            "Build a real-time notification service",
        ],
        intensity="high"
    )
    
    print(f"  ✅ Training complete")
    print(f"  📊 Quality: {metrics.quality_before * 100:.2f}% → {metrics.quality_after * 100:.2f}%")
    print(f"  ✅ Tests: {metrics.tests_passed}/{metrics.tests_total} passed")
    
    print()
    print("=" * 60)
    print("  ✅ OmniCoder-AGI Initialization Complete!")
    print("=" * 60)
    print()
    print("Quick Start Commands:")
    print()
    print("  # Run a task")
    print('  python -m cli run "Create a Python web scraper"')
    print()
    print("  # Multi-agent task")
    print('  python -m cli multi "Build a REST API" --agents 3')
    print()
    print("  # Train engines")
    print("  python -m cli train --intensity extreme")
    print()
    print("  # View statistics")
    print("  python -m cli stats")
    print()
    print("  # Self-upgrade")
    print('  python -m cli upgrade "Add new feature" --auto')
    print()
    print("  # List AGI boards")
    print("  python -m cli boards")
    print()
    print("  # GitHub integration")
    print("  python -m cli github login --token YOUR_TOKEN")
    print("  python -m cli github repos")
    print()
    print("  # Settings")
    print("  python -m cli settings show")
    print()
    print("For more help: python -m cli --help")
    print()

if __name__ == "__main__":
    main()
