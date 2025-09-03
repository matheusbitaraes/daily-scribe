Epic 1: Core Digest Engine & Delivery

**Goal:** To establish the foundational backend service that can fetch content from a configured list of RSS feeds, summarize the new articles using a local LLM, aggregate them into a single digest, and deliver it via email on a daily schedule.

### Story 1.1: Project Setup and Configuration Loading

**As a** user,
**I want** a way to configure the application using a simple JSON file,
**so that** I can easily manage my RSS feeds and destination email address.

### Acceptance Criteria

1. The project structure (monorepo) is created.
2. A configuration file (e.g., `config.json`) is located in the root directory.
3. The application can successfully read the `config.json` file on startup.
4. The configuration file structure must support a list of RSS feed URLs and a single "to" email address.
5. If the configuration file is missing or malformed, the application logs a clear error message and exits gracefully.

### Story 1.2: Fetch and Parse RSS Feeds

**As the** system,
**I want** to fetch content from all RSS feeds listed in the configuration file,
**so that** I have the articles ready for processing.

### Acceptance Criteria

1. The system iterates through each RSS feed URL in the `config.json` file.
2. For each feed, it successfully fetches the raw XML content.
3. The system parses the XML to extract individual article links and titles.
4. The system includes basic error handling for invalid URLs or failed fetch attempts, logging a warning for any failed feed.
5. The system should be able to process at least 5 different RSS feeds concurrently.

### Story 1.3: Article Summarization via Local LLM

**As the** system,
**I want** to use a local LLM to summarize the content of a single article,
**so that** the core summarization logic is functional.

### Acceptance Criteria

1. The system can take the full text content of an article as input.
2. It processes the text through a configured lightweight LLM.
3. The LLM generates a summary that is 1-2 paragraphs long.
4. The summarization function can handle articles up to 3000 words.
5. The function returns the summary as a clean string.

### Story 1.4: Daily Digest Aggregation and Scheduling

**As a** user,
**I want** the system to automatically run once a day to create a consolidated digest,
**so that** I don't have to trigger it manually.

### Acceptance Criteria

1. A scheduler is implemented that triggers the digest creation process once every 24 hours.
2. The process fetches articles from all RSS feeds (from Story 1.2).
3. It identifies which articles are new since the last successful run.
4. For each new article, it generates a summary using the LLM (from Story 1.3).
5. It compiles all the new summaries into a single, formatted text document for the day's digest.
6. The digest format should include the article title and a link to the original source above each summary.

### Story 1.5: Email Delivery

**As a** user,
**I want** to receive the final aggregated digest via email,
**so that** I can read my personalized news summary conveniently.

### Acceptance Criteria

1. The system can connect to an email sending service (e.g., using SMTP).
2. The system takes the daily digest content and sends it as the body of an email.
3. The email is sent to the "to" address specified in the `config.json` file.
4. The subject line of the email should be "Your Daily Digest for [Current Date]".
5. The system logs a confirmation message upon successful email delivery.