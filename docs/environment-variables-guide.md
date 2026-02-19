# Environment Variables Guide

## Overview

Daily Scribe uses environment variables for configuration to keep sensitive information secure and allow for different configurations across development, testing, and production environments.

## Environment Variable Loading

### Automatic Loading
The application automatically loads environment variables from a `.env` file in the project root using the `python-dotenv` library. This is handled by the `components.env_loader` module.

### Centralized Access
All environment variable access should go through the `components.env_loader` module to ensure consistent loading and error handling:

```python
from components.env_loader import get_env_var, get_jwt_secret_key

# Get any environment variable with optional default
api_key = get_env_var('GEMINI_API_KEY', 'default-key')

# Get JWT secret key specifically
jwt_secret = get_jwt_secret_key()
```

## Required Environment Variables

### Security
- `JWT_SECRET_KEY`: Secret key for signing JWT tokens used in unsubscribe and preference management

### API Keys
- `GEMINI_API_KEY`: API key for Google Gemini AI service (primary free-tier summarization)
- `OPENAI_API_KEY`: API key for OpenAI (optional, used as paid fallback when free tiers are exhausted)
- `GROQ_API_KEY`: (Optional) Groq API key for high-speed free-tier models (e.g. Llama 3.3 70B)
- `DEEPSEEK_API_KEY`: (Optional) DeepSeek API key for free-tier fallback
- `OPENROUTER_API_KEY`: (Optional) OpenRouter API key for 30+ free models as meta fallback
- `OLLAMA_HOST`: (Optional) URL for local Ollama instance (e.g. `http://localhost:11434`) for offline fallback
- `LLM_MODEL_OVERRIDE`: (Optional) Override model for testing (e.g. `ollama/llama3.1`)
- `SMTP_PASSWORD`: Password for email SMTP authentication

### Database
- `DB_PATH`: Path to SQLite database file (default: `/data/digest_history.db`)
- `DB_TIMEOUT`: Database connection timeout in seconds (default: 30)

### Email Configuration
Email settings are typically loaded through the config.json file, but some sensitive values come from environment variables.

### Backup Configuration (Litestream)
- `GCS_SERVICE_ACCOUNT_PATH`: Path to Google Cloud Service Account JSON file
- `GCS_BUCKET`: Google Cloud Storage bucket name for backups
- `GCS_REGION`: Google Cloud Storage region

## Setting Up Environment Variables

### Development
1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` with your actual values:
   ```bash
   JWT_SECRET_KEY=your-256-bit-secret-key-here
   GEMINI_API_KEY=your-actual-gemini-api-key
   SMTP_PASSWORD=your-actual-smtp-password
   ```

### Production
Set environment variables through your deployment system:
- Docker: Use environment variables in docker-compose.yml or Dockerfile
- Kubernetes: Use ConfigMaps and Secrets
- Server deployment: Export variables in shell or use systemd environment files

## Security Best Practices

1. **Never commit `.env` files** to version control
2. **Use strong, unique secrets** for JWT_SECRET_KEY
3. **Rotate secrets regularly** in production
4. **Use different values** for development, testing, and production
5. **Limit access** to environment files and variables

## Troubleshooting

### Environment Variables Not Loading
If environment variables are not being loaded:

1. Check that `.env` file exists in the project root
2. Verify the file format (KEY=value, one per line)
3. Ensure no spaces around the `=` sign
4. Check that `python-dotenv` is installed
5. Verify imports are using `components.env_loader`

### Testing Environment Loading
You can test environment loading with:

```python
# Test basic loading
python -c "
import sys
sys.path.insert(0, 'src')
from components.env_loader import get_jwt_secret_key
print('JWT Secret:', get_jwt_secret_key())
"

# Run the environment loader tests
python -m pytest tests/test_env_loader.py -v
```

## Migration from Direct os.getenv

If you have code using `os.getenv()` directly, migrate to use the centralized loader:

**Before:**
```python
import os
secret = os.getenv('JWT_SECRET_KEY', 'default')
```

**After:**
```python
from components.env_loader import get_jwt_secret_key
secret = get_jwt_secret_key()
```

This ensures consistent environment loading and better error handling.

## Database Migrations

Daily Scribe includes an automatic migration system that runs when the application starts. Recent migrations include:

- **006_migrate_user_preferences_to_users**: Automatically migrates users from the `user_preferences` table to the `users` table with `is_active = 1`. This ensures that all existing users are properly set up in the subscription management system.

You can run migrations manually if needed:

```python
from utils.migrations import migrate_database
result = migrate_database()
print('Migration result:', result)
```
