import asyncio
import sys
import os

# Add the backend directory to sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db import async_session_maker
from app.models import Deal, Order
from sqlalchemy import delete

async def clear_data():
    async with async_session_maker() as db:
        print("Deleting Deals...")
        await db.execute(delete(Deal))
        print("Deleting Orders...")
        await db.execute(delete(Order))
        await db.commit()
        print("Data cleared successfully.")

if __name__ == "__main__":
    asyncio.run(clear_data())
