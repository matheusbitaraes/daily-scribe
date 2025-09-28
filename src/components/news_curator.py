import time
from collections import defaultdict
from components.database import DatabaseService
from datetime import datetime, timedelta, timezone, date
from components.article_clusterer import ArticleClusterer
from components.search.elasticsearch_service import ElasticsearchService
import os
import logging
from dotenv import load_dotenv
load_dotenv()

class NewsCurator:
    """
    Curates articles for the digest based on configurable rules and user preferences.
    """
    def __init__(self,):
        self.db_service = DatabaseService()
        self.es_service = ElasticsearchService()
        self.logger = logging.getLogger(__name__)

    def _parse_published_at_to_milliseconds(self, published_at):
        """
        Parse published_at field to milliseconds since epoch.
        Handles various formats: datetime objects, ISO strings, timestamps, and Elasticsearch objects.
        
        Args:
            published_at: The published_at value from an article
            
        Returns:
            int: Milliseconds since epoch, or 0 if parsing fails
        """
        if not published_at:
            return 0
            
        try:
            # Handle Elasticsearch datetime object
            if hasattr(published_at, 'value') and hasattr(published_at.value, 'millis'):
                return int(published_at.value.millis)
            
            # Handle Python datetime object
            elif isinstance(published_at, datetime):
                return int(published_at.timestamp() * 1000)
            
            # Handle ISO string format
            elif isinstance(published_at, str):
                # Handle both 'Z' and timezone formats
                dt_str = published_at.replace('Z', '+00:00')
                dt = datetime.fromisoformat(dt_str)
                return int(dt.timestamp() * 1000)
            
            # Handle numeric timestamp (assume seconds, convert to milliseconds)
            elif isinstance(published_at, (int, float)):
                return int(published_at * 1000)
            
            else:
                self.logger.warning(f"Unknown published_at format: {type(published_at)} - {published_at}")
                return 0
                
        except Exception as e:
            self.logger.warning(f"Failed to parse published_at '{published_at}': {e}")
            return 0

    def _curate_articles_legacy(self, categories=None, limit=10, start_date=None, end_date=None, offset=0):
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
            # get impact and urgency score, but convert to 1-5 (int) scale. Now its 0-100. so, 0-20 = 1, 21-40=2, 41-60=3, 61-80=4, 81-100=5
            urgency_raw = article.get('urgency_score', 0) or 0
            impact_raw = article.get('impact_score', 0) or 0

            # convert impact score to 1-5 scale
            def convert_score(score):
                return max(1, min(5, int(round(score/20))))  # convert 0-100 to 1-5 scale
                    
            urgency = convert_score(urgency_raw)
            impact = convert_score(impact_raw)

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
                    similar = clusterer.get_similar_articles(
                        article['id'],
                        enabled_source_ids=None,
                        top_k=int(os.getenv("CLUSTERIZATION_TOP_K", 20)),
                        similarity_threshold=float(os.getenv("CLUSTERIZATION_SIMILARITY_THRESHOLD_LEGACY", 0.75)),
                    )
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

    def _build_score_script(self):
        """
        Builds the score script for Elasticsearch queries.
        """
        # Calculate current time in milliseconds (Elasticsearch timestamp format)
        current_time = int(time.time() * 1000)

        # Define decay time
        decay_time = 3 * 24 * 60 * 60 * 1000  # after 3 days in milliseconds, urgency decays to 0

        # The score script consider the following: urgency_score and impact_score
        # also, it considers the decay of urgency_score over time (more recent articles with a 5 urgency will be better rated than older articles with a 5 urgency)
        score_script = """
            double impact = doc.containsKey('impact_score') && !doc['impact_score'].empty ? doc['impact_score'].value : 0;
            double urgency = doc.containsKey('urgency_score') && !doc['urgency_score'].empty ? doc['urgency_score'].value : 0;
            long publishedAt = doc.containsKey('published_at') && !doc['published_at'].empty ? doc['published_at'].value.millis : 0;
            double timeDiff = (params.current_time - publishedAt) / (double)params.decay_time;
            double decay = Math.max(0.0, 1.0 - timeDiff);
            return impact + (urgency * decay);
        """

        # Return the complete _script sort structure
        return {
                    "source": score_script,
                    "params": {
                        "current_time": current_time,
                        "decay_time": decay_time
                    }
                }

    def _curate_articles_elasticsearch(self, categories=None, limit=10, start_date=None, end_date=None, offset=0):
        """
        Curates articles using Elasticsearch with the same logic as legacy method.
        """
        # Set date range - default to last 2 days if not specified
        if not start_date:
            start_date = date.today() - timedelta(days=2)
        if not end_date:
            end_date = date.today()

        # Initialize Elasticsearch service
        try:
            if not self.es_service.is_healthy():
                self.logger.warning("Elasticsearch not healthy, falling back to legacy method")
                return self._curate_articles_legacy(categories, limit, start_date, end_date, offset)
        except Exception as e:
            self.logger.error(f"Failed to initialize Elasticsearch service: {e}")
            return self._curate_articles_legacy(categories, limit, start_date, end_date, offset)

        function_score_query = {
            "query": {
                "script_score": {
                    "query": {
                        "bool": {
                            "must": [{"match_all": {}}],
                            "filter": []
                        }
                    },
                    "script": self._build_score_script()
                }
            },
            "sort": [
                {"_score": {"order": "desc"}}
            ]
        }

        query = function_score_query["query"]["script_score"]["query"]

        # Add date range filter
        query["bool"]["filter"].append({
            "range": {
                "published_at": {
                    "gte": start_date.isoformat(),
                    "lte": end_date.isoformat()
                }
            }
        })

        # Add category filter if specified
        if categories:
            if isinstance(categories, str):
                categories = [cat.strip() for cat in categories.split(',')]
            # Normalize categories to lowercase for case-insensitive matching
            normalized_categories = [cat.lower() for cat in categories]
            query["bool"]["filter"].append({
                "terms": {
                    "category": normalized_categories
                }
            })

        # Filter for articles that have embeddings (needed for clustering)
        query["bool"]["filter"].append({
            "term": {
                "has_embedding": True
            }
        })

        try:
            # Get articles from Elasticsearch
            response = self.es_service.search(
                index_type="articles",
                query=function_score_query,
                size=limit * 10,  # Get more articles to allow for clustering
                from_=0
            )

            # prints the top 20 results with their scores, urgency_score, impact_score, and published_at
            print("Top 20 Elasticsearch results:")
            for hit in response["hits"]["hits"][:20]:
                source = hit["_source"]
                score = hit["_score"]
                urgency = source.get("urgency_score", 0)
                impact = source.get("impact_score", 0)
                published_at = source.get("published_at", "N/A")
                title_first_20_chars = source.get("title_pt", "N/A")[:20]
                print(f"ID: {source.get('id')}, Score: {score}, Urgency: {urgency}, Impact: {impact}, Published At: {published_at}, Title Start: {title_first_20_chars}")

            if not response or 'hits' not in response:
                self.logger.warning("No response from Elasticsearch, falling back to legacy method")
                return self._curate_articles_legacy(categories, limit, start_date, end_date, offset)

            # Convert ES response to article format
            articles = []
            for hit in response["hits"]["hits"]:
                article = hit["_source"]
                articles.append(article)

        except Exception as e:
            self.logger.error(f"Elasticsearch query failed: {e}, falling back to legacy method")
            return self._curate_articles_legacy(categories, limit, start_date, end_date, offset)

        # Rest of the clustering logic remains the same...
        clustered_curated_articles = []
        category_counts = defaultdict(int)
        used_article_ids = set()
        max_news_per_category = limit

        for article in articles:
            if article['id'] in used_article_ids:
                continue

            # Determine the categories for the current article
            article_categories = article.get('category')
            if not article_categories:
                article_categories = ['uncategorized']
            elif isinstance(article_categories, str):
                article_categories = [cat.strip() for cat in article_categories.split(',')]

            # Check if any category for this article is under the limit
            can_add_cluster = any(category_counts[cat] < max_news_per_category for cat in article_categories)

            if can_add_cluster:
                # Form a cluster around the current article
                cluster = [article]
                current_cluster_ids = {article['id']}
                
                # Use Elasticsearch vector similarity search for clustering
                try:
                    similar_articles = self.es_service.get_similar_articles(
                        article,
                        top_k=int(os.getenv("CLUSTERIZATION_TOP_K", 20)),
                        similarity_threshold=float(os.getenv("CLUSTERIZATION_SIMILARITY_THRESHOLD", 0.75)),
                        start_date=start_date,
                        end_date=end_date
                    )
                    
                    self.logger.debug(f"Found {len(similar_articles)} similar articles for article {article['id']} using Elasticsearch")
                    
                    for sim_article in similar_articles:
                        if sim_article['id'] not in used_article_ids:
                            cluster.append(sim_article)
                            current_cluster_ids.add(sim_article['id'])
                            
                except Exception as e:
                    self.logger.warning(f"Could not get similar articles for {article['id']} using Elasticsearch: {e}")

                # Add cluster and update counts
                clustered_curated_articles.append(cluster)
                used_article_ids.update(current_cluster_ids)
                for cat in article_categories:
                    category_counts[cat] += 1

        return clustered_curated_articles

    def curate_for_homepage(self, categories=None, limit=10, start_date=None, end_date=None, offset=0, use_search=False):

        if use_search:
            clustered_curated_articles = self._curate_articles_elasticsearch(
                categories=categories,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                offset=offset
            )
        else:
            clustered_curated_articles = self._curate_articles_legacy(
                categories=categories,
                limit=limit,
                start_date=start_date,
                end_date=end_date,
                offset=offset
            )
            
        return clustered_curated_articles

    def get_cluster_sort_key(self, cluster, verbose=False):
        # Sort all clusters by urgency + impact scores (highest first), then by size (largest first)
        if not cluster:
            return (0, 0, 0)
        main_article = cluster[0]
        urgency_raw = main_article.get('urgency_score', 0) or 0
        impact_raw = main_article.get('impact_score', 0) or 0

        # urgency score is affected by the time decay, so we need to consider that as well
        current_time = int(time.time() * 1000)
        decay_days = 4
        decay_time = decay_days * 24 * 60 * 60 * 1000  # after {{decay_days}} days in milliseconds, urgency decays to 0
        published_at_ms = self._parse_published_at_to_milliseconds(main_article.get('published_at'))
        time_diff = current_time - published_at_ms
        decay = max(0.0, 1.0 - time_diff / decay_time)
        urgency = urgency_raw * decay

        impact = impact_raw

        cluster_size = len(cluster) - 1 
        # return a weighted comparisson where urgency + impact is primary and size is secondary
        CLUSTERIZATION_MAX_VALUE = 10 # 10 or more clusters should be considered full size
       
        normalized_cluster_size = min(cluster_size / CLUSTERIZATION_MAX_VALUE if CLUSTERIZATION_MAX_VALUE > 0 else 0, 1.0) # normalize to 0-1 scale and cap at 1.0

        # normalize sum of urgency + impact to 0-1 scale
        normalized_urgency_impact_score = (urgency + impact) / 200.0  # max is 100 + 100 = 200

        
        # user similarity bonus (if available in main article)
        user_similarity = main_article.get('user_similarity', 0.0) # this value is between -1 and 1
        if user_similarity > 0:
            normalized_urgency_impact_score += user_similarity * 0.2  # add up to 0.2 bonus for positive similarity
            normalized_urgency_impact_score = min(normalized_urgency_impact_score, 1.0)  # cap at 1.0

        
        urgency_impact_weighted = normalized_urgency_impact_score * 0.7
        cluster_size_weighted = normalized_cluster_size * 0.3 if cluster_size > 0 else 0
        score = urgency_impact_weighted + cluster_size_weighted 


        # print all relevant information regarding all calculations above, using line breaks for clarity
        if verbose:
            self.logger.debug(f"Cluster main article ID: {main_article['id']} - Score: {score:.4f}")
            self.logger.debug(f" Urgency raw: {urgency_raw}, published At: {main_article.get('published_at')}, Decay: {decay:.4f}, Decayed Urgency: {urgency:.4f}")
            self.logger.debug(f" Impact raw: {impact_raw}")
            self.logger.debug(f" User Similarity: {user_similarity:.4f}, adding to Urgency+Impact: {user_similarity * 0.2:.4f}")
            self.logger.debug(f" Normalized Urgency+Impact+similarity Score: {normalized_urgency_impact_score:.4f}, Weighted: {urgency_impact_weighted:.4f}")
            self.logger.debug(f" Cluster size: {cluster_size}, Normalized Size: {normalized_cluster_size:.4f}, Weighted Size: {cluster_size_weighted:.4f}")
            self.logger.debug(f" {urgency_impact_weighted:.4f} + {cluster_size_weighted:.4f} = Total Score: {score:.4f}")
        return -score

    def sort_clusters(self, clusters, limit=None):
        sorted_clusters = sorted(clusters, key=self.get_cluster_sort_key)
        if limit is not None:
            sorted_clusters = sorted_clusters[:limit]
        return sorted_clusters
   
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

        self.logger.debug(f"User {email_address} preferences: sources={enabled_sources}, categories={enabled_categories}, max_news_per_category={max_news_per_category}")

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

        self.logger.debug(f"Found {len(articles)} unsent articles for user {email_address} from {start_date_str} to {end_date_str}")

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
                    # date threshold is start_date minus 1 day to allow for more similar articles
                    date_threshold = start_date - timedelta(days=1)
                    similar = clusterer.get_similar_articles(
                        article['id'],
                        enabled_source_ids,
                        top_k=int(os.getenv("CLUSTERIZATION_TOP_K", 20)),
                        similarity_threshold=float(os.getenv("CLUSTERIZATION_SIMILARITY_THRESHOLD_LEGACY", 0.75)),
                        date_threshold=date_threshold
                    )
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
        
        clustered_curated_articles = self.sort_clusters(clustered_curated_articles)

        self.logger.debug(f"Curated {len(clustered_curated_articles)} clusters for user {email_address}")
        if self.logger.isEnabledFor(logging.DEBUG):
            for cluster in clustered_curated_articles:
                self.logger.debug(f"Cluster: {[article['id'] for article in cluster]} - score: {self.get_cluster_sort_key(cluster, verbose=True):.4f}")
                for article in cluster:
                    self.logger.debug(f" - Article {article['id']}: Urgency {article.get('urgency_score', 0)}, Impact {article.get('impact_score', 0)}, Similarity {article.get('user_similarity', 0):.4f}, Category: {article.get('category', 'N/A')}, Title: {article.get('title_pt', '')[:20]}...")
                self.logger.debug("\n")

        return clustered_curated_articles