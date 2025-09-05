#!/usr/bin/env python3
"""
Test script to verify the enhanced DatabaseService functionality.
"""

import os
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from components.database import DatabaseService
from components.config import load_config, DatabaseConfig

def test_database_environment_variables():
    """Test that DatabaseService respects environment variables."""
    print("Testing environment variable support...")
    
    # Test 1: Default values
    print("Test 1: Default values")
    service = DatabaseService()
    print(f"  Default db_path: {service.db_path}")
    print(f"  Default timeout: {service.timeout}")
    assert service.db_path == 'data/digest_history.db'
    assert service.timeout == 30.0
    print("  ✓ Default values test passed")
    
    # Test 2: Environment variables
    print("Test 2: Environment variables")
    original_db_path = os.environ.get('DB_PATH')
    original_db_timeout = os.environ.get('DB_TIMEOUT')
    
    try:
        os.environ['DB_PATH'] = '/tmp/test_db.db'
        os.environ['DB_TIMEOUT'] = '45'
        
        service = DatabaseService()
        print(f"  Env db_path: {service.db_path}")
        print(f"  Env timeout: {service.timeout}")
        assert service.db_path == '/tmp/test_db.db'
        assert service.timeout == 45.0
        print("  ✓ Environment variables test passed")
        
    finally:
        # Restore environment
        if original_db_path is not None:
            os.environ['DB_PATH'] = original_db_path
        elif 'DB_PATH' in os.environ:
            del os.environ['DB_PATH']
            
        if original_db_timeout is not None:
            os.environ['DB_TIMEOUT'] = original_db_timeout
        elif 'DB_TIMEOUT' in os.environ:
            del os.environ['DB_TIMEOUT']

def test_wal_mode():
    """Test that WAL mode is enabled."""
    print("Testing WAL mode...")
    
    db_path = "test_wal.db"
    service = DatabaseService(db_path=db_path)
    
    try:
        with service._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA journal_mode")
            result = cursor.fetchone()
            print(f"  Journal mode: {result[0]}")
            assert result[0].upper() == 'WAL'
        print("  ✓ WAL mode test passed")
        
    finally:
        # Clean up
        for file_ext in ['', '-wal', '-shm']:
            file_path = db_path + file_ext
            if os.path.exists(file_path):
                os.remove(file_path)

def test_database_config():
    """Test DatabaseConfig class."""
    print("Testing DatabaseConfig class...")
    
    config = DatabaseConfig(path="/tmp/test.db", timeout=60)
    print(f"  Config path: {config.path}")
    print(f"  Config timeout: {config.timeout}")
    assert config.path == "/tmp/test.db"
    assert config.timeout == 60
    print("  ✓ DatabaseConfig test passed")

def test_initialization_idempotent():
    """Test that initialization is idempotent."""
    print("Testing idempotent initialization...")
    
    db_path = "test_idempotent.db"
    service = DatabaseService(db_path=db_path)
    
    try:
        # Initialize multiple times
        service._initialize_database()
        service._initialize_database()
        
        # Verify database works
        assert os.path.exists(db_path)
        print("  ✓ Idempotent initialization test passed")
        
    finally:
        # Clean up
        for file_ext in ['', '-wal', '-shm']:
            file_path = db_path + file_ext
            if os.path.exists(file_path):
                os.remove(file_path)

if __name__ == "__main__":
    print("Running DatabaseService enhancement tests...")
    
    try:
        test_database_environment_variables()
        test_wal_mode()
        test_database_config()
        test_initialization_idempotent()
        
        print("\n🎉 All tests passed! DatabaseService enhancements are working correctly.")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
