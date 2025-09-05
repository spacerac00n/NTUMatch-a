from fastapi import FastAPI, HTTPException, Depends

from sqlalchemy import create_engine, Column, Integer, String, Boolean, LargeBinary, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session 

from pydantic import BaseModel, ConfigDict
from typing import List, Optional

from datetime import datetime, timezone

app = FastAPI(title="NTUMatch API")

# Database Setup 
engine = create_engine("postgresql+psycopg://postgres:postgres@localhost:5432/ntumatch", echo=True )
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Database Model 
class User (Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    telegram_username = Column(String, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, index=True, nullable=False)
    gender = Column(String, index=True, nullable=False)
    hobby = Column (String, index=True, nullable=True)
    description = Column (String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))

Base.metadata.create_all(bind=engine)

# Pydantic Model 
class UserCreate (BaseModel): # Input Schema
    telegram_username: str
    email: str
    name: str
    age: int
    gender: str
    hobby: str
    description: str

class UserResponse (BaseModel): # Output Schema 
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

def get_db ():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

get_db()

# Creating the Endpoint
@app.get("/")
def read_root():
    return {
        "name": "NTU Match API",
        "version": "1.0.0",
        "description": "An API for matching NTU students",
        "docs": "/docs"
    }

@app.post("/users/", response_model= UserResponse) # Create
def create_user (user: UserCreate, db: Session = Depends (get_db)):
    if db.query(User).filter(User.email == user.email).first():
        raise HTTPException(status_code=404, detail="User already exists")

    # Create a new user
    new_user = User(**user.dict()) # ** means unpacking the user dictionary input. Just unpack the input from API
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user

@app.put("/users/telegram/{telegram_username}", response_model = UserResponse) # Update
def update_user_by_telegram_username (telegram_username: str, user: UserCreate, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.telegram_username == telegram_username).first()
        if not db_user:
            raise HTTPException(status_code = 404, detail = "User not found")

        # Update user information
        for key, value in user.dict().items():
            setattr(db_user, key, value)
        db.commit()
        db.refresh(db_user)
        return db_user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))

@app.get("/users/telegram/{telegram_username}", response_model=UserResponse) # Get user by telegram username
def get_user_by_telegram_username(telegram_username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_username == telegram_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.delete("/users/telegram/{telegram_username}", response_model=UserResponse) # Delete
def delete_user_by_telegram_username(telegram_username: str, db: Session = Depends(get_db)):
    try:
        db_user = db.query(User).filter(User.telegram_username == telegram_username).first()
        if not db_user:
            raise HTTPException(status_code=404, detail="User not found")

        db.delete(db_user)
        db.commit()
        return db_user
    except Exception as e:
        raise HTTPException(status_code=404, detail=str(e))