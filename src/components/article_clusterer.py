import openai
import os
import numpy as np
import logging
from typing import List, Dict, Tuple
from datetime import datetime
from components.database import DatabaseService
from sklearn.cluster import KMeans
from sklearn.metrics.pairwise import cosine_similarity

logger = logging.getLogger(__name__)

class ArticleClusterer:
    def __init__(self, openai_api_key: str = os.environ.get("OPENAI_API_KEY")):
        self.db_service = DatabaseService()
        self.client = openai.OpenAI(api_key=openai_api_key)
        self.embedding_model = "text-embedding-3-small"

    def get_articles_without_embeddings(self) -> List[Dict]:
        return self.db_service.get_articles_without_embeddings()

    def create_text_for_embedding(self, article: Dict) -> str:
        parts = []
        
        # Use Portuguese title if available, otherwise fallback to original title
        preferred_title = article.get('title_pt') or article.get('title')
        if preferred_title:
            parts.append(f"Title: {preferred_title}")
        
        # Use Portuguese summary if available, otherwise fallback to English
        preferred_summary = article.get('summary_pt') or article.get('summary')
        if preferred_summary:
            parts.append(f"Summary: {preferred_summary}")
            
        if article.get('category'):
            parts.append(f"Category: {article['category']}")
        if article.get('keywords'):
            parts.append(f"Keywords: {article['keywords']}")
        
        # Parse raw_content JSON and extract text by type
        if article.get('raw_content'):
            try:
                import json
                content_parts = json.loads(article['raw_content'])
                content_by_type = {}
                
                for part in content_parts:
                    if isinstance(part, dict) and part.get('text') and part.get('type'):
                        content_type = part['type']
                        text = part['text'].strip()
                        if text:  # Only include non-empty text
                            if content_type not in content_by_type:
                                content_by_type[content_type] = []
                            content_by_type[content_type].append(text)
                
                # Add content by type in a structured way
                for content_type, texts in content_by_type.items():
                    if content_type == 'title':
                        # Skip title if we already have it from the article metadata
                        if not preferred_title:
                            parts.append(f"Title: {' | '.join(texts)}")
                    elif content_type == 'summary':
                        # Skip summary if we already have it from the article metadata
                        if not preferred_summary:
                            parts.append(f"Summary: {' | '.join(texts)}")
                    elif content_type == 'content':
                        parts.append(f"Content: {' | '.join(texts)}")
                    elif content_type == 'description':
                        parts.append(f"Description: {' | '.join(texts)}")
                    elif content_type == 'subtitle':
                        parts.append(f"Subtitle: {' | '.join(texts)}")
                    elif content_type == 'scraped':
                        parts.append(f"Article Text: {' | '.join(texts)}")
                    else:
                        # For any other content types
                        parts.append(f"{content_type.capitalize()}: {' | '.join(texts)}")
                        
            except (json.JSONDecodeError, TypeError) as e:
                logger.warning(f"Failed to parse raw_content as JSON for article ID {article.get('id')}: {e}")
                # Fallback to using raw_content as-is
                parts.append(f"Content: {article['raw_content']}")
        
        return " | ".join(parts)

    def get_embedding(self, text: str) -> List[float]:
        try:
            text = text.replace("\n", " ").strip()
            if len(text) > 8000:
                text = text[:8000]
            response = self.client.embeddings.create(
                input=text,
                model=self.embedding_model
            )
            return response.data[0].embedding
        except Exception as e:
            logger.error(f"Error getting embedding: {e}")
            raise

    def store_embedding(self, article_id: int, embedding: List[float]):
        embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()
        self.db_service.store_article_embedding(article_id, embedding_bytes)

    def generate_embeddings(self, batch_size: int = 10, delay: float = 1.0):
        articles = self.get_articles_without_embeddings()
        logger.info(f"Found {len(articles)} articles without embeddings")
        if not articles:
            logger.info("All articles already have embeddings")
            return
        for i, article in enumerate(articles):
            try:
                logger.info(f"Processing article {i+1}/{len(articles)}: ID {article['id']}")
                text = self.create_text_for_embedding(article)
                if not text.strip():
                    logger.warning(f"No text content for article ID {article['id']}, skipping")
                    continue
                embedding = self.get_embedding(text)
                self.store_embedding(article['id'], embedding)
                logger.info(f"Stored embedding for article ID {article['id']}")
                if (i + 1) % batch_size == 0:
                    logger.info(f"Processed {i+1} articles, sleeping for {delay} seconds...")
                    import time
                    time.sleep(delay)
            except Exception as e:
                logger.error(f"Error processing article ID {article['id']}: {e}")
                continue

    def get_all_embeddings(self, article_ids: List[int] = None) -> Tuple[np.ndarray, List[int]]:
        return self.db_service.get_all_article_embeddings(article_ids=article_ids)

    def perform_clustering(self, articles: List[Dict], n_clusters: int = 10, similarity_threshold: float = 0.5) -> List[List[Dict]]:
        """
        Performs clustering on a given list of articles.
        """
        logger.info(f"Starting clustering for {len(articles)} articles into {n_clusters} clusters.")
        
        if not articles:
            return []

        article_ids = [article['id'] for article in articles]
        embeddings, found_article_ids = self.get_all_embeddings(article_ids=article_ids)

        if len(embeddings) < n_clusters:
            logger.warning(f"Number of articles with embeddings ({len(embeddings)}) is less than n_clusters ({n_clusters}). "
                           f"Adjusting n_clusters to {len(embeddings)}. Or returning all articles as a single cluster if no embeddings.")
            if len(embeddings) == 0:
                return [articles]
            n_clusters = len(embeddings)

        # Map article IDs to articles for easy lookup
        articles_by_id = {article['id']: article for article in articles}

        # Filter out articles for which no embedding was found
        original_articles = [articles_by_id[id] for id in found_article_ids]

        kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
        cluster_labels = kmeans.fit_predict(embeddings)
        cluster_centers = kmeans.cluster_centers_

        clusters = [[] for _ in range(n_clusters)]
        for i, label in enumerate(cluster_labels):
            embedding = embeddings[i].reshape(1, -1)
            center = cluster_centers[label].reshape(1, -1)
            similarity = cosine_similarity(embedding, center)[0][0]
            if similarity >= similarity_threshold:
                clusters[label].append(original_articles[i])

        # Filter out empty clusters
        clusters = [cluster for cluster in clusters if cluster]

        # Sort clusters by size (largest first)
        clusters.sort(key=len, reverse=True)
        
        logger.info(f"Clustering complete. Found {len(clusters)} clusters after applying similarity threshold.")
        return clusters

    def analyze_clusters(self, run_id: str) -> Dict:
        return self.db_service.analyze_clusters(run_id)

    def get_similar_articles(self, article_id: int, enabled_source_ids: List[int] = None, top_k: int = 5, similarity_threshold: float = 0.85, date_threshold: datetime = None) -> List[Dict]:
        embeddings, article_ids = self.get_all_embeddings()
        if article_id not in article_ids:
            raise ValueError(f"Article ID {article_id} not found in embeddings")
        ref_idx = article_ids.index(article_id)
        ref_embedding = embeddings[ref_idx].reshape(1, -1)
        similarities = cosine_similarity(ref_embedding, embeddings)[0]
        # Get indices sorted by similarity, descending, skip self
        similar_indices = np.argsort(similarities)[::-1][1:]
        results = []
        for idx in similar_indices:
            sim_article_id = article_ids[idx]
            similarity_score = similarities[idx]
            if similarity_score < similarity_threshold:
                continue
            article = self.db_service.get_article_by_id(sim_article_id)
            if article:
                # Filter by enabled source IDs if provided
                if enabled_source_ids is not None and str(article.get('source_id')) not in enabled_source_ids:
                    continue

                # Filter by date if date_threshold is provided
                if date_threshold is not None and article.get('published_at'):
                    published_at = datetime.fromisoformat(article['published_at'])
                    
                    # Handle timezone awareness mismatch
                    if date_threshold.tzinfo is not None and published_at.tzinfo is None:
                        # date_threshold is timezone-aware, published_at is naive
                        # Assume published_at is in UTC if no timezone info
                        from datetime import timezone
                        published_at = published_at.replace(tzinfo=timezone.utc)
                    elif date_threshold.tzinfo is None and published_at.tzinfo is not None:
                        # date_threshold is naive, published_at is timezone-aware
                        # Convert published_at to naive UTC
                        published_at = published_at.replace(tzinfo=None)
                    
                    if published_at < date_threshold:
                        continue
                article['similarity_score'] = float(similarity_score)
                results.append(article)
            if len(results) >= top_k:
                break
        return results

    def update_user_embedding(self, email_address: str) -> List[float]:
        """
        Generate an embedding for a user based on their preferences in the database.
        Args:
            email_address: The user's email address.
        Returns:
            Embedding vector as a list of floats.
        """
        # Fetch user preferences from the database
        prefs = self.db_service.get_user_preferences(email_address)
        
        if not prefs:
            raise ValueError(f"No user preferences found for {email_address}")
        categories = prefs.get('enabled_categories', [])
        user_keywords = prefs.get('keywords', [])
        # Combine keywords and categories into a single text string
        text_parts = []
        if user_keywords:
            text_parts.append("Keywords: " + ", ".join(user_keywords))
        if categories:
            text_parts.append("Categories: " + ", ".join(categories))
        user_text = " | ".join(text_parts)
        if not user_text.strip():
            # raise warning but no error and return None
            logger.warning("No user keywords or categories provided for embedding.")
            return None

        embedding = self.get_embedding(user_text)

        # Store or update the user embedding in the database
        self.db_service.store_user_embedding(email_address, embedding)
        return embedding
    
    def get_user_embedding(self, email_address: str) -> List[float]:
        return self.db_service.get_user_embedding(email_address)

