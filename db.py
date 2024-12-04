from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, JSON, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker


# Database setup
DATABASE_URL = "sqlite:///./tictactoe.db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


# Database models
class DbGame(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    moves = Column(JSON, nullable=True)  # store list of moves as JSON - not beautiful, but simple and data is small


# Create tables
Base.metadata.create_all(bind=engine)


# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
