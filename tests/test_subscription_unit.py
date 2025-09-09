"""
Unit tests for subscription functionality.
"""

import unittest
import tempfile
import os
import sqlite3
from datetime import datetime, timedelta
import sys

# Add src to path
sys.path.insert(0, 'src')

from components.database import DatabaseService
from components.subscription_service import SubscriptionService
from utils.migrations import DatabaseMigrator


class TestSubscriptionService(unittest.TestCase):
    """Test cases for subscription service."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database with migrations
        migrator = DatabaseMigrator(self.db_path)
        migrator.run_all_migrations()
        
        self.db_service = DatabaseService(self.db_path)
        self.subscription_service = SubscriptionService(self.db_service)

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_create_subscription_request_success(self):
        """Test successful subscription request creation."""
        email = "test@example.com"
        result = self.subscription_service.create_subscription_request(email)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['email'], email)
        self.assertIn('message', result)
        
        # Verify record in database
        self.assertTrue(self.db_service.is_email_pending_verification(email))

    def test_create_subscription_request_duplicate_pending(self):
        """Test duplicate subscription request with pending verification."""
        email = "test@example.com"
        
        # Create first subscription
        result1 = self.subscription_service.create_subscription_request(email)
        self.assertTrue(result1['success'])
        
        # Try to create duplicate
        result2 = self.subscription_service.create_subscription_request(email)
        self.assertFalse(result2['success'])
        self.assertEqual(result2['error'], 'verification_pending')

    def test_create_subscription_request_already_subscribed(self):
        """Test subscription request for already subscribed email."""
        email = "test@example.com"
        
        # Manually add user to subscribed users
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, is_active) VALUES (?, 1)", (email,))
            conn.commit()
        
        result = self.subscription_service.create_subscription_request(email)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'email_already_subscribed')

    def test_verify_email_success(self):
        """Test successful email verification."""
        email = "test@example.com"
        
        # Create subscription request
        result = self.subscription_service.create_subscription_request(email)
        self.assertTrue(result['success'])
        
        # Get the verification token
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT verification_token FROM pending_subscriptions WHERE email = ?", (email,))
            token_row = cursor.fetchone()
            self.assertIsNotNone(token_row)
            token = token_row[0]
        
        # Verify email
        verify_result = self.subscription_service.verify_email(token)
        self.assertTrue(verify_result['success'])
        self.assertEqual(verify_result['email'], email)
        
        # Check user was moved to users table
        self.assertTrue(self.db_service.is_email_subscribed(email))
        self.assertFalse(self.db_service.is_email_pending_verification(email))

    def test_verify_email_invalid_token(self):
        """Test email verification with invalid token."""
        result = self.subscription_service.verify_email("invalid-token-123")
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'invalid_token')

    def test_verify_email_expired_token(self):
        """Test email verification with expired token."""
        email = "test@example.com"
        token = "expired-token-123"
        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        
        # Manually insert expired token
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO pending_subscriptions (email, verification_token, expires_at)
                VALUES (?, ?, ?)
            """, (email, token, expired_time))
            conn.commit()
        
        result = self.subscription_service.verify_email(token)
        self.assertFalse(result['success'])
        self.assertEqual(result['error'], 'invalid_token')

    def test_generate_verification_token(self):
        """Test verification token generation."""
        token1 = self.subscription_service.generate_verification_token()
        token2 = self.subscription_service.generate_verification_token()
        
        # Tokens should be different
        self.assertNotEqual(token1, token2)
        
        # Tokens should be reasonable length
        self.assertGreater(len(token1), 20)
        self.assertGreater(len(token2), 20)


