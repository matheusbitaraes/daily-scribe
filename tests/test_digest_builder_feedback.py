from components.digest_builder import DigestBuilder


def test_prepare_template_data_includes_feedback_links(monkeypatch):
    monkeypatch.setenv("MAIN_ARTICLES_NUMBER_FOR_BODY", "1")
    builder = DigestBuilder(template_dir="src/templates")
    clustered = [
        [{
            "id": 42,
            "url": "https://news.example/story",
            "title": "Example Story",
            "summary": "Summary",
            "category": "Technology",
            "source_name": "Example News"
        }],
        [{
            "id": 43,
            "url": "https://news.example/other",
            "title": "Another Story",
            "summary": "Another Summary",
            "category": "Technology",
            "source_name": "Example News"
        }]
    ]

    data = builder._prepare_template_data(
        clustered_summaries=clustered,
        preference_token="secure-token",
        unsubscribe_link_html="",
        max_clusters=5,
        base_url="https://dailyscribe.news",
        feedback_api_base_url="https://api.dailyscribe.news",
        digest_id="digest-2025-09-30"
    )

    main_news = data["main_news"][0]
    main_feedback = main_news["feedback"]

    assert main_feedback is not None
    assert main_feedback["positive_url"].startswith("https://dailyscribe.news/feedback/secure-token?")
    assert "article_id=42" in main_feedback["positive_url"]
    assert "signal=1" in main_feedback["positive_url"]
    assert "digest-2025-09-30" in main_feedback["positive_url"]
    assert main_feedback["negative_url"].startswith("https://dailyscribe.news/feedback/secure-token?")
    assert "signal=-1" in main_feedback["negative_url"]
    assert main_feedback["tooltip_positive"]
    assert main_feedback["tooltip_negative"]

    category_links = data["category_links"]
    assert category_links
    first_category = category_links[0]["articles"][0]
    category_feedback = first_category["feedback"]

    assert category_feedback is not None
    assert category_feedback["positive_url"].startswith("https://dailyscribe.news/feedback/secure-token?")
    assert "article_id=43" in category_feedback["positive_url"]
    assert "signal=1" in category_feedback["positive_url"]
    assert "digest-2025-09-30" in category_feedback["positive_url"]
    assert category_feedback["negative_url"].startswith("https://dailyscribe.news/feedback/secure-token?")
    assert "signal=-1" in category_feedback["negative_url"]
