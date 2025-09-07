## Goals and Background Context

### Goals

- **Save Time:** Eliminate the need to manually browse multiple news websites daily.
- **Stay Informed:** Receive a daily, focused summary of news and updates on specific, user-defined topics.
- **Personalization:** Ensure the content is highly relevant by basing it on personal preferences.

### Background Context

The user wants to solve the problem of information fragmentation and the time-consuming nature of daily news consumption. Instead of visiting many different sources, the user desires a single, consolidated digest tailored to their interests. The system has evolved from a personal project into a comprehensive news aggregation platform with web interface capabilities and flexible deployment options supporting both local and cloud-based infrastructure.

### Functional Requirements

- **FR1:** The system must allow a user to provide a list of RSS feeds as news sources.
- **FR2:** The system shall fetch new articles from all provided RSS feeds on a daily schedule.
- **FR3:** For each fetched article, the system will generate a summary that is one to two paragraphs long using external LLM APIs.
- **FR4:** The system will aggregate all the summaries from a single day into one daily digest. The news should be aggregated by main topics using intelligent clustering.
- **FR5:** The system must be able to send the final digest to user-configured email addresses.
- **FR6:** The system provides both configuration file management and web-based user preference management.
- **FR7:** *(New)* The system shall provide a web interface for digest simulation, preview, and user preference management.
- **FR8:** *(New)* The system must support multiple users with individual preferences and authentication tokens.
- **FR9:** *(New)* The system shall provide API endpoints for external integration and automation.

### Non-Functional Requirements

- **NFR1:** The entire process of fetching, summarizing, and sending the daily digest should complete within a few minutes (e.g., under 5 minutes).
- **NFR2:** System configuration supports both JSON file management and database-driven user preferences.
- **NFR3:** The system must be deployable on various platforms from personal laptops to cloud servers and home servers.
- **NFR4:** *(Updated)* The system utilizes external LLM APIs (Google Gemini, OpenAI) for reliable and scalable content processing.
- **NFR5:** *(New)* The web interface must be responsive and accessible on desktop and mobile devices.
- **NFR6:** *(New)* API responses must be performant with typical response times under 500ms for user interfaces.
- **NFR7:** *(New)* The system must provide secure token-based authentication for user preference management.

## Technical Assumptions

### Repository Structure: Monorepo

The project will be contained within a single Git repository. This approach simplifies dependency management and version control for a self-contained application.

### Service Architecture: Monolith

The application will be built as a single, unified service (a monolith). This is the most straightforward architecture for this project, reducing deployment and operational complexity.