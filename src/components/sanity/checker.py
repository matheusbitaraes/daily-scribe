"""
Database sanity checker for Daily Scribe application.

This module contains the DatabaseSanityChecker class that runs comprehensive
health checks on the database and provides detailed reporting functionality.
"""

import json
import logging
import os
import re
import sqlite3
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

from components.database import DatabaseService


class DatabaseSanityChecker:
    """Runs database sanity checks and formats results."""

    def __init__(self, db_path: Optional[str] = None, verbose: bool = False):
        """
        Initialize the sanity checker.
        
        Args:
            db_path: Path to the SQLite database (uses default if None)
            verbose: Whether to show detailed output
        """
        # Use DatabaseService to get the correct path
        if db_path is None:
            db_service = DatabaseService()
            self.db_path = db_service.db_path
        else:
            self.db_path = db_path
            
        self.verbose = verbose
        self.logger = self._setup_logging()
        
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        return logging.getLogger(__name__)

    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with proper configuration."""
        if not os.path.exists(self.db_path):
            raise FileNotFoundError(f"Database file not found: {self.db_path}")
        
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.row_factory = sqlite3.Row  # Enable dict-like access
        return conn

    def _get_sql_checks(self) -> str:
        """Get SQL checks content from the SQL file or return embedded checks."""
        # Try to find SQL file in project root
        project_root = Path(__file__).parent.parent.parent.parent
        sql_file_path = project_root / "database_sanity_checks.sql"
        
        if sql_file_path.exists():
            with open(sql_file_path, 'r') as f:
                return f.read()
        
        # Fallback to embedded SQL checks if file not found
        return self._get_embedded_sql_checks()

    def _get_embedded_sql_checks(self) -> str:
        """Return embedded SQL checks as fallback."""
        return """
-- CHECK 1: Articles without summary/summary_pt but raw_content is null (processed yesterday)
-- This indicates articles that were marked as processed but failed content extraction
SELECT 
    'Articles processed yesterday missing both content and summary' as check_name,
    COUNT(*) as issue_count,
    'CRITICAL' as severity
FROM articles a
LEFT JOIN sources s ON a.source_id = s.id
WHERE DATE(a.processed_at) = DATE('now', '-1 day')
  AND (a.summary IS NULL AND a.summary_pt IS NULL)
  AND a.raw_content IS NULL;

-- CHECK 2: No articles processed in last 5 hours
-- This indicates the RSS processor or content pipeline may be down
SELECT 
    'Articles processed in last 5 hours' as check_name,
    COUNT(*) as article_count,
    CASE 
        WHEN COUNT(*) = 0 THEN 'CRITICAL'
        WHEN COUNT(*) < 10 THEN 'WARNING'
        ELSE 'OK'
    END as severity,
    MAX(processed_at) as last_processed_at
FROM articles 
WHERE processed_at >= datetime('now', '-5 hours');

-- CHECK 3: No articles with summary/summary_pt in last 5 hours  
-- This indicates the NLP/summarization pipeline may be down
SELECT 
    'Articles with summaries in last 5 hours' as check_name,
    COUNT(*) as article_count,
    CASE 
        WHEN COUNT(*) = 0 THEN 'CRITICAL'
        WHEN COUNT(*) < 5 THEN 'WARNING'
        ELSE 'OK'
    END as severity,
    MAX(processed_at) as last_summarized_at
FROM articles 
WHERE processed_at >= datetime('now', '-5 hours')
  AND (summary IS NOT NULL OR summary_pt IS NOT NULL);

-- CHECK 4: System health summary
-- Overall system health dashboard
SELECT 
    'System Health Summary' as dashboard,
    (SELECT COUNT(*) FROM articles WHERE processed_at >= datetime('now', '-1 hour')) as articles_last_hour,
    (SELECT COUNT(*) FROM articles WHERE processed_at >= datetime('now', '-24 hours')) as articles_last_24h,
    (SELECT COUNT(*) FROM articles WHERE (summary IS NOT NULL OR summary_pt IS NOT NULL) AND processed_at >= datetime('now', '-1 hour')) as summarized_last_hour,
    (SELECT COUNT(*) FROM sources) as total_sources,
    (SELECT COUNT(*) FROM rss_feeds WHERE is_enabled = 1) as enabled_feeds,
    (SELECT COUNT(*) FROM user_preferences) as active_users,
    (SELECT MAX(processed_at) FROM articles) as last_article_processed;
