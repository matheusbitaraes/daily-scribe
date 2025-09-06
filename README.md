# Daily Scribe

A personal RSS digest generator that fetches content from configured RSS feeds, summarizes articles using a local LLM, and delivers daily digests via email.

## Project Status

This project is currently implementing **Epic 1: Core Digest Engine & Delivery**.

### Completed Stories
- ✅ **Story 1.1: Project Setup and Configuration Loading** - Project structure created with configuration loading functionality
- ✅ **Story 1.2: Fetch and Parse RSS Feeds** - RSS feed processing with concurrent fetching and parsing implemented
- ✅ **Story 1.3: Article Summarization via Local LLM** - Mock summarization service implemented with content extraction

### In Progress
- 🔄 **Story 1.4: Daily Digest Aggregation and Scheduling** - Coming next

### Upcoming Stories
- 📋 **Story 1.5: Email Delivery**

## Features

- **Configuration Management**: Simple JSON-based configuration for RSS feeds and email settings
- **RSS Feed Processing**: Fetch and parse multiple RSS feeds concurrently
- **Local LLM Integration**: Summarize articles using lightweight local language models
- **Automated Scheduling**: Daily digest generation and delivery
- **Email Delivery**: Send formatted digests to configured email addresses

## Quick Start

### Prerequisites

- Python 3.11+
- Git

### Installation

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd daily-scribe
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create your configuration file:
   ```bash
   cp config.json.example config.json
   ```

5. Edit `config.json` with your RSS feeds and email settings:
   ```json
   {
     "rss_feeds": [
       "https://feeds.bbci.co.uk/news/rss.xml",
       "https://rss.cnn.com/rss/edition.rss"
     ],
     "email": {
       "to": "your-email@example.com",
       "smtp_server": "smtp.gmail.com",
       "smtp_port": 587,
       "username": "your-email@gmail.com"
     },
     "schedule": {
       "hour": 8,
       "minute": 0
     }
   }
   ```

6. Test the configuration:
   ```bash
   python src/main.py
   ```

## Configuration

The application uses a `config.json` file for configuration. Here's the structure:

### RSS Feeds
- `rss_feeds`: Array of RSS feed URLs to monitor

### Email Settings
- `to`: Destination email address for digests
- `smtp_server`: SMTP server address
- `smtp_port`: SMTP server port
- `username`: SMTP username (password will be loaded from environment variables)

### Schedule
- `hour`: Hour of day to run (0-23)
- `minute`: Minute of hour to run (0-59)

## Environment Variables

The following environment variables are supported for configuration:

### Required Environment Variables
- `GEMINI_API_KEY`: Your Gemini API key for content summarization
- `SMTP_PASSWORD`: SMTP password for email delivery

### Optional Environment Variables
- `DB_PATH`: Path to SQLite database file (default: `data/digest_history.db`)
- `DB_TIMEOUT`: Database connection timeout in seconds (default: `30`)

### Example Environment Setup

Create a `.env` file in the project root (this file is git-ignored):

```bash
# Required
GEMINI_API_KEY=your-gemini-api-key-here
SMTP_PASSWORD=your-smtp-password-here

# Optional database configuration
DB_PATH=/custom/path/to/database.db
DB_TIMEOUT=45
```

Load environment variables before running:
```bash
source .env  # or use python-dotenv
python -m src.main
```

## Project Structure

```
daily-scribe/
├── config.json.example      # Example configuration file
├── requirements.txt         # Python dependencies
├── src/                    # Source code
│   ├── main.py            # Main application entry point
│   └── components/        # Core application components
│       └── config.py      # Configuration loader
├── tests/                  # Test files
├── data/                   # Data storage (SQLite database)
└── models/                 # Local LLM model files
```

## Development

### Running Tests

```bash
pytest tests/
```

### Database Management

#### Fetching Production Database
To fetch the latest production database for local development:

```bash
# View what would be fetched (dry run)
./scripts/fetch-production-db.sh --dry-run

# Fetch with confirmation prompts (auto-detects if snapshot needed)
./scripts/fetch-production-db.sh

# Recommended: Always use snapshot for consistency
./scripts/fetch-production-db.sh --snapshot --force

# Direct file copy (use when containers are stopped)
./scripts/fetch-production-db.sh --direct --force
```

The script will:
1. Backup your existing local database to `digest_history_backup_YYYYMMDD.db`
2. Create a consistent snapshot from the running container (if `--snapshot`) or copy directly from disk
3. Fetch the production database via SSH/rsync
4. Verify database integrity
5. Show database statistics

**Database Fetch Methods:**
- `--snapshot`: Creates a consistent backup from running container (recommended)
- `--direct`: Copies database file directly from host filesystem
- Default: Auto-detects and offers snapshot if containers are running

For more details, see [docs/fetch-production-db.md](docs/fetch-production-db.md).

### Code Quality

The project uses:
- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking

### Adding New Features

1. Create feature branch from `main`
2. Implement feature following the established patterns
3. Add tests for new functionality
4. Update documentation as needed
5. Submit pull request

## Contributing

This is a personal project, but suggestions and improvements are welcome!

## License

This project is for personal use only.