def main():
    """Example usage"""
    # Configuration
    DB_PATH = "your_database.db"  # Replace with your database path
    OPENAI_API_KEY = "your_openai_api_key"  # Replace with your API key
    
    # Initialize clusterer
    clusterer = ArticleClusterer(DB_PATH, OPENAI_API_KEY)
        
    # Generate embeddings for all articles
    logger.info("Generating embeddings...")
    clusterer.generate_embeddings(batch_size=5, delay=1.0)
    
    # Perform clustering
    logger.info("Performing clustering...")
    run_id = clusterer.perform_clustering(n_clusters=15)
    
    # Analyze results
    logger.info("Analyzing clusters...")
    analysis = clusterer.analyze_clusters(run_id)
    
    print(f"\nClustering Results (Run ID: {run_id})")
    print(f"Total clusters: {analysis['total_clusters']}")
    print(f"Total articles: {analysis['total_articles']}")
    print(f"Average cluster size: {analysis['avg_cluster_size']:.1f}")
    
    print("\nCluster Details:")
    for cluster in analysis['cluster_details'][:10]:  # Show top 10 clusters
        print(f"Cluster {cluster['cluster_id']}: {cluster['article_count']} articles")
        print(f"  Categories: {cluster['categories']}")
        print(f"  Sample titles: {cluster['sample_titles']}")
        print()
    
    # Example: Find similar articles
    if analysis['total_articles'] > 0:
        sample_article_id = 1  # Replace with actual article ID
        try:
            similar = clusterer.get_similar_articles(sample_article_id, None, top_k=3)
            print(f"\nArticles similar to ID {sample_article_id}:")
            for article in similar:
                print(f"- {article['title']} (similarity: {article['similarity_score']:.3f})")
        except ValueError as e:
            print(f"Could not find similar articles: {e}")

if __name__ == "__main__":
    main()