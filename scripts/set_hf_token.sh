#!/bin/bash
# Script to set Hugging Face token as environment variable
# This makes it persistent across sessions

if [ -z "$1" ]; then
    echo "Usage: ./scripts/set_hf_token.sh YOUR_TOKEN"
    echo ""
    echo "Or run interactively:"
    read -sp "Enter your Hugging Face token: " TOKEN
    echo ""
else
    TOKEN="$1"
fi

# Detect shell and add to appropriate config file
if [ -n "$ZSH_VERSION" ]; then
    CONFIG_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    CONFIG_FILE="$HOME/.bashrc"
else
    CONFIG_FILE="$HOME/.profile"
fi

# Check if token already exists in config
if grep -q "HF_TOKEN" "$CONFIG_FILE" 2>/dev/null; then
    echo "⚠️  HF_TOKEN already exists in $CONFIG_FILE"
    read -p "Do you want to update it? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # Remove old token line
        sed -i.bak '/^export HF_TOKEN=/d' "$CONFIG_FILE"
    else
        echo "Cancelled."
        exit 0
    fi
fi

# Add token to config file
echo "" >> "$CONFIG_FILE"
echo "# Hugging Face token for SkyGuard" >> "$CONFIG_FILE"
echo "export HF_TOKEN=\"$TOKEN\"" >> "$CONFIG_FILE"

echo "✅ HF_TOKEN added to $CONFIG_FILE"
echo ""
echo "To use it in this session, run:"
echo "  export HF_TOKEN=\"$TOKEN\""
echo "  source $CONFIG_FILE"
echo ""
echo "Or restart your terminal."