class TestDatabaseService(unittest.TestCase):
    """Test cases for database service subscription methods."""

    def setUp(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize database with migrations
        migrator = DatabaseMigrator(self.db_path)
        migrator.run_all_migrations()
        
        self.db_service = DatabaseService(self.db_path)

    def tearDown(self):
        """Clean up test database."""
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_create_pending_subscription(self):
        """Test creating pending subscription."""
        email = "test@example.com"
        token = "test-token-123"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        result = self.db_service.create_pending_subscription(email, token, expires_at)
        self.assertTrue(result)
        
        # Verify in database
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM pending_subscriptions WHERE email = ?", (email,))
            row = cursor.fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row[1], email)  # email column
            self.assertEqual(row[2], token)  # token column

    def test_create_pending_subscription_duplicate_email(self):
        """Test creating pending subscription with duplicate email."""
        email = "test@example.com"
        token1 = "test-token-123"
        token2 = "test-token-456"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # First subscription should succeed
        result1 = self.db_service.create_pending_subscription(email, token1, expires_at)
        self.assertTrue(result1)
        
        # Second subscription with same email should fail
        result2 = self.db_service.create_pending_subscription(email, token2, expires_at)
        self.assertFalse(result2)

    def test_is_email_subscribed(self):
        """Test checking if email is subscribed."""
        email = "test@example.com"
        
        # Initially not subscribed
        self.assertFalse(self.db_service.is_email_subscribed(email))
        
        # Add user
        with self.db_service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO users (email, is_active) VALUES (?, 1)", (email,))
            conn.commit()
        
        # Should be subscribed now
        self.assertTrue(self.db_service.is_email_subscribed(email))

    def test_is_email_pending_verification(self):
        """Test checking if email is pending verification."""
        email = "test@example.com"
        token = "test-token-123"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Initially not pending
        self.assertFalse(self.db_service.is_email_pending_verification(email))
        
        # Add pending subscription
        self.db_service.create_pending_subscription(email, token, expires_at)
        
        # Should be pending now
        self.assertTrue(self.db_service.is_email_pending_verification(email))

    def test_verify_subscription_token(self):
        """Test verifying subscription token."""
        email = "test@example.com"
        token = "test-token-123"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Add pending subscription
        self.db_service.create_pending_subscription(email, token, expires_at)
        
        # Verify token
        result_email = self.db_service.verify_subscription_token(token)
        self.assertEqual(result_email, email)
        
        # Test invalid token
        invalid_result = self.db_service.verify_subscription_token("invalid-token")
        self.assertIsNone(invalid_result)

    def test_activate_subscription(self):
        """Test activating subscription."""
        email = "test@example.com"
        token = "test-token-123"
        expires_at = (datetime.utcnow() + timedelta(hours=24)).isoformat()
        
        # Add pending subscription
        self.db_service.create_pending_subscription(email, token, expires_at)
        
        # Activate subscription
        result = self.db_service.activate_subscription(email, token)
        self.assertTrue(result)
        
        # Check user was added and pending was removed
        self.assertTrue(self.db_service.is_email_subscribed(email))
        self.assertFalse(self.db_service.is_email_pending_verification(email))

    def test_cleanup_expired_pending_subscriptions(self):
        """Test cleaning up expired pending subscriptions."""
        email1 = "test1@example.com"
        email2 = "test2@example.com"
        token1 = "token1"
        token2 = "token2"
        
        # Add expired subscription
        expired_time = (datetime.utcnow() - timedelta(hours=1)).isoformat()
        self.db_service.create_pending_subscription(email1, token1, expired_time)
        
        # Add valid subscription
        valid_time = (datetime.utcnow() + timedelta(hours=1)).isoformat()
        self.db_service.create_pending_subscription(email2, token2, valid_time)
        
        # Clean up
        removed_count = self.db_service.cleanup_expired_pending_subscriptions()
        self.assertEqual(removed_count, 1)
        
        # Check only valid subscription remains
        self.assertFalse(self.db_service.is_email_pending_verification(email1))
        self.assertTrue(self.db_service.is_email_pending_verification(email2))


if __name__ == '__main__':
    unittest.main()
