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
        if article.get('title'):
            parts.append(f"Title: {article['title']}")
        if article.get('summary'):
            parts.append(f"Summary: {article['summary']}")
        if article.get('category'):
            parts.append(f"Category: {article['category']}")
        if article.get('keywords'):
            parts.append(f"Keywords: {article['keywords']}")
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

    def get_all_embeddings(self) -> Tuple[np.ndarray, List[int]]:
        return self.db_service.get_all_article_embeddings()

    def perform_clustering(self, n_clusters: int = 10, algorithm: str = 'kmeans') -> str:
        logger.info(f"Starting clustering with {n_clusters} clusters using {algorithm}")
        embeddings, article_ids = self.get_all_embeddings()
        if len(embeddings) == 0:
            raise ValueError("No embeddings found. Run generate_embeddings() first.")
        logger.info(f"Clustering {len(embeddings)} articles")
        if algorithm == 'kmeans':
            clusterer = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
            cluster_labels = clusterer.fit_predict(embeddings)
            cluster_centers = clusterer.cluster_centers_
            similarity_scores = []
            for i, embedding in enumerate(embeddings):
                cluster_id = cluster_labels[i]
                similarity = -np.linalg.norm(embedding - cluster_centers[cluster_id])
                similarity_scores.append(similarity)
        else:
            raise ValueError(f"Algorithm {algorithm} not implemented yet")
        run_id = f"clustering_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.db_service.store_article_clusters(article_ids, cluster_labels, similarity_scores, run_id)
        logger.info(f"Clustering complete. Run ID: {run_id}")
        return run_id

    def analyze_clusters(self, run_id: str) -> Dict:
        return self.db_service.analyze_clusters(run_id)

    def get_similar_articles(self, article_id: int, top_k: int = 5, similarity_threshold: float = 0.65) -> List[Dict]:
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
                article['similarity_score'] = float(similarity_score)
                results.append(article)
            if len(results) >= top_k:
                break
        return results

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
            similar = clusterer.get_similar_articles(sample_article_id, top_k=3)
            print(f"\nArticles similar to ID {sample_article_id}:")
            for article in similar:
                print(f"- {article['title']} (similarity: {article['similarity_score']:.3f})")
        except ValueError as e:
            print(f"Could not find similar articles: {e}")

if __name__ == "__main__":
    main()