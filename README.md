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

## Roadmap

- [x] RSS feed fetching and parsing
- [x] External model (Gemini API integration)
- [x] Handle rate limiting from the LLM API
- [x] Improve digest format and language
- [x] store publication date in the artice table as well as creation date in our side
- [x] Develop a categorization approach - implement a metadata extractor?
- [x] divide extraction of content and diggest to be different processes
- [x] Daily digest generation and scheduling
- [x] Email delivery system
- [x] Add a new table to track in which digest the articles were sent
- [x] Have a new column in sources that will hide them from ones email diggest (but we will keep on fetching the article news)
- [x] Advanced content filtering and categorization -> add a way to curate content when digest is really big - check [here](https://gemini.google.com/gem/fdc459572bee/7c4574e44151bd6c)
- [x] Similar news showing clustered
- [x] send source in digest
- [x] fix ordering
- [ ] split article fetch from article summarization 
      - store originals 
      - create a layer for translating each different rss?
- [ ] Web interface for configuration management
- [ ] Multiple digest formats (HTML, Markdown, etc.) 
- [ ] Web interface to subscription
- [ ] Local LLM integration for summarization