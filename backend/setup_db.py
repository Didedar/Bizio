#!/usr/bin/env python3
"""
Setup database: create tables and seed demo data
"""
import asyncio
import os

# Set environment variable before importing
os.environ["CREATE_TABLES_ON_STARTUP"] = "true"

from app.db import create_all_tables
from seed_data import seed_demo_data

async def setup():
    print("📦 Creating database tables...")
    await create_all_tables()
    print("✅ Tables created successfully!\n")
    
    print("🌱 Seeding demo data...")
    await seed_demo_data()
    print("\n✅ Database setup complete!")

if __name__ == "__main__":
    asyncio.run(setup())
