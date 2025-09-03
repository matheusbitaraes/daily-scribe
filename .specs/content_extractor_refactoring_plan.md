### Refactoring Plan: `ContentExtractor`

This plan outlines the steps to split the content extraction and summarization processes into two distinct parts.

1.  **Database Modification:**
    *   A new table, `article_content`, will be created to store the raw content of scraped articles.
    *   **Schema for `article_content`:**
        *   `id`: Primary Key (INTEGER)
        *   `article_id`: Foreign Key to `articles.id` (INTEGER)
        *   `url`: URL of the article (TEXT)
        *   `raw_content`: The full scraped content of the article (TEXT)
        *   `created_at`: Timestamp of when the content was extracted (DATETIME)

2.  **Extraction Process:**
    *   The `ContentExtractor.extract_and_summarize` method will be replaced by a new method, `ContentExtractor.extract_and_save`.
    *   `extract_and_save` will:
        1.  Scrape the article content from the URL.
        2.  Save the raw content into the new `article_content` table.
    *   The `fetch_news` function in `src/main.py` will be updated to use `extract_and_save`.

3.  **Summarization Process:**
    *   A new standalone summarization process will be created.
    *   This process will:
        1.  Fetch articles from `article_content` that have not yet been summarized.
        2.  Use the `Summarizer` to generate a summary from the `raw_content`.
        3.  Save the summary and other metadata to the `articles` table.
    *   A new command, `summarize-articles`, will be added to `main.py` to trigger this process.

4.  **Execution Flow Update:**
    *   The `full-run` command in `main.py` will be updated to orchestrate the new two-step process:
        1.  Run `fetch-news` to extract and save article content.
        2.  Run `summarize-articles` to process the saved content and generate summaries.
