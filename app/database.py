from sqlalchemy import create_engine, Column, String, Integer, Text
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import Generator
import os
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://nwsl:nwsl@localhost/nwsl_db"
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)
Base = declarative_base()

class PlayerDB(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    number = Column(Integer, nullable=True)
    age = Column(Integer, nullable=True)
    country = Column(String, nullable=False)
    position = Column(String, nullable=False)
    team = Column(String, nullable=False, index=True)
    note = Column(Text, nullable=True)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
