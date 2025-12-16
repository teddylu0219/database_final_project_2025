#!/usr/bin/env python3
"""Database Initialization Script (schema only; load data via load_all.sh or /import)."""

from db import init_db

if __name__ == '__main__':
    print("=" * 50)
    print("NYCU Food Recommendation Database Initialization")
    print("=" * 50)
    print()

    try:
        init_db()
        print()
        print("=" * 50)
        print("SUCCESS! Database schema initialized successfully!")
        print("=" * 50)
        print()
        print("Load data via: bash load_all.sh   (uses data/*.csv)")
        print("Or use the web importer at /import")
        print()

    except Exception as e:
        print()
        print("=" * 50)
        print("ERROR! Database initialization failed!")
        print("=" * 50)
        print()
        print(f"Error: {e}")
        print()
        print("Please check:")
        print("1. PostgreSQL is running")
        print("2. Database 'nycu_food' exists")
        print("3. .env file is configured correctly")
        print("4. Database credentials are correct")
        print()
        exit(1)
