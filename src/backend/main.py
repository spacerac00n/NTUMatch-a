from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, ConfigDict
from typing import Optional
from datetime import datetime, timezone
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

# FastAPI app
app = FastAPI(title="NTUMatch API")

# Get DB credentials
host = os.getenv("DB_HOST")
port = os.getenv("DB_PORT")
dbname = os.getenv("DB_NAME")
user = os.getenv("DB_USER")
password = os.getenv("DB_PASSWORD")

# SQLAlchemy database URL
DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"

# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True enables SQL debug logs

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Model
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, index=True, nullable=False)
    gender = Column(String, index=True, nullable=False)
    hobby = Column(String, index=True, nullable=True)
    description = Column(String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

# Create tables automatically
Base.metadata.create_all(bind=engine)

# Pydantic Models
class UserCreate(BaseModel):
    telegram_username: str
    email: str
    name: str
    age: int
    gender: str
    hobby: str
    description: str

class UserResponse(BaseModel):
    id: int
    telegram_username: str
    email: str
    name: str
    age: int
    gender: str
    hobby: str
    description: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Root endpoint
@app.get("/")
def read_root():
    return {
        "name": "NTU Match API",
        "version": "1.0.0",
        "description": "An API for matching NTU students",
        "docs": "/docs"
    }

# Create User
@app.post("/users/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=409, detail="User already exists")

    new_user = User(**user.dict())
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

# Update User by Telegram Username
@app.put("/users/telegram/{telegram_username}", response_model=UserResponse)
def update_user_by_telegram_username(telegram_username: str, user: UserCreate, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.telegram_username == telegram_username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    for key, value in user.dict().items():
        setattr(db_user, key, value)

    db.commit()
    db.refresh(db_user)
    return db_user

# Get User by Telegram Username
@app.get("/users/telegram/{telegram_username}", response_model=UserResponse)
def get_user_by_telegram_username(telegram_username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_username == telegram_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

# Delete User by Telegram Username
@app.delete("/users/telegram/{telegram_username}", response_model=UserResponse)
def delete_user_by_telegram_username(telegram_username: str, db: Session = Depends(get_db)):
    db_user = db.query(User).filter(User.telegram_username == telegram_username).first()
    if not db_user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(db_user)
    db.commit()
    return db_user

# Run FastAPI
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
