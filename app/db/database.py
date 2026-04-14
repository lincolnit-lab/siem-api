import os
from sqlalchemy.orm import sessionmaker, declarative_base
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_async_engine(DATABASE_URL, connect_args={"check_same_thread": False})


AsyncSessionLocal = sessionmaker(bind=engine, class_= AsyncSession, expire_on_commit=False)

Base = declarative_base()
