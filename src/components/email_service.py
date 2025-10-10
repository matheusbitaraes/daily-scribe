"""
Email service for Daily Scribe application.

This module handles email generation with preference configuration tokens
and secure button integration for user preference management.
"""

import logging
import os
from typing import Optional, Dict, Any
from urllib.parse import urlencode

from .database import DatabaseService
from .security.token_manager import SecureTokenManager
from .digest_builder import DigestBuilder
from utils.html_minifier import minify_html


MAX_EMAIL_HTML_BYTES = int(os.getenv("MAX_EMAIL_HTML_BYTES", 95_000))

logger = logging.getLogger(__name__)


class EmailService:
    """Service for generating emails with preference configuration capabilities."""
    
    def __init__(self, db_service: Optional[DatabaseService] = None):
        """
        Initialize the email service.
        
        Args:
            db_service: Database service instance (optional, creates new if None)
        """
        self.db_service = db_service or DatabaseService()
        self.token_manager = SecureTokenManager(self.db_service)
        self.base_url = os.getenv("FRONTEND_URL")
    
    def generate_preference_token(
        self,
        email_address: str,
        user_agent: str = "Email Client",
        ip_address: str = "unknown"
    ) -> Optional[str]:
        """
        Generate a secure token for preference access.
        
        Args:
            email_address: User's email address
            user_agent: Client user agent (defaults to "Email Client")
            ip_address: Client IP address (defaults to "unknown")
            
        Returns:
            Secure token string if successful, None otherwise
        """
        try:
            # Ensure user preferences exist
            user_prefs = self.db_service.get_user_preferences_by_email(email_address)
            if not user_prefs:
                # Create default preferences for new user
                prefs_id = self.db_service.add_user_preferences(
                    email_address=email_address,
                    enabled_sources=[],
                    enabled_categories=[],
                    keywords=[],
                    max_news_per_category=10
                )
                if not prefs_id:
                    logger.error(f"Failed to create default preferences for {email_address}")
                    return None
                logger.info(f"Created default preferences for new user: {email_address}")
            
            # Generate token
            token = self.token_manager.create_preference_token(
                user_email=email_address,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            if token:
                logger.info(f"Generated preference token for {email_address}")
                return token
            else:
                logger.error(f"Failed to generate preference token for {email_address}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating preference token for {email_address}: {e}")
            return None

    def generate_unsubscribe_token(
        self,
        email_address: str,
        user_agent: str = "Email Client",
        ip_address: str = "unknown"
    ) -> Optional[str]:
        """
        Generate a secure token for unsubscribe access.
        
        Args:
            email_address: User's email address
            user_agent: Client user agent (defaults to "Email Client")
            ip_address: Client IP address (defaults to "unknown")
            
        Returns:
            Secure token string if successful, None otherwise
        """
        try:
            # Generate token
            token = self.token_manager.create_unsubscribe_token(
                user_email=email_address,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            if token:
                logger.info(f"Generated unsubscribe token for {email_address}")
                return token
            else:
                logger.error(f"Failed to generate unsubscribe token for {email_address}")
                return None
                
        except Exception as e:
            logger.error(f"Error generating unsubscribe token for {email_address}: {e}")
            return None
    
    def build_unsubscribe_link_html(
        self,
        token: str,
        link_text: str = "Cancelar inscrição"
    ) -> str:
        """
        Build HTML for the unsubscribe link.
        
        Args:
            token: Secure unsubscribe token
            link_text: Text to display for the link
            
        Returns:
            HTML string for the unsubscribe link
        """
        # Build the unsubscribe URL with token
        unsubscribe_url = f"{self.base_url}/unsubscribe/{token}"
        
        # Create simple text link that works across email clients
        link_html = f"""
        <div style="margin: 8px 0; text-align: center; font-size: 11px; color: #666;">
            <a href="{unsubscribe_url}" 
               target="_blank" 
               rel="noopener"
               style="color: #999; text-decoration: underline; font-size: 11px;">
                {link_text}
            </a>
        </div>
        """
        
        return link_html
    
    def build_digest_with_preferences(
        self,
        clustered_summaries: list,
        email_address: str,
        user_agent: str = "Email Client",
        ip_address: str = "unknown",
    ) -> Dict[str, Any]:
        """
        Build a complete email digest with preference configuration button.
        
        Args:
            clustered_summaries: List of article clusters for the digest
            email_address: Recipient's email address
            user_agent: Client user agent
            ip_address: Client IP address
            
        Returns:
            Dict containing html_content, preference_token, and metadata
        """
        try:
            # Generate preference token
            preference_token = self.generate_preference_token(
                email_address=email_address,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Generate unsubscribe token
            unsubscribe_token = self.generate_unsubscribe_token(
                email_address=email_address,
                user_agent=user_agent,
                ip_address=ip_address
            )
            
            # Build unsubscribe link HTML
            if unsubscribe_token:
                unsubscribe_link_html = self.build_unsubscribe_link_html(
                    token=unsubscribe_token,
                )
            else:
                logger.warning(f"Failed to generate unsubscribe token for {email_address}, building digest without unsubscribe link")
                unsubscribe_link_html = ""
            
            # Build the main digest HTML with preference button and unsubscribe link included
            digest_builder = DigestBuilder()

            digest_html = digest_builder.build_html_digest(
                clustered_summaries=clustered_summaries,
                preference_token=preference_token if preference_token else "",
                unsubscribe_link_html=unsubscribe_link_html if unsubscribe_link_html else "",
                max_clusters=20,
                base_url=self.base_url
            )
            original_length = len(digest_html.encode("utf-8"))
            digest_html = minify_html(digest_html)
            minified_length = len(digest_html.encode("utf-8"))

            if minified_length >= MAX_EMAIL_HTML_BYTES:
                logger.warning(
                    "Digest HTML length after minification is %s bytes (threshold=%s). Original was %s bytes."
                    " Consider reducing content to avoid email clipping.",
                    minified_length,
                    MAX_EMAIL_HTML_BYTES,
                    original_length
                )
            else:
                logger.info(
                    "Digest HTML minified successfully: original=%s bytes, minified=%s bytes (threshold=%s)",
                    original_length,
                    minified_length,
                    MAX_EMAIL_HTML_BYTES,
                )
            
            return {
                "html_content": digest_html,
                "preference_token": preference_token,
                "unsubscribe_token": unsubscribe_token,
                "email_address": email_address,
                "has_preference_button": preference_token is not None,
                "has_unsubscribe_link": unsubscribe_token is not None,
                "metadata": {
                    "clusters_count": len(clustered_summaries),
                    "articles_count": sum(len(cluster) for cluster in clustered_summaries),
                    "preference_url": f"{self.base_url}/preferences/{preference_token}" if preference_token else None,
                    "unsubscribe_url": f"{self.base_url}/unsubscribe/{unsubscribe_token}" if unsubscribe_token else None
                }
            }
            
        except Exception as e:
            logger.error(f"Error building digest with preferences for {email_address}: {e}")
            # Fallback to basic digest without preference button
            digest_builder = DigestBuilder()
            fallback_html = digest_builder.build_html_digest(
                clustered_summaries=clustered_summaries,
                max_clusters=20,
                base_url=self.base_url
            )

            minified_fallback = minify_html(fallback_html)
            fb_length = len(minified_fallback.encode("utf-8"))
            if fb_length >= MAX_EMAIL_HTML_BYTES:
                logger.warning(
                    "Fallback digest HTML length after minification is %s bytes (threshold=%s).",
                    fb_length,
                    MAX_EMAIL_HTML_BYTES,
                )
            return {
                "html_content": minified_fallback,
                "preference_token": None,
                "unsubscribe_token": None,
                "email_address": email_address,
                "has_preference_button": False,
                "has_unsubscribe_link": False,
                "metadata": {
                    "clusters_count": len(clustered_summaries),
                    "articles_count": sum(len(cluster) for cluster in clustered_summaries),
                    "preference_url": None,
                    "unsubscribe_url": None,
                    "error": str(e)
                }
            }
