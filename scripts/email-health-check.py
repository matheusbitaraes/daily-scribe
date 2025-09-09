#!/usr/bin/env python3
"""
Email Health Check Script for Daily Scribe

This script tests email connectivity and configuration for health monitoring.
"""

import os
import sys
import json
import logging
from datetime import datetime

# Add the source directory to Python path
sys.path.insert(0, '/app/src')
sys.path.insert(0, 'src')  # For local development

try:
    from components.config import load_config
    from components.notifier import EmailNotifier
except ImportError as e:
    print(f"ERROR: Failed to import required modules: {e}")
    sys.exit(1)


def test_email_connectivity():
    """
    Test email service connectivity and configuration.
    
    Returns:
        dict: Health check results
    """
    health_status = {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "email_service": "aws_ses",
        "checks": {}
    }
    
    try:
        # Test 1: Configuration Loading
        try:
            config = load_config()
            health_status["checks"]["config_loading"] = {
                "status": "pass",
                "message": "Configuration loaded successfully"
            }
        except Exception as e:
            health_status["checks"]["config_loading"] = {
                "status": "fail",
                "message": f"Failed to load configuration: {str(e)}"
            }
            health_status["status"] = "unhealthy"
            return health_status
        
        # Test 2: Email Configuration Validation
        try:
            email_config = config.email
            required_fields = ['provider', 'smtp_server', 'smtp_port', 'username', 'password']
            
            for field in required_fields:
                if not hasattr(email_config, field) or not getattr(email_config, field):
                    raise ValueError(f"Missing required email configuration: {field}")
            
            health_status["checks"]["email_config"] = {
                "status": "pass",
                "message": f"Email configuration valid for provider: {email_config.provider}",
                "provider": email_config.provider,
                "smtp_server": email_config.smtp_server,
                "smtp_port": email_config.smtp_port
            }
        except Exception as e:
            health_status["checks"]["email_config"] = {
                "status": "fail",
                "message": f"Email configuration validation failed: {str(e)}"
            }
            health_status["status"] = "unhealthy"
        
        # Test 3: SMTP Connection Test
        try:
            import smtplib
            with smtplib.SMTP(email_config.smtp_server, email_config.smtp_port, timeout=10) as server:
                server.starttls()
                server.login(email_config.username, email_config.password)
            
            health_status["checks"]["smtp_connection"] = {
                "status": "pass",
                "message": "SMTP connection and authentication successful"
            }
        except Exception as e:
            health_status["checks"]["smtp_connection"] = {
                "status": "fail",
                "message": f"SMTP connection failed: {str(e)}"
            }
            health_status["status"] = "unhealthy"
        
        # Test 4: Notifier Initialization
        try:
            notifier = EmailNotifier(email_config)
            health_status["checks"]["notifier_init"] = {
                "status": "pass",
                "message": "Email notifier initialized successfully"
            }
        except Exception as e:
            health_status["checks"]["notifier_init"] = {
                "status": "fail",
                "message": f"Failed to initialize email notifier: {str(e)}"
            }
            health_status["status"] = "unhealthy"
        
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    return health_status


def main():
    """Main health check function."""
    # Configure logging
    logging.basicConfig(
        level=logging.WARNING,  # Reduce noise for health checks
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
    
    # Suppress urllib3 warnings for health checks
    import urllib3
    urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    # Run health check
    health_status = test_email_connectivity()
    
    # Output results
    if len(sys.argv) > 1 and sys.argv[1] == "--json":
        print(json.dumps(health_status, indent=2))
    else:
        status_symbol = "✅" if health_status["status"] == "healthy" else "❌"
        print(f"{status_symbol} Email Service Health: {health_status['status'].upper()}")
        
        for check_name, check_result in health_status["checks"].items():
            check_symbol = "✅" if check_result["status"] == "pass" else "❌"
            print(f"  {check_symbol} {check_name}: {check_result['message']}")
        
        if "error" in health_status:
            print(f"❌ Error: {health_status['error']}")
    
    # Exit with appropriate code
    sys.exit(0 if health_status["status"] == "healthy" else 1)


if __name__ == "__main__":
    main()