"""

    def _parse_sql_content(self, content: str) -> List[Tuple[str, str, List[str]]]:
        """
        Parse SQL content and extract individual checks.
        
        Args:
            content: SQL content string
            
        Returns:
            List of tuples: (check_name, description, sql_queries)
        """
        checks = []
        current_check = None
        current_description = ""
        current_queries = []
        
        lines = content.split('\n')
        i = 0
        
        while i < len(lines):
            line = lines[i].strip()
            
            # Look for check headers (-- CHECK N:)
            check_match = re.match(r'^-- CHECK (\d+):\s*(.+)', line)
            if check_match:
                # Save previous check if exists
                if current_check and current_queries:
                    checks.append((current_check, current_description, current_queries))
                
                # Start new check
                check_num = check_match.group(1)
                current_check = f"CHECK {check_num}: {check_match.group(2)}"
                current_description = ""
                current_queries = []
                
            # Look for description lines
            elif line.startswith('-- ') and not line.startswith('-- =') and current_check:
                desc_line = line[3:].strip()
                if desc_line and not desc_line.startswith('CHECK'):
                    current_description += desc_line + " "
            
            # Look for SQL queries
            elif line and not line.startswith('--') and current_check:
                # Collect multi-line SQL query
                sql_lines = [line]
                i += 1
                while i < len(lines):
                    next_line = lines[i].strip()
                    if next_line.startswith('--') or (next_line == '' and len(sql_lines) > 1):
                        break
                    if next_line:
                        sql_lines.append(next_line)
                    i += 1
                i -= 1  # Adjust for outer loop increment
                
                if sql_lines and any(sql_lines):
                    sql_query = ' '.join(sql_lines).strip()
                    if sql_query.endswith(';'):
                        current_queries.append(sql_query)
            
            i += 1
        
        # Don't forget the last check
        if current_check and current_queries:
            checks.append((current_check, current_description.strip(), current_queries))
        
        return checks

    def _execute_query(self, query: str) -> Tuple[List[Dict], Optional[str]]:
        """
        Execute a SQL query and return results.
        
        Args:
            query: SQL query to execute
            
        Returns:
            Tuple of (results, error_message)
        """
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(query)
                
                # Convert rows to dictionaries
                rows = cursor.fetchall()
                results = [dict(row) for row in rows]
                
                return results, None
                
        except sqlite3.Error as e:
            return [], f"SQL Error: {str(e)}"
        except Exception as e:
            return [], f"Unexpected error: {str(e)}"

    def _format_severity(self, severity: str) -> str:
        """Format severity with colors for terminal output."""
        color_map = {
            'CRITICAL': '\033[91m',  # Red
            'WARNING': '\033[93m',   # Yellow
            'INFO': '\033[94m',      # Blue
            'OK': '\033[92m'         # Green
        }
        reset = '\033[0m'
        
        if sys.stdout.isatty():  # Only use colors if outputting to terminal
            color = color_map.get(severity.upper(), '')
            return f"{color}{severity}{reset}"
        return severity

    def _format_check_result(self, check_name: str, results: List[Dict], error: Optional[str]) -> Dict[str, Any]:
        """
        Format the results of a single check.
        
        Args:
            check_name: Name of the check
            results: Query results
            error: Error message if query failed
            
        Returns:
            Formatted check result
        """
        if error:
            return {
                'check_name': check_name,
                'status': 'ERROR',
                'error': error,
                'results': [],
                'summary': f"Failed to execute: {error}"
            }
        
        if not results:
            return {
                'check_name': check_name,
                'status': 'OK',
                'results': [],
                'summary': 'No issues found'
            }
        
        # Extract status/severity from first result if available
        first_result = results[0]
        severity = 'INFO'
        summary = 'Check completed'
        
        # Look for common status/severity fields
        for field in ['severity', 'status', 'check_name']:
            if field in first_result:
                if field in ['severity', 'status']:
                    severity = str(first_result[field]).upper()
                break
        
        # Generate summary from results
        if len(results) == 1 and 'issue_count' in first_result:
            count = first_result['issue_count']
            if count == 0:
                summary = 'No issues found'
                severity = 'OK'
            else:
                summary = f"Found {count} issues"
        elif len(results) == 1 and 'article_count' in first_result:
            count = first_result['article_count']
            summary = f"Found {count} articles"
        else:
            summary = f"Returned {len(results)} rows"
        
        return {
            'check_name': check_name,
            'status': severity,
            'results': results,
            'summary': summary
        }

    def run_checks(self, specific_checks: Optional[List[int]] = None) -> Dict[str, Any]:
        """
        Run all database sanity checks.
        
        Args:
            specific_checks: List of specific check numbers to run (optional)
            
        Returns:
            Dictionary containing all check results and summary
        """
        self.logger.info(f"Starting database sanity checks on {self.db_path}")
        
        # Get SQL checks content
        try:
            sql_content = self._get_sql_checks()
            checks = self._parse_sql_content(sql_content)
        except Exception as e:
            return {
                'success': False,
                'error': f"Failed to load SQL checks: {str(e)}",
                'checks': [],
                'summary': {}
            }
        
        # Filter checks if specific ones requested
        if specific_checks:
            filtered_checks = []
            for i, check in enumerate(checks, 1):
                if i in specific_checks:
                    filtered_checks.append(check)
            checks = filtered_checks
        
        results = {
            'success': True,
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'database_path': self.db_path,
            'checks': [],
            'summary': {
                'total_checks': len(checks),
                'passed': 0,
                'warnings': 0,
                'critical': 0,
                'errors': 0,
                'info': 0
            }
        }
        
        # Run each check
        for check_name, description, queries in checks:
            self.logger.info(f"Running {check_name}")
            
            check_results = []
            overall_status = 'OK'
            
            # Execute all queries for this check
            for query in queries:
                query_results, error = self._execute_query(query)
                formatted_result = self._format_check_result(check_name, query_results, error)
                check_results.extend(formatted_result['results'])
                
                # Update overall status for this check
                if error or formatted_result['status'] == 'ERROR':
                    overall_status = 'ERROR'
                elif formatted_result['status'] == 'CRITICAL' and overall_status != 'ERROR':
                    overall_status = 'CRITICAL'
                elif formatted_result['status'] == 'WARNING' and overall_status not in ['ERROR', 'CRITICAL']:
                    overall_status = 'WARNING'
            
            # Format final result for this check
            final_result = {
                'check_name': check_name,
                'description': description,
                'status': overall_status,
                'results': check_results,
                'query_count': len(queries)
            }
            
            results['checks'].append(final_result)
            
            # Update summary counters
            if overall_status == 'OK':
                results['summary']['passed'] += 1
            elif overall_status == 'WARNING':
                results['summary']['warnings'] += 1
            elif overall_status == 'CRITICAL':
                results['summary']['critical'] += 1
            elif overall_status == 'ERROR':
                results['summary']['errors'] += 1
            else:
                results['summary']['info'] += 1
        
        self.logger.info(f"Completed {len(checks)} checks")
        return results

    def get_exit_code(self, results: Dict[str, Any]) -> int:
        """
        Get appropriate exit code based on results.
        
        Args:
            results: Results from run_checks()
            
        Returns:
            Exit code (0=success, 1=warnings, 2=critical)
        """
        if not results.get('success', False):
            return 2  # Error occurred
        
        summary = results.get('summary', {})
        if summary.get('critical', 0) > 0 or summary.get('errors', 0) > 0:
            return 2  # Critical issues
        elif summary.get('warnings', 0) > 0:
            return 1  # Warnings
        else:
            return 0  # Success

    def print_results(self, results: Dict[str, Any], json_output: bool = False) -> None:
        """
        Print formatted results to stdout.
        
        Args:
            results: Results from run_checks()
            json_output: Whether to output as JSON
        """
        if json_output:
            print(json.dumps(results, indent=2, default=str))
            return
        
        # Print header
        print("=" * 80)
        print("DAILY SCRIBE DATABASE SANITY CHECKS")
        print("=" * 80)
        print(f"Database: {results['database_path']}")
        print(f"Timestamp: {results['timestamp']}")
        print()
        
        # Print summary
        summary = results['summary']
        print("SUMMARY:")
        print(f"  Total Checks: {summary['total_checks']}")
        print(f"  {self._format_severity('OK')}: {summary['passed']}")
        print(f"  {self._format_severity('WARNING')}: {summary['warnings']}")
        print(f"  {self._format_severity('CRITICAL')}: {summary['critical']}")
        print(f"  {self._format_severity('ERROR')}: {summary['errors']}")
        print(f"  {self._format_severity('INFO')}: {summary['info']}")
        print()
        
        # Print individual check results
        for check in results['checks']:
            status_formatted = self._format_severity(check['status'])
            print(f"[{status_formatted}] {check['check_name']}")
            
            if check['description']:
                print(f"  Description: {check['description']}")
            
            # Show summary of results
            result_count = len(check['results'])
            if result_count > 0:
                print(f"  Results: {result_count} rows returned")
                
                # Show detailed results if verbose or if there are issues
                if self.verbose or check['status'] in ['WARNING', 'CRITICAL', 'ERROR']:
                    for i, result in enumerate(check['results'][:5]):  # Limit to first 5 results
                        print(f"    Row {i+1}: {dict(result)}")
                    
                    if result_count > 5:
                        print(f"    ... and {result_count - 5} more rows")
            else:
                print("  Results: No issues found")
            
            print()
        
        # Print final status
        if summary['critical'] > 0:
            print(f"🔴 {self._format_severity('CRITICAL')} issues found! Immediate attention required.")
        elif summary['warnings'] > 0:
            print(f"🟡 {self._format_severity('WARNING')} issues found. Review recommended.")
        elif summary['errors'] > 0:
            print(f"🔴 {self._format_severity('ERROR')} occurred during checks.")
        else:
            print(f"✅ All checks passed! System appears healthy.")