import asyncio 
from app.db.models import User
from app.db.database import AsyncSessionLocal

from app.core.security import get_password_hash

async def create_first_user():
    async with AsyncSessionLocal() as session:
        username = "admin"
        password = "kakdela1"


        hashed_password = get_password_hash(password)

        new_user =  User(username=username, hashed_password=hashed_password)

        session.add(new_user)

        try:
            await session.commit()
            print (f"Ebat kak '{username}' Yeah")

            session.add(new_user)
        except Exception as e:
            await session.rollback()
            print("Failed")

if __name__ == "__main__":
    asyncio.run(create_first_user())