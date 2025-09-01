#!/bin/zsh

# Source your zsh configuration to load environment variables (like API keys)
source /Users/Matheus/.zshrc

# Navigate to your project directory
cd /Users/Matheus/daily-scribe

# Run the python script using the virtual environment's python
# The script will inherit the environment variables sourced above
/Users/Matheus/daily-scribe/venv/bin/python src/main.py $1