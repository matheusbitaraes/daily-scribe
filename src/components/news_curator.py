from collections import defaultdict
from components.database import DatabaseService
from datetime import datetime, timedelta, timezone, date
from components.article_clusterer import ArticleClusterer
import logging

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules and user preferences.
    """
    def __init__(self,):
        self.db_service = DatabaseService()
        self.logger = logging.getLogger(__name__)

    def curate_for_homepage(self, categories=None, limit=10, start_date=None, end_date=None, offset=0):
        # Set date range - default to last 2 days if not specified
        if not start_date:
            start_date = date.today() - timedelta(days=2)
        if not end_date:
            end_date = date.today()

            
        # Get articles for the specified criteria
        articles = self.db_service.get_articles(
            start_date=start_date.isoformat() if start_date else None,
            end_date=(end_date + timedelta(days=1)).isoformat() if end_date else None,
            categories=categories,
            limit=limit * 10,  # Get more articles to allow for clustering
            offset=0
        )

        # Sort articles by sum of urgency_score + impact_score (descending), then by user similarity if available
        def get_sort_key(article):
            urgency = article.get('urgency_score', 0) or 0
            impact = article.get('impact_score', 0) or 0
            # Primary sort: sum of urgency + impact (desc)
            return (-(urgency + impact),)

        articles = sorted(articles, key=get_sort_key)

        clustered_curated_articles = []
        category_counts = defaultdict(int)
        used_article_ids = set()
        clusterer = ArticleClusterer()
        max_news_per_category = limit

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
                    similar = clusterer.get_similar_articles(article['id'], enabled_source_ids=None, top_k=5, similarity_threshold=0.55)
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

    def curate_and_cluster(self, email_address: str):
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

        enabled_source_ids = [str(s) for s in enabled_sources] if enabled_sources else None

        articles = self.db_service.get_unsent_articles(
            email_address,
            start_date=start_date_str,
            end_date=end_date_str,
            source_ids=enabled_source_ids,
            categories=enabled_categories
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
        
        # Sort articles by sum of urgency_score + impact_score (descending), then by user similarity if available
        def get_sort_key(article):
            urgency = article.get('urgency_score', 0) or 0
            impact = article.get('impact_score', 0) or 0
            similarity = article.get('user_similarity', 0)
            # Primary sort: sum of urgency + impact (desc), then similarity (desc)
            return (-(urgency + impact), -similarity)
        
        articles = sorted(articles, key=get_sort_key)
        
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
                    similar = clusterer.get_similar_articles(article['id'], enabled_source_ids, top_k=5, similarity_threshold=0.55)
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