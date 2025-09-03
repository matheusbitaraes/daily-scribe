### Definitive Tech Stack Selections

1. **Primary Language: Python (Version 3.11+)**
    - **Justification:** Python has the most mature and extensive ecosystem for running local AI/ML models, especially with libraries like Hugging Face Transformers. It also has excellent, easy-to-use libraries for web scraping, RSS parsing, and database interaction, making it the ideal choice for this project.
2. **Core Frameworks & Libraries:**
    - **Application Runner: Typer**
        - **Justification:** While this is a monolithic script, using a simple framework like Typer will allow us to build a clean Command-Line Interface (CLI). This makes the script easy to run manually for testing and provides a structured entry point for the daily scheduled task.
    - **LLM Interaction: Hugging Face `transformers` & `PyTorch`**
        - **Justification:** This is the industry standard for loading and running open-source LLMs locally. It gives us access to a vast range of lightweight models that can run on the specified hardware.
    - **Scheduling: `schedule` library**
        - **Justification:** A simple, in-process scheduling library that is human-readable and platform-independent. It will allow us to define the "run daily" logic directly within the Python code, avoiding the need to configure OS-specific tools like Cron or Task Scheduler.
3. **Database: SQLite**
    - **Justification:** For this project, we only need to store a history of processed article URLs to avoid duplicates. SQLite is a zero-configuration, file-based database that is perfect for this. It requires no separate server and is natively supported in Python.
4. **Data Parsing & Fetching:**
    - **RSS Feeds: `feedparser`**
        - **Justification:** A robust and widely-used library for parsing all kinds of RSS and Atom feeds.
    - **Article Content: `requests` & `BeautifulSoup4`**
        - **Justification:** `requests` is the standard for making HTTP requests to get web page content. `BeautifulSoup4` is excellent for parsing the resulting HTML and extracting the core article text while stripping out ads, navigation, and other boilerplate.

### High-Level Overview

This system is designed as a **Monolithic Application**, executed as a single, scheduled script within a **Monorepo**. The primary data flow is linear and can be visualized as follows:

Snippet de código

```jsx
graph TD
    A[Start Daily Schedule] --> B{Read config.json};
    B --> C[Fetch RSS Feeds];
    C --> D[For each new article...];
    D --> E[Scrape Article Content];
    E --> F[Summarize with Local LLM];
    F --> G[Store Article URL in SQLite DB];
    G --> H[Aggregate Summaries into Digest];
    H --> I[Send Digest via Email];
    I --> J[End];
```

### Component View

Even though this is a monolith, we will structure the code into distinct logical components, each with a clear responsibility. This promotes clean, maintainable code.

- **Scheduler (`scheduler.py`):** The main entry point. It uses the `schedule` library to trigger the digest generation process once per day.
- **Config Loader (`config.py`):** Responsible for reading and validating the `config.json` file.
- **Database Service (`database.py`):** Manages all interactions with the SQLite database, primarily for checking if an article has already been processed and for storing the URLs of newly processed articles.
- **Feed Processor (`feed_processor.py`):** Takes the list of RSS feeds, fetches their content, and parses them to identify new article URLs.
- **Article Scraper (`scraper.py`):** Takes a URL, fetches the HTML, and uses `BeautifulSoup4` to extract the clean, readable text content of the article.
- **Summarization Service (`summarizer.py`):** This component will be responsible for loading the local LLM and providing a simple function that takes text and returns a summary.
- **Email Notifier (`notifier.py`):** Responsible for constructing the email and sending it using Python's `smtplib`.

### Project Structure

The project will be organized in a standard Python application layout within the monorepo.

Plaintext

```jsx
personal-digest/
├── .gitignore
├── config.json               # User configuration for RSS feeds and email
├── data/
│   └── digest_history.db     # The SQLite database file
├── docs/
│   └── architecture.md       # This document
├── models/                     # Directory to store the downloaded LLM files
├── requirements.txt            # Python dependencies
├── src/
│   ├── __init__.py
│   ├── main.py                 # Main script entry point, containing the scheduler logic
│   ├── components/
│   │   ├── __init__.py
│   │   ├── config.py           # Config Loader
│   │   ├── database.py         # Database Service
│   │   ├── feed_processor.py   # Feed Processor
│   │   ├── notifier.py         # Email Notifier
│   │   ├── scraper.py          # Article Scraper
│   │   └── summarizer.py       # Summarization Service
│   └── utils/
│       └── __init__.py
└── tests/
    ├── __init__.py
    └── test_placeholder.py   # Placeholder for future unit tests
```

This structure separates the main application logic (`main.py`) from the reusable components and ensures the project is organized and scalable.

### API Reference

This application does not provide any internal APIs. However, it consumes external resources and services.

