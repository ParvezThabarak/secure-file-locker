#!/usr/bin/env python3
"""
Database initialization script
Run this to create tables and initial migration
"""

import os
import sys
from flask_migrate import init, migrate, upgrade

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from app.database.database import db

def init_database():
    """Initialize the database with tables and migrations"""
    app = create_app('development')
    
    with app.app_context():
        try:
            # Initialize migration repository if it doesn't exist
            if not os.path.exists('migrations'):
                print("Initializing migration repository...")
                init()
            
            # Create initial migration
            print("Creating initial migration...")
            migrate(message='Initial migration')
            
            # Create all tables
            print("Creating database tables...")
            db.create_all()
            
            print("Database initialization completed successfully!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            return False
    
    return True

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1)
