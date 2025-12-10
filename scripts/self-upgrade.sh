#!/bin/bash
# OmniCoder-AGI Self-Upgrade Script
# ==================================
#
# This script runs the self-upgrade process safely.
#
# Usage:
#   ./scripts/self-upgrade.sh [prompt_file] [github_pat]
#
# Examples:
#   ./scripts/self-upgrade.sh
#   ./scripts/self-upgrade.sh self-upgrade-prompt.txt
#   ./scripts/self-upgrade.sh self-upgrade-prompt.txt $GITHUB_PAT

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

# Default prompt file
PROMPT_FILE="${1:-self-upgrade-prompt.txt}"
GITHUB_PAT="${2:-$GITHUB_PAT}"

echo "============================================"
echo "  OmniCoder-AGI Self-Upgrade"
echo "============================================"
echo ""

# Check if prompt file exists
if [ ! -f "$PROMPT_FILE" ]; then
    echo "⚠️  Prompt file not found: $PROMPT_FILE"
    echo ""
    echo "Creating from template..."
    
    if [ -f "self-upgrade-prompt.template.txt" ]; then
        cp self-upgrade-prompt.template.txt "$PROMPT_FILE"
        echo "✅ Created $PROMPT_FILE from template"
        echo "   Please edit it with your upgrade instructions, then run this script again."
        exit 0
    else
        echo "❌ Template file not found. Creating default..."
        cat > "$PROMPT_FILE" << 'EOF'
Upgrade the OmniCoder-AGI system with improvements:
- Enhance code generation quality
- Improve test coverage
- Optimize performance
- Add new features as needed
EOF
        echo "✅ Created default $PROMPT_FILE"
    fi
fi

echo "📄 Using prompt file: $PROMPT_FILE"
echo ""

# Check for GitHub PAT
if [ -z "$GITHUB_PAT" ]; then
    echo "⚠️  No GitHub PAT provided."
    echo "   Set GITHUB_PAT environment variable or pass as second argument."
    echo ""
    echo "   Running upgrade without GitHub integration..."
    echo ""
    python3 -m cli.omnicoder_agi upgrade --from-file "$PROMPT_FILE" --auto
else
    echo "🔐 GitHub PAT configured"
    echo ""
    python3 -m cli.omnicoder_agi upgrade --from-file "$PROMPT_FILE" --token "$GITHUB_PAT" --auto
fi

echo ""
echo "============================================"
echo "  Self-Upgrade Complete!"
echo "============================================"