### External Services Consumed

1. **RSS Feeds (Various)**
    - **Purpose:** To fetch the latest articles from user-defined news sources.
    - **Authentication:** None. These are typically public feeds.
    - **Key Endpoints Used:** The URLs provided by the user in `config.json`.
    - **Data Format:** XML (RSS or Atom standard).
2. **SMTP Email Service**
    - **Purpose:** To send the final digest to the user's email address.
    - **Authentication:** Requires SMTP server address, port, username, and password. These will need to be configured securely (details for this will be covered under Security Best Practices later).
    - **Key Endpoints Used:** Standard SMTP protocol for sending email.

### Data Models

### Core Application Entities

The primary entity is a representation of an `Article` as it's processed by the system.

- **Article Schema (In-memory object):**Python
    
    ```jsx
    # Example Python Dataclass representation
    from dataclasses import dataclass
    
    @dataclass
    class Article:
      title: str
      url: str
      summary: str
    ```
    

### Database Schema

The SQLite database will contain a single table to keep a history of processed articles to prevent sending duplicates.

- **Table Name:** `articles`
- **Purpose:** To store the URLs of articles that have already been included in a digest.
- **Schema Definition:**SQL
    
    ```jsx
    CREATE TABLE articles (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      url TEXT NOT NULL UNIQUE,
      summary TEXT 
      processed_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
    );
    ```
    

### Core Workflow / Sequence Diagram

This diagram illustrates how the logical components interact in sequence to generate and send the daily digest.

Snippet de código

```jsx
sequenceDiagram
    participant Scheduler
    participant ConfigLoader
    participant FeedProcessor
    participant DatabaseService
    participant Scraper
    participant Summarizer
    participant DigestBuilder
    participant Notifier

    Scheduler->>+ConfigLoader: load_config()
    ConfigLoader-->>-Scheduler: config_data

    Scheduler->>+FeedProcessor: fetch_new_articles(config_data.rss_feeds)
    FeedProcessor->>+DatabaseService: get_processed_urls()
    DatabaseService-->>-FeedProcessor: list_of_urls
    Note right of FeedProcessor: Fetches all RSS feeds and filters out articles whose URLs are already in the database.
    FeedProcessor-->>-Scheduler: new_articles_to_process

    loop For each new article
        Scheduler->>+Scraper: scrape_text(article_url)
        Scraper-->>-Scheduler: article_text
        Scheduler->>+Summarizer: summarize(article_text)
        Summarizer-->>-Scheduler: summary
        Scheduler->>+DatabaseService: mark_as_processed(article_url)
        DatabaseService-->>-Scheduler: success
    end

    Scheduler->>+DigestBuilder: build(summaries)
    DigestBuilder-->>-Scheduler: formatted_digest

    Scheduler->>+Notifier: send_email(config_data.email_details, formatted_digest)
    Notifier-->>-Scheduler: success/failure
```

### Infrastructure and Deployment Overview

- **Infrastructure:** This is a local application designed to run on a personal laptop. No cloud infrastructure is required.
- **Deployment:** Deployment consists of setting up the Python environment (`pip install -r requirements.txt`) and running the main script via an OS scheduler (Cron, Task Scheduler) or manually.

### Error Handling Strategy

- **General Approach:** Use standard Python exceptions for error flow.
- **Logging:** Use Python's built-in `logging` module to output status information and errors to the console and a log file (`digest.log`).
    - `INFO`: For routine process steps (e.g., "Starting daily run," "Digest sent successfully").
    - `WARNING`: For non-critical failures (e.g., "Failed to fetch RSS feed [URL], skipping.").
    - `ERROR`: For critical failures that stop the process (e.g., "Could not load LLM," "Email credentials invalid.").
- **Specific Handling Patterns:**
    - **Feed or Scraper Failure:** The application will log a `WARNING` and skip that specific article, but will continue processing the rest of the feeds. A single failed source should not prevent the entire digest.
    - **Summarization Failure:** The application will log an `ERROR` for the specific article and skip it, continuing with the others.
    - **Email Failure:** This is a critical path failure. The application will log a clear `ERROR` message indicating that the digest was generated but could not be sent.

### Coding Standards

- **Style Guide & Linter:** `Black` will be used for auto-formatting, and `Flake8` for linting to ensure code quality.
- **Naming Conventions:** `snake_case` for variables and functions, `PascalCase` for classes.
- **Type Safety:** Python type hints are mandatory for all function signatures and will be checked with `MyPy`. This ensures clarity for the developer agent.

### Security Best Practices

- **Secrets Management:** SMTP credentials (username, password) **must not** be stored in `config.json`. They should be loaded from environment variables or a `.env` file, which must be included in the `.gitignore` file to prevent accidental commits.

---