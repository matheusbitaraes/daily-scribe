"""
DigestService for Daily Scribe application.

This module provides reusable digest generation and sending functionality.
Separates the concerns of digest generation from email delivery.
"""

import logging
import time
import uuid
import os
from typing import Optional, Dict, List, Any

from components.database import DatabaseService
from components.article_clusterer import ArticleClusterer
from components.news_curator import NewsCurator
from components.notifier import EmailNotifier
from components.email_service import EmailService

logger = logging.getLogger(__name__)


class DigestService:
    """Service for generating and sending digests."""
    
    def __init__(self):
        self.db_service = DatabaseService()
        self.email_service = EmailService()
        self.news_curator = NewsCurator()
    
    def generate_digest_for_user(
        self,
        email_address: str,
    ) -> Dict:
        """
        Generate a digest for a specific user using their preferences.
        
        Args:
            email_address: User's email address
            
        Returns:
            Dict containing html_content, metadata, and clustered articles for sending
        """
        logger.info(f"Generating digest for user {email_address}")
        
        # Update user embedding before curation if there isnt one
        # clusterer = ArticleClusterer()
        # clusterer.update_user_embedding(email_address)
        
        # Use curator to get articles based on user preferences
        clustered_articles = self.news_curator.curate_and_cluster(email_address)

        if not clustered_articles:
            return {
                "success": False,
                "html_content": "",
                "metadata": {
                    "email_address": email_address,
                    "article_count": 0,
                    "clusters": 0,
                    "method": "standard"
                },
                "clustered_articles": [],
                "ranking_details": [],
                "message": "No curated articles found for user after applying preferences."
            }
        
        # Generate HTML digest with preference button
        digest_result = self.email_service.build_digest_with_preferences(
            clustered_summaries=clustered_articles,
            email_address=email_address
        )
        
        # Extract HTML content from the result
        if isinstance(digest_result, dict):
            html_content = digest_result.get("html_content", "")
            preference_metadata = digest_result.get("metadata", {})
        else:
            # Fallback for string result
            html_content = digest_result
            preference_metadata = {}
        
        # Count total articles
        total_articles = sum(len(cluster) for cluster in clustered_articles)
        
        metadata = {
            "email_address": email_address,
            "article_count": total_articles,
            "clusters": len(clustered_articles),
            "method": "standard",
            "generated_at": time.strftime('%Y-%m-%d %H:%M:%S'),
            "has_preference_button": preference_metadata.get("has_preference_button", False),
            "preference_url": preference_metadata.get("preference_url")
        }
        
        ranking_details = self._build_ranking_details(clustered_articles)

        return {
            "success": True,
            "html_content": html_content,
            "metadata": metadata,
            "clustered_articles": clustered_articles,
            "ranking_details": ranking_details,
            "message": f"Successfully generated user digest with {len(clustered_articles)} clusters from {total_articles} articles."
        }

    def _build_ranking_details(self, clustered_articles: List[List[Dict]]) -> List[Dict[str, Any]]:
        """Build structured ranking breakdown for each cluster."""
        ranking_details: List[Dict[str, Any]] = []

        feature_labels = ["semantic", "recency", "urgency", "impact"]

        for cluster_index, cluster in enumerate(clustered_articles):
            if not cluster:
                continue

            score_components = self.news_curator.calculate_cluster_score_components(cluster)
            if score_components is None:
                continue

            main_article = cluster[0]

            articles_details: List[Dict[str, Any]] = []
            for position, article in enumerate(cluster):
                ltr_features = article.get("ltr_features")
                if isinstance(ltr_features, list) and len(ltr_features) == len(feature_labels):
                    ltr_features_serialized = {
                        label: float(value) if value is not None else None
                        for label, value in zip(feature_labels, ltr_features)
                    }
                else:
                    ltr_features_serialized = ltr_features

                articles_details.append({
                    "position": position,
                    "id": article.get("id"),
                    "title": article.get("title_pt") or article.get("title"),
                    "source": article.get("source_name") or article.get("source"),
                    "category": article.get("category"),
                    "published_at": article.get("published_at"),
                    "urgency_score": float(article.get("urgency_score") or 0.0),
                    "impact_score": float(article.get("impact_score") or 0.0),
                    "user_similarity": float(article.get("user_similarity") or 0.0),
                    "rank_score": float(article.get("rank_score") or 0.0),
                    "ltr_features": ltr_features_serialized,
                    "summary": article.get("summary_pt") or article.get("summary"),
                    "subject": article.get("subject_pt") or article.get("subject"),
                    "url": article.get("url"),
                })

            ranking_details.append({
                "cluster_index": cluster_index,
                "cluster_size": len(cluster),
                "main_article_id": main_article.get("id"),
                "main_article_title": main_article.get("title_pt") or main_article.get("title"),
                "score_components": score_components,
                "articles": articles_details,
            })

        return ranking_details
    
    def send_digest_to_user(
        self,
        email_address: str,
        force: bool = False,
    ) -> Dict:
        """
        Generate and send a digest to a specific user.
        
        Args:
            email_address: User's email address
            force: Whether to force sending even if already sent today
            
        Returns:
            Dict containing success status and details
        """
        logger.info(f"Starting digest generation and sending for {email_address}")
        
        try:
            # Safety switch: check if user has received a digest today
            if not force and self.db_service.has_user_received_digest_today(email_address):
                logger.warning(f"Digest already sent to {email_address} today. Use force=True to override.")
                return {
                    "success": False,
                    "message": f"Digest already sent to {email_address} today. Use force=True to override.",
                    "reason": "already_sent_today"
                }
            
            # Generate the digest
            result = self.generate_digest_for_user(email_address)
            
            if not result["success"]:
                logger.info(f"No curated articles to send to {email_address}")
                return result
            
            # Send the digest via email
            html_digest = result["html_content"]
            clustered_articles = result["clustered_articles"]
            
            # Generate subject with top 3 highest scoring articles
            subject = self._generate_email_subject(clustered_articles)
            
            notifier = EmailNotifier()
            
            email_from_editor = os.getenv("EMAIL_FROM_EDITOR")
            editor_name = os.getenv("EDITOR_NAME", "Editor")
            editor_email = f'"{editor_name}" <{email_from_editor}>'
            notifier.send_digest(html_digest, email_address, editor_email, subject)
            
            # Mark all sent articles in sent_articles table
            digest_id = uuid.uuid4()
            all_sent_articles = [article for cluster in clustered_articles for article in cluster]
            for article in all_sent_articles:
                db_article = self.db_service.get_article_by_url(article['url'])
                if db_article:
                    self.db_service.add_sent_article(db_article['id'], digest_id=digest_id, email_address=email_address)
            
            logger.info(f"Digest generated and sent successfully to {email_address}")
            
            return {
                "success": True,
                "message": f"Digest sent successfully to {email_address}",
                "metadata": result["metadata"],
                "digest_id": str(digest_id),
                "articles_sent": len(all_sent_articles),
                "ranking_details": result.get("ranking_details", [])
            }
            
        except Exception as e:
            logger.error(f"An error occurred during digest sending to {email_address}: {e}")
            return {
                "success": False,
                "message": f"Error sending digest to {email_address}: {str(e)}",
                "reason": "error",
                "error": str(e)
            }
    
    def _generate_email_subject(self, clustered_articles: List[List[Dict]]) -> str:
        """
        Generate email subject using subject_pt from top 3 highest scoring clusters.
        
        Args:
            clustered_articles: List of article clusters
            
        Returns:
            Email subject string
        """
        print("Generating email subject...")

        # Get top 3 clusters with subject_pt from their main article
        top_subjects = []
        MAIN_ARTICLES_NUMBER_FOR_SUBJECT = int(os.getenv("MAIN_ARTICLES_NUMBER_FOR_SUBJECT", 3))
        for cluster in clustered_articles[:MAIN_ARTICLES_NUMBER_FOR_SUBJECT]:
            if cluster:
                main_article = cluster[0]
                subject_pt = main_article.get('subject_pt')
                if subject_pt and subject_pt.strip():
                    top_subjects.append(subject_pt.strip())
        
        # Generate subject
        date_str = time.strftime('%d/%m/%Y')
        
        if top_subjects:
            if len(top_subjects) == 1:
                subject = f"{top_subjects[0]} - {date_str}"
            elif len(top_subjects) == 2:
                subject = f"{top_subjects[0]} • {top_subjects[1]} - {date_str}"
            else:  # 3 or more
                subject = f"{top_subjects[0]} • {top_subjects[1]} • {top_subjects[2]} - {date_str}"
        else:
            # Fallback to original subject if no subject_pt available
            subject = f"Suas Notícias de {date_str}"
        
        return subject