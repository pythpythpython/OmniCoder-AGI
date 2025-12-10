#!/bin/bash
# Remove Secrets from Git History
# ================================
#
# This script helps remove accidentally committed secrets from git history.
# Use this when GitHub Push Protection blocks your push.
#
# Usage:
#   ./scripts/remove-secret-from-history.sh [file_with_secret]

set -e

FILE_TO_CLEAN="${1:-self-upgrade-prompt.txt}"

echo "============================================"
echo "  Remove Secret from Git History"
echo "============================================"
echo ""
echo "⚠️  WARNING: This will rewrite git history!"
echo "   File to clean: $FILE_TO_CLEAN"
echo ""

read -p "Continue? (y/N) " confirm
if [ "$confirm" != "y" ] && [ "$confirm" != "Y" ]; then
    echo "Cancelled"
    exit 0
fi

# Check if file exists in history
if ! git log --all --full-history -- "$FILE_TO_CLEAN" | head -1 | grep -q commit; then
    echo "❌ File not found in git history: $FILE_TO_CLEAN"
    exit 1
fi

echo ""
echo "🔧 Method 1: Remove file from last commit (if secret was just added)"
echo "   git reset HEAD~1"
echo "   # Edit the file to remove the secret"
echo "   git add $FILE_TO_CLEAN"
echo "   git commit -m 'Add upgrade prompt (without secrets)'"
echo ""

echo "🔧 Method 2: Remove file entirely from history (nuclear option)"
echo "   git filter-branch --force --index-filter \\"
echo "     'git rm --cached --ignore-unmatch $FILE_TO_CLEAN' \\"
echo "     --prune-empty --tag-name-filter cat -- --all"
echo ""

echo "🔧 Method 3: Use BFG Repo Cleaner (recommended for large repos)"
echo "   # Install: brew install bfg"
echo "   bfg --delete-files $FILE_TO_CLEAN"
echo "   git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo ""

echo "Choose a method:"
echo "  1. Reset last commit (safest, if secret is in last commit only)"
echo "  2. Delete file from all history"
echo "  q. Quit and do manually"
echo ""

read -p "Choice: " choice

case $choice in
    1)
        echo ""
        echo "Resetting last commit..."
        git reset HEAD~1
        echo ""
        echo "✅ Last commit reset. Now:"
        echo "   1. Edit $FILE_TO_CLEAN to remove any secrets"
        echo "   2. Run: git add $FILE_TO_CLEAN"
        echo "   3. Run: git commit -m 'Your commit message'"
        echo "   4. Run: git push --force origin BRANCH_NAME"
        ;;
    2)
        echo ""
        echo "⚠️  This will remove $FILE_TO_CLEAN from ALL history!"
        read -p "Are you absolutely sure? (yes/no) " confirm2
        if [ "$confirm2" = "yes" ]; then
            git filter-branch --force --index-filter \
                "git rm --cached --ignore-unmatch $FILE_TO_CLEAN" \
                --prune-empty --tag-name-filter cat -- --all
            echo ""
            echo "✅ File removed from history"
            echo "   Now run: git push --force origin BRANCH_NAME"
        else
            echo "Cancelled"
        fi
        ;;
    *)
        echo "Manual intervention required. See instructions above."
        ;;
esac
