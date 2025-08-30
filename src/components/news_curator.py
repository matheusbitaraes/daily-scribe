from collections import defaultdict
from components.database import DatabaseService
from datetime import datetime, timedelta, timezone

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules and user preferences.
    """
    def __init__(self,):
        self.db_service = DatabaseService()

    def curate_for_user(self, email_address):
        """
        Select up to max_per_category articles per category, filtered by user preferences and from the last 48 hours.
        Now also considers user embedding similarity to articles (if available).
        """
        import numpy as np
        # Get user preferences
        prefs = self.db_service.get_user_preferences(email_address)
        enabled_sources = prefs['enabled_sources'] if prefs and prefs.get('enabled_sources') else None
        enabled_categories = prefs['enabled_categories'] if prefs and prefs.get('enabled_categories') else None
        max_news_per_category = prefs['max_news_per_category'] if prefs and prefs.get('max_news_per_category') is not None else 10

        # Date range: last 24 hours
        end_date = datetime.now(timezone.utc)
        start_date = end_date - timedelta(hours=24)
        start_date_str = start_date.isoformat()
        end_date_str = end_date.isoformat()

        articles = self.db_service.get_unsent_articles(
            email_address,
            start_date=start_date_str,
            end_date=end_date_str,
            enabled_sources=[str(s) for s in enabled_sources] if enabled_sources else None,
            enabled_categories=enabled_categories
        )

        # Try to get user embedding
        user_embedding = None
        try:
            user_embedding = self.db_service.get_user_embedding(email_address)
        except Exception:
            user_embedding = None

        # If user embedding and article embeddings are available, rank by similarity
        if user_embedding is not None and len(articles) > 0:
            # Get all article embeddings and ids
            all_embeddings, all_ids = self.db_service.get_all_article_embeddings()
            # Map article id to embedding
            id_to_emb = {aid: emb for aid, emb in zip(all_ids, all_embeddings)}
            # Compute similarity for each article
            for a in articles:
                emb = id_to_emb.get(a['id'])
                if emb is not None:
                    # Cosine similarity
                    sim = float(np.dot(user_embedding, emb) / (np.linalg.norm(user_embedding) * np.linalg.norm(emb) + 1e-8))
                    a['user_similarity'] = sim
                else:
                    a['user_similarity'] = 0.0
            # Sort articles by similarity (descending)
            articles = sorted(articles, key=lambda x: x.get('user_similarity', 0), reverse=True)
        
        curated = []
        category_counts = defaultdict(int)
        for article in articles:
            categories = article.get('category')
            if not categories:
                categories = ['uncategorized']
            elif isinstance(categories, str):
                categories = [categories]
            added = False
            for cat in categories:
                if category_counts[cat] < max_news_per_category:    
                    curated.append(article)
                    for c in categories:
                        category_counts[c] += 1
                    added = True
                    break
            if added:
                continue
        return curated
