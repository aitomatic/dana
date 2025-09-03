#!/bin/bash

# Setup script for Kimi API key
echo "Setting up Kimi API key for Dana..."

# Set the API key
export MOONSHOT_API_KEY="sk-4GnZSJdTdTXZdS2i1koODAMkmTDCp8uj2OG112JcZHWWzn4e"

# Add to shell profile for persistence
if [[ "$SHELL" == *"zsh"* ]]; then
    PROFILE_FILE="$HOME/.zshrc"
elif [[ "$SHELL" == *"bash"* ]]; then
    PROFILE_FILE="$HOME/.bashrc"
else
    PROFILE_FILE="$HOME/.bash_profile"
fi

# Check if the export is already in the profile
if ! grep -q "MOONSHOT_API_KEY" "$PROFILE_FILE"; then
    echo "" >> "$PROFILE_FILE"
    echo "# Dana Kimi API Key" >> "$PROFILE_FILE"
    echo 'export MOONSHOT_API_KEY="sk-4GnZSJdTdTXZdS2i1koODAMkmTDCp8uj2OG112JcZHWWzn4e"' >> "$PROFILE_FILE"
    echo "Added MOONSHOT_API_KEY to $PROFILE_FILE"
else
    echo "MOONSHOT_API_KEY already exists in $PROFILE_FILE"
fi

echo "Kimi API key setup complete!"
echo "You can now run: dana agent.na" 