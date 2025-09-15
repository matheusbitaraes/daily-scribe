"""
Subscription service for Daily Scribe application.

This module handles subscription business logic including email verification,
token generation, and email notifications.
"""

import secrets
import logging
from datetime import datetime, timedelta
import os

from components.database import DatabaseService
from components.notifier import EmailNotifier
from components.env_loader import get_jwt_secret_key


class SubscriptionService:
    """Handles subscription management and email verification."""

    def __init__(self, database_service: DatabaseService):
        """
        Initialize the subscription service.
        
        Args:
            database_service: Database service instance
        """

        self.db_service = database_service
        self.email_notifier = EmailNotifier()
        self.logger = logging.getLogger(__name__)
        
        # Get base URL from environment or use default (frontend URL, not API URL)
        self.base_url = os.getenv("FRONTEND_URL")

    def generate_verification_token(self) -> str:
        """
        Generate a secure verification token.
        
        Returns:
            Secure random token string
        """
        # Generate a secure random token
        token = secrets.token_urlsafe(32)
        return token

    def create_subscription_request(self, email: str) -> dict:
        """
        Create a new subscription request.
        
        Args:
            email: User's email address
            
        Returns:
            Dictionary with success status and message
        """
        try:
            # Check if email is already subscribed
            if self.db_service.is_email_subscribed(email):
                return {
                    'success': False,
                    'error': 'email_already_subscribed',
                    'message': 'This email address is already subscribed'
                }
            
            # Check if email has pending verification
            if self.db_service.is_email_pending_verification(email):
                return {
                    'success': False,
                    'error': 'verification_pending',
                    'message': 'A verification email has already been sent. Please check your inbox.'
                }
            
            # Generate verification token
            verification_token = self.generate_verification_token()
            
            # Set expiration time (24 hours from now)
            expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
            
            # Create pending subscription
            success = self.db_service.create_pending_subscription(
                email=email,
                verification_token=verification_token,
                expires_at=expires_at
            )
            
            if not success:
                return {
                    'success': False,
                    'error': 'database_error',
                    'message': 'Failed to create subscription request'
                }

            # Send verification email
            if self.email_notifier:
                try:
                    self._send_verification_email(email, verification_token)
                except Exception as e:
                    self.logger.error(f"Failed to send verification email to {email}: {e}")
                    # Note: We don't fail the request if email sending fails
                    # The user can still be verified manually if needed
            
            return {
                'success': True,
                'message': 'Verification email sent successfully',
                'email': email
            }
            
        except Exception as e:
            self.logger.error(f"Error creating subscription request for {email}: {e}")
            return {
                'success': False,
                'error': 'internal_error',
                'message': 'An unexpected error occurred'
            }

    def verify_email(self, token: str) -> dict:
        """
        Verify an email using the verification token.
        
        Args:
            token: Verification token
            
        Returns:
            Dictionary with verification result
        """
        try:
            # Verify the token and get the email
            email = self.db_service.verify_subscription_token(token)
            
            if not email:
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'Invalid or expired verification token'
                }
            
            # Activate the subscription
            success = self.db_service.activate_subscription(email, token)
            
            if not success:
                return {
                    'success': False,
                    'error': 'activation_failed',
                    'message': 'Failed to activate subscription'
                }
            
            self.logger.info(f"Successfully verified and activated subscription for {email}")
            
            return {
                'success': True,
                'message': 'Email verified successfully',
                'email': email
            }
            
        except Exception as e:
            self.logger.error(f"Error verifying email with token {token}: {e}")
            return {
                'success': False,
                'error': 'internal_error',
                'message': 'An unexpected error occurred during verification'
            }

    def _send_verification_email(self, email: str, token: str) -> None:
        """
        Send verification email to the user.
        
        Args:
            email: User's email address
            token: Verification token
        """
        if not self.email_notifier:
            self.logger.warning("Email notifier not configured, skipping verification email")
            return
        
        verification_url = f"{self.base_url}/verify-email?token={token}"
        
        subject = "Confirm your Daily Scribe subscription"
        
        html_content = f"""
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Bem-vindo ao Daily Scribe</title>
        </head>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #2c3e50;">Bem-vindo ao Daily Scribe!</h2>
                
                <p>Obrigado por se inscrever em nosso resumo diário de notícias. Para completar sua inscrição, por favor clique no botão abaixo para verificar seu endereço de email:</p>
                
                <div style="text-align: center; margin: 30px 0;">
                    <a href="{verification_url}" 
                    style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 5px; display: inline-block; font-weight: bold;">
                        Verificar Meu Email
                    </a>
                </div>
                
                <p>Se o botão não funcionar, você pode copiar e colar este link no seu navegador:</p>
                <p style="background-color: #f8f9fa; padding: 10px; border-radius: 5px; word-break: break-all;">
                    {verification_url}
                </p>
                
                <p><strong>Este link de verificação expirará em 24 horas.</strong></p>
                
                <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
                
                <p style="font-size: 12px; color: #666;">
                    Se você não solicitou esta inscrição, pode ignorar este email com segurança.
                </p>
                
                <p style="font-size: 12px; color: #666;">
                    Atenciosamente,<br>
                    Equipe Daily Scribe
                </p>
            </div>
        </body>
        </html>
        """

        email_from_admin = os.getenv("EMAIL_FROM_ADMIN")
        admin_name = os.getenv("ADMIN_NAME", "Admin")
        admin_email = f'"{admin_name}" <{email_from_admin}>'

        try:
            self.email_notifier.send_digest(html_content, email, admin_email, subject)
            self.logger.info(f"Verification email sent to {email}")
        except Exception as e:
            self.logger.error(f"Failed to send verification email to {email}: {e}")
            raise

    def cleanup_expired_tokens(self) -> int:
        """
        Clean up expired verification tokens.
        
        Returns:
            Number of expired tokens removed
        """
        try:
            return self.db_service.cleanup_expired_pending_subscriptions()
        except Exception as e:
            self.logger.error(f"Error cleaning up expired tokens: {e}")
            return 0

    def process_unsubscribe_request(self, token: str) -> dict:
        """
        Process an unsubscribe request using a secure token.
        
        Args:
            token: Secure unsubscribe token
            
        Returns:
            Dictionary with unsubscribe result
        """
        try:
            # Import here to avoid circular imports
            from components.security.token_manager import SecureTokenManager
            
            # Initialize token manager
            token_manager = SecureTokenManager(self.db_service)
            
            # Validate the unsubscribe token
            validation_result = token_manager.validate_token(
                token=token,
                user_agent="Unsubscribe Request",
                ip_address="unknown"
            )
            
            if not validation_result.is_valid:
                self.logger.warning(f"Invalid unsubscribe token: {validation_result.error_message}")
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': validation_result.error_message or 'Invalid or expired unsubscribe token'
                }
            
            # Verify this is an unsubscribe token (not preference token)
            # We need to check the token directly since validate_token doesn't return purpose
            from components.security.token_manager import SecureTokenManager
            import jwt
            import os
            
            try:
                # Decode the token to check its purpose
                secret_key = get_jwt_secret_key()
                payload = jwt.decode(token, secret_key, algorithms=['HS256'])
                token_purpose = payload.get('purpose')
                
                if token_purpose != 'unsubscribe':
                    self.logger.warning(f"Token is not an unsubscribe token for user {validation_result.user_email}")
                    return {
                        'success': False,
                        'error': 'invalid_token_type',
                        'message': 'Invalid token type for unsubscribe operation'
                    }
            except jwt.DecodeError:
                self.logger.warning(f"Could not decode token for purpose check")
                return {
                    'success': False,
                    'error': 'invalid_token',
                    'message': 'Invalid token format'
                }
            
            user_email = validation_result.user_email
            
            # Check if user is already unsubscribed
            subscription = self.db_service.get_subscription_by_email(user_email)
            if not subscription:
                self.logger.warning(f"No subscription found for {user_email}")
                return {
                    'success': False,
                    'error': 'subscription_not_found',
                    'message': 'No active subscription found for this email address'
                }
            
            if subscription['status'] != 'active':
                self.logger.info(f"User {user_email} is already unsubscribed (status: {subscription['status']})")
                return {
                    'success': True,
                    'message': 'You are already unsubscribed from the newsletter',
                    'email': user_email,
                    'status': 'already_unsubscribed'
                }
            
            # Perform the unsubscription
            success = self.db_service.unsubscribe_user(user_email)
            
            if not success:
                self.logger.error(f"Failed to unsubscribe user {user_email}")
                return {
                    'success': False,
                    'error': 'unsubscribe_failed',
                    'message': 'Failed to process unsubscription request'
                }
            
            # Mark token as used (increment usage count)
            # We need the token_id from the payload for this
            token_id = payload.get('token_id')
            if token_id:
                self.db_service.increment_token_usage(token_id)
            
            self.logger.info(f"Successfully unsubscribed user {user_email}")
            
            return {
                'success': True,
                'message': 'You have been successfully unsubscribed from the newsletter',
                'email': user_email,
                'status': 'unsubscribed',
                'unsubscribed_at': datetime.utcnow().isoformat() + 'Z'
            }
            
        except Exception as e:
            self.logger.error(f"Error processing unsubscribe request with token {token}: {e}")
            return {
                'success': False,
                'error': 'internal_error',
                'message': 'An unexpected error occurred while processing your unsubscribe request'
            }
