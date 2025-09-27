"""
Email notification system for database sanity check failures.

This module provides email alerting functionality when database
sanity checks detect critical issues or failures.
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any, Optional

from components.notifier import EmailNotifier
from dotenv import load_dotenv


class SanityCheckEmailNotifier:
    """Handles email notifications for sanity check failures."""

    def __init__(self):
        """Initialize the email notifier."""
        load_dotenv()
        self.logger = logging.getLogger(__name__)
        self.notifier = EmailNotifier()
        self.admin_email = os.getenv('ADMIN_EMAIL', 'matheusbitaraesdenovaes@gmail.com')
        self.daily_scribe_sender_email = os.getenv('EMAIL_FROM_ADMIN', 'admin@dailyscribe.news')

    def should_send_alert(self, results: Dict[str, Any]) -> bool:
        """
        Determine if an email alert should be sent based on check results.
        
        Args:
            results: Results from DatabaseSanityChecker.run_checks()
            
        Returns:
            True if alert should be sent, False otherwise
        """
        if not results.get('success', False):
            return True  # Always alert on system errors
        
        summary = results.get('summary', {})
        
        # Send alert if critical issues or errors detected
        if summary.get('critical', 0) > 0 or summary.get('errors', 0) > 0:
            return True
        
        # Optionally send alert for warnings (uncomment if desired)
        # if summary.get('warnings', 0) > 0:
        #     return True
        
        return False

    def _format_severity_for_email(self, severity: str) -> str:
        """Format severity for email display."""
        severity_emojis = {
            'CRITICAL': '🔴',
            'WARNING': '⚠️',
            'ERROR': '❌',
            'INFO': 'ℹ️',
            'OK': '✅'
        }
        emoji = severity_emojis.get(severity.upper(), '❓')
        return f"{emoji} {severity}"

    def _generate_alert_subject(self, results: Dict[str, Any]) -> str:
        """
        Generate email subject line based on check results.
        
        Args:
            results: Results from sanity checks
            
        Returns:
            Email subject line
        """
        if not results.get('success', False):
            return "🚨 Daily Scribe Database Health Check - SYSTEM ERROR"
        
        summary = results.get('summary', {})
        critical_count = summary.get('critical', 0)
        error_count = summary.get('errors', 0)
        warning_count = summary.get('warnings', 0)
        
        if critical_count > 0:
            return f"🚨 Daily Scribe Database Health Check - {critical_count} CRITICAL Issues"
        elif error_count > 0:
            return f"🚨 Daily Scribe Database Health Check - {error_count} ERRORS"
        elif warning_count > 0:
            return f"⚠️ Daily Scribe Database Health Check - {warning_count} Warnings"
        else:
            return "✅ Daily Scribe Database Health Check - All Good"

    def _generate_alert_body(self, results: Dict[str, Any]) -> str:
        """
        Generate email body content based on check results.
        
        Args:
            results: Results from sanity checks
            
        Returns:
            Email body content
        """
        timestamp = results.get('timestamp', 'Unknown')
        database_path = results.get('database_path', 'Unknown')
        
        # Start with header
        body_lines = [
            "Daily Scribe Database Health Check Alert",
            "=" * 50,
            f"Timestamp: {timestamp}",
            f"Database: {database_path}",
            ""
        ]
        
        # Handle system errors
        if not results.get('success', False):
            error = results.get('error', 'Unknown error occurred')
            body_lines.extend([
                "❌ SYSTEM ERROR:",
                f"   {error}",
                "",
                "The database health check system encountered an error and",
                "could not complete the checks. Please investigate immediately.",
                ""
            ])
            return "\n".join(body_lines)
        
        # Summary section
        summary = results.get('summary', {})
        body_lines.extend([
            "SUMMARY:",
            f"  Total Checks: {summary.get('total_checks', 0)}",
            f"  ✅ Passed: {summary.get('passed', 0)}",
            f"  ⚠️  Warnings: {summary.get('warnings', 0)}",
            f"  🔴 Critical: {summary.get('critical', 0)}",
            f"  ❌ Errors: {summary.get('errors', 0)}",
            f"  ℹ️  Info: {summary.get('info', 0)}",
            ""
        ])
        
        # Details for critical issues and errors
        critical_checks = []
        error_checks = []
        warning_checks = []
        
        for check in results.get('checks', []):
            status = check.get('status', '').upper()
            if status == 'CRITICAL':
                critical_checks.append(check)
            elif status == 'ERROR':
                error_checks.append(check)
            elif status == 'WARNING':
                warning_checks.append(check)
        
        # Critical issues section
        if critical_checks:
            body_lines.extend([
                "🔴 CRITICAL ISSUES (IMMEDIATE ACTION REQUIRED):",
                "-" * 50
            ])
            for check in critical_checks:
                body_lines.extend([
                    f"• {check['check_name']}",
                    f"  Description: {check.get('description', 'No description')}",
                    f"  Results: {len(check.get('results', []))} rows returned"
                ])
                
                # Show first few results for critical issues
                for i, result in enumerate(check.get('results', [])[:3]):
                    body_lines.append(f"    Row {i+1}: {dict(result)}")
                
                if len(check.get('results', [])) > 3:
                    body_lines.append(f"    ... and {len(check['results']) - 3} more rows")
                
                body_lines.append("")
        
        # Error section
        if error_checks:
            body_lines.extend([
                "❌ SYSTEM ERRORS:",
                "-" * 50
            ])
            for check in error_checks:
                body_lines.extend([
                    f"• {check['check_name']}",
                    f"  Error: {check.get('error', 'Unknown error')}",
                    ""
                ])
        
        # Warning section (only if no critical issues)
        if warning_checks and not critical_checks:
            body_lines.extend([
                "⚠️  WARNINGS (Review Recommended):",
                "-" * 50
            ])
            for check in warning_checks:
                body_lines.extend([
                    f"• {check['check_name']}",
                    f"  Description: {check.get('description', 'No description')}",
                    f"  Results: {len(check.get('results', []))} rows returned",
                    ""
                ])
        
        # Add action recommendations
        if critical_checks or error_checks:
            body_lines.extend([
                "RECOMMENDED ACTIONS:",
                "-" * 20,
                "1. Check the Daily Scribe application logs for errors",
                "2. Verify RSS processing and summarization pipelines are running",
                "3. Check database connectivity and disk space",
                "4. Review recent system changes or deployments",
                "5. Run manual diagnostics: ./check_database.sh -v",
                ""
            ])
        
        # Footer
        body_lines.extend([
            "This is an automated alert from the Daily Scribe monitoring system.",
            f"For more details, run: python3 src/main.py --sanity-check --verbose",
            "",
            "Daily Scribe Database Health Monitor"
        ])
        
        return "\n".join(body_lines)

    def send_alert(self, results: Dict[str, Any], recipient: Optional[str] = None) -> bool:
        """
        Send email alert based on sanity check results.
        
        Args:
            results: Results from DatabaseSanityChecker.run_checks()
            recipient: Email recipient (uses admin email if None)
            
        Returns:
            True if email sent successfully, False otherwise
        """
        try:
            if not self.should_send_alert(results):
                self.logger.debug("No alert needed - checks passed")
                return True
            
            recipient = recipient or self.admin_email
            subject = self._generate_alert_subject(results)
            body = self._generate_alert_body(results)
            
            # Send email using the email service
            success = self.notifier.send_email(
                subject=subject,
                html_content=body,
                recipient_email=recipient,
                sender_email=self.daily_scribe_sender_email
            )
            
            if success:
                self.logger.info(f"Sanity check alert sent to {recipient}")
                return True
            else:
                self.logger.error(f"Failed to send sanity check alert to {recipient}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending sanity check alert: {e}")
            return False

    def test_alert_system(self, recipient: Optional[str] = None) -> bool:
        """
        Send a test alert to verify the email notification system is working.
        
        Args:
            recipient: Email recipient (uses admin email if None)
            
        Returns:
            True if test email sent successfully, False otherwise
        """
        try:
            recipient = recipient or self.admin_email
            
            # Create a mock critical result for testing
            test_results = {
                'success': True,
                'timestamp': datetime.utcnow().isoformat() + 'Z',
                'database_path': 'test_database.db',
                'checks': [{
                    'check_name': 'TEST: Email Alert System',
                    'description': 'This is a test alert to verify the notification system is working',
                    'status': 'CRITICAL',
                    'results': [{'test_issue': 'Email system test', 'severity': 'CRITICAL'}],
                    'query_count': 1
                }],
                'summary': {
                    'total_checks': 1,
                    'passed': 0,
                    'warnings': 0,
                    'critical': 1,
                    'errors': 0,
                    'info': 0
                }
            }
            
            subject = "🧪 Daily Scribe Health Check - TEST ALERT"
            body = f"""This is a TEST alert from the Daily Scribe database health monitoring system.

If you received this email, the alert system is working correctly.

Test Details:
- Timestamp: {test_results['timestamp']}
- System: Daily Scribe Database Health Monitor
- Alert Type: Test Alert

This test was initiated manually to verify email notifications are functioning.

Daily Scribe Database Health Monitor"""
            success = self.notifier.send_email(
                subject=subject,
                html_content=body,
                recipient_email=recipient,
                sender_email=self.daily_scribe_sender_email
            )
            
            if success:
                self.logger.info(f"Test alert sent successfully to {recipient}")
                return True
            else:
                self.logger.error(f"Failed to send test alert to {recipient}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error sending test alert: {e}")
            return False