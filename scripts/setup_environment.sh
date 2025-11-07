#!/bin/bash

# This script sets up the environment for Claude Code on the web
# It only runs in remote environments, not locally

# Exit immediately if a command exits with a non-zero status
set -e

# Check if running in remote environment (Claude Code on the web)
if [ "$CLAUDE_CODE_REMOTE" != "true" ]; then
  echo "Skipping setup - not in remote environment"
  exit 0
fi

echo "Setting up environment for Claude Code on the web..."

# Install dependencies using uv
echo "Installing project dependencies with uv..."
uv sync

echo "Environment setup completed successfully!"
exit 0
