#!/usr/bin/env python3
"""
Database Setup Script for S3 File Manager Backend
This script handles database connection, creation, and table setup.
"""

import os
import sys
import time
import pymysql
from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError


def wait_for_database(max_retries=30, delay=5):
    """
    Wait for the database to be available and create it if it doesn't exist.
    """
    print("🚀 Starting S3 File Manager Backend...")
    print("⏳ Checking database connection and creating database if needed...")
    
    # Get database credentials from environment
    db_host = os.getenv('MYSQL_HOST')
    db_user = os.getenv('MYSQL_USER')
    db_password = os.getenv('MYSQL_PASSWORD')
    db_name = os.getenv('MYSQL_DB')
    db_port = int(os.getenv('MYSQL_PORT', 3306))
    
    if not all([db_host, db_user, db_password, db_name]):
        print("❌ Missing database credentials in environment variables")
        print("Required: MYSQL_HOST, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DB")
        sys.exit(1)
    
    print(f"Connecting to MySQL at {db_host}:{db_port}...")
    
    for attempt in range(max_retries):
        try:
            # First try to connect to MySQL server (without database)
            connection = pymysql.connect(
                host=db_host,
                user=db_user,
                password=db_password,
                port=db_port
            )
            
            # Check if database exists, create if not
            cursor = connection.cursor()
            cursor.execute(f'CREATE DATABASE IF NOT EXISTS {db_name}')
            connection.commit()
            cursor.close()
            connection.close()
            
            print(f"✅ Database {db_name} is ready!")
            return True
            
        except Exception as e:
            print(f"Database connection failed: {e}")
            if attempt < max_retries - 1:
                print(f"Database not ready, waiting {delay} seconds...")
                time.sleep(delay)
            else:
                print(f"❌ Database did not become ready after {max_retries} attempts")
                return False
    
    return False


def setup_database_tables(app):
    """
    Create database tables using SQLAlchemy's create_all().
    """
    print("🗄️  Setting up database tables...")
    
    try:
        with app.app_context():
            from app.database.database import db
            
            # Create all tables
            db.create_all()
            print("✅ Database tables created/verified")
                
    except Exception as e:
        print(f"❌ Database table setup failed: {e}")
        return False
    
    return True


def verify_database_tables(app):
    """
    Verify that all required tables exist.
    """
    print("🔍 Verifying database tables...")
    
    try:
        with app.app_context():
            from app.database.database import db
            
            # Check if tables exist by trying to query them
            try:
                # Try to query the users table
                result = db.session.execute(text("SELECT COUNT(*) FROM users"))
                users_count = result.scalar()
                print(f"✅ Users table exists ({users_count} users)")
                
                # Try to query the files table
                result = db.session.execute(text("SELECT COUNT(*) FROM files"))
                files_count = result.scalar()
                print(f"✅ Files table exists ({files_count} files)")
                
                # Try to query the aws_credentials table
                result = db.session.execute(text("SELECT COUNT(*) FROM aws_credentials"))
                aws_count = result.scalar()
                print(f"✅ AWS credentials table exists ({aws_count} credentials)")
                
                print("✅ All database tables verified successfully")
                return True
                
            except Exception as e:
                print(f"❌ Table verification failed: {e}")
                return False
                
    except Exception as e:
        print(f"❌ Database verification failed: {e}")
        return False


def setup_database(app):
    """
    Main database setup function.
    """
    print("=" * 50)
    print("🗄️  DATABASE SETUP")
    print("=" * 50)
    
    # Step 1: Wait for database and create if needed
    if not wait_for_database():
        print("❌ Database setup failed - could not connect to database")
        return False
    
    # Step 2: Setup tables
    if not setup_database_tables(app):
        print("❌ Database setup failed - table setup failed")
        return False
    
    # Step 3: Verify tables
    if not verify_database_tables(app):
        print("❌ Database setup failed - table verification failed")
        return False
    
    print("=" * 50)
    print("✅ DATABASE SETUP COMPLETE")
    print("=" * 50)
    return True


if __name__ == "__main__":
    # This script can be run standalone for testing
    from app import create_app
    
    app = create_app()
    success = setup_database(app)
    sys.exit(0 if success else 1)
