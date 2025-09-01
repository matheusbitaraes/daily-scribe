from collections import defaultdict
from components.database import DatabaseService
from datetime import datetime, timedelta, timezone
from components.article_clusterer import ArticleClusterer
import logging

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules and user preferences.
    """
    def __init__(self,):
        self.db_service = DatabaseService()
        self.logger = logging.getLogger(__name__)

    def curate_and_cluster_for_user(self, email_address):
        """
        Select up to max_per_category articles per category, filtered by user preferences and from the last 24 hours.
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
        
        
        clustered_curated_articles = []
        category_counts = defaultdict(int)
        used_article_ids = set()
        clusterer = ArticleClusterer()

        for article in articles:
            if article['id'] in used_article_ids:
                continue

            # Determine the categories for the current article
            categories = article.get('category')
            if not categories:
                categories = ['uncategorized']
            elif isinstance(categories, str):
                categories = [cat.strip() for cat in categories.split(',')]

            # Check if any category for this article is under the limit
            can_add_cluster = any(category_counts[cat] < max_news_per_category for cat in categories)

            if can_add_cluster:
                # Form a cluster around the current article
                cluster = [article]
                current_cluster_ids = {article['id']}
                
                try:
                    similar = clusterer.get_similar_articles(article['id'], top_k=5, similarity_threshold=0.55)
                    for sim_article in similar:
                        if sim_article['id'] not in used_article_ids:
                            cluster.append(sim_article)
                            current_cluster_ids.add(sim_article['id'])
                except Exception as e:
                    self.logger.warning(f"Could not get similar articles for {article['id']}: {e}")

                # Add cluster and update counts
                clustered_curated_articles.append(cluster)
                used_article_ids.update(current_cluster_ids)
                for cat in categories:
                    category_counts[cat] += 1
        
        return clustered_curated_articles

    def curate_and_cluster_for_user_alt(self, email_address: str):
        """
        Curates and clusters articles by first filtering, then clustering within categories.
        1) Gets articles from the last 24h and filters based on user preferences.
        2) Calls clusterer.perform_clustering to get up to max_news_per_category clusters for each category.
        """
        # 1. Get articles from last 24h and filter based on user preferences.
        prefs = self.db_service.get_user_preferences(email_address)
        enabled_sources = prefs.get('enabled_sources') if prefs else None
        enabled_categories = prefs.get('enabled_categories') if prefs else None
        max_news_per_category = prefs.get('max_news_per_category', 10) if prefs else 10

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

        if not articles:
            self.logger.info("No articles found for curation.")
            return []

        # Group articles by category
        articles_by_category = defaultdict(list)
        for article in articles:
            categories = article.get('category')
            if not categories:
                categories = ['uncategorized']
            elif isinstance(categories, str):
                categories = [cat.strip() for cat in categories.split(',')]
            
            for cat in categories:
                articles_by_category[cat].append(article)

        # 2. Call clusterer.perform_clustering for each category
        clusterer = ArticleClusterer()
        all_clustered_articles = []
        
        for category, cat_articles in articles_by_category.items():
            if not cat_articles:
                continue
            
            num_clusters = min(max_news_per_category, len(cat_articles))
            if num_clusters == 0:
                continue

            self.logger.info(f"Clustering {len(cat_articles)} articles for category '{category}' into {num_clusters} clusters.")
            
            clusters = clusterer.perform_clustering(articles=cat_articles, n_clusters=num_clusters)
            
            all_clustered_articles.extend(clusters[:max_news_per_category])

        return all_clustered_articles

