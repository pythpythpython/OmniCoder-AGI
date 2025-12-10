#!/bin/bash
# Fix Git Divergent Branches
# ==========================
#
# This script helps fix divergent branches by rebasing onto origin/main.
#
# Usage:
#   ./scripts/fix-git-divergence.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$REPO_ROOT"

echo "============================================"
echo "  Fix Git Divergent Branches"
echo "============================================"
echo ""

# Configure git pull behavior
echo "🔧 Configuring git pull to use rebase..."
git config pull.rebase true

# Fetch latest
echo "📥 Fetching latest changes..."
git fetch origin

# Check current branch
CURRENT_BRANCH=$(git branch --show-current)
echo "📍 Current branch: $CURRENT_BRANCH"

# Check for divergence
LOCAL=$(git rev-parse @)
REMOTE=$(git rev-parse @{u} 2>/dev/null || echo "")
BASE=$(git merge-base @ @{u} 2>/dev/null || echo "")

if [ -z "$REMOTE" ]; then
    echo "⚠️  No upstream branch set"
    exit 0
fi

if [ "$LOCAL" = "$REMOTE" ]; then
    echo "✅ Branch is up to date"
    exit 0
elif [ "$LOCAL" = "$BASE" ]; then
    echo "⬇️  Need to pull (fast-forward possible)"
    git pull --rebase origin "$CURRENT_BRANCH"
elif [ "$REMOTE" = "$BASE" ]; then
    echo "⬆️  Need to push"
    echo "   Run: git push origin $CURRENT_BRANCH"
else
    echo "🔀 Branches have diverged"
    echo ""
    echo "Options:"
    echo "  1. Rebase onto remote (recommended for clean history):"
    echo "     git pull --rebase origin $CURRENT_BRANCH"
    echo ""
    echo "  2. Merge with remote:"
    echo "     git pull --no-rebase origin $CURRENT_BRANCH"
    echo ""
    echo "  3. Force push (DANGER - overwrites remote):"
    echo "     git push --force origin $CURRENT_BRANCH"
    echo ""
    echo "  4. Reset to remote (DANGER - loses local commits):"
    echo "     git reset --hard origin/$CURRENT_BRANCH"
    echo ""
    
    read -p "Choose option (1-4) or 'q' to quit: " choice
    
    case $choice in
        1)
            echo "Rebasing..."
            git pull --rebase origin "$CURRENT_BRANCH"
            ;;
        2)
            echo "Merging..."
            git pull --no-rebase origin "$CURRENT_BRANCH"
            ;;
        3)
            echo "Force pushing..."
            git push --force origin "$CURRENT_BRANCH"
            ;;
        4)
            echo "Resetting to remote..."
            git reset --hard "origin/$CURRENT_BRANCH"
            ;;
        *)
            echo "Cancelled"
            exit 0
            ;;
    esac
fi

echo ""
echo "✅ Done!"
