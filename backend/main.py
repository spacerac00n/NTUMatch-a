from fastapi import FastAPI, HTTPException, Depends
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    func,
    or_,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from pydantic import BaseModel, ConfigDict
from datetime import datetime, timezone
from dotenv import load_dotenv
import os
from typing import List, Optional

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
#DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}"
#DATABASE_URL = f"postgresql://postgres:{password}@db.ymknmrnlepsqpualasmj.supabase.co:5432/postgres"
DATABASE_URL = (
    f"postgresql+psycopg2://postgres.ymknmrnlepsqpualasmj:{password}"
    "@aws-1-ap-southeast-1.pooler.supabase.com:5432/postgres"
)


# Create SQLAlchemy engine
engine = create_engine(DATABASE_URL, echo=True)  # echo=True enables SQL debug logs

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Database Model
class User(Base):
    __tablename__ = "users"

    telegram_username = Column(String, index=True, nullable=False, unique=True, primary_key=True)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, index=True, nullable=False)
    age = Column(Integer, index=True, nullable=False)
    gender = Column(String, index=True, nullable=False)
    hobby = Column(String, index=True, nullable=True)
    description = Column(String, index=True, nullable=True)
    picture_id = Column(String, index=True, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc))


class UserInteraction(Base):
    __tablename__ = "user_interactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_username = Column(
        String,
        ForeignKey("users.telegram_username"),
        nullable=False,
        index=True,
    )
    target_username = Column(
        String,
        ForeignKey("users.telegram_username"),
        nullable=False,
        index=True,
    )
    action = Column(String, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)


class Match(Base):
    __tablename__ = "matches"
    __table_args__ = (
        UniqueConstraint("user1_username", "user2_username", name="uq_match_pair"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    user1_username = Column(
        String,
        ForeignKey("users.telegram_username"),
        nullable=False,
        index=True,
    )
    user2_username = Column(
        String,
        ForeignKey("users.telegram_username"),
        nullable=False,
        index=True,
    )
    matched_at = Column(DateTime, default=datetime.now(timezone.utc), nullable=False)


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
    picture_id: str

class UserResponse(BaseModel):
    telegram_username: str
    email: str
    name: str
    age: int
    gender: str
    hobby: str
    picture_id: str
    description: str
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InteractionCreate(BaseModel):
    user_username: str
    target_username: str
    action: str


class MatchInfo(BaseModel):
    id: int
    matched_at: datetime
    user: UserResponse


class InteractionResponse(BaseModel):
    status: str
    is_match: bool = False
    match: Optional[MatchInfo] = None


MatchListResponse = List[MatchInfo]

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


@app.get("/users/random/{telegram_username}", response_model=UserResponse)
def get_random_user(telegram_username: str, db: Session = Depends(get_db)):
    requesting_user = (
        db.query(User).filter(User.telegram_username == telegram_username).first()
    )
    if not requesting_user:
        raise HTTPException(status_code=404, detail="Requesting user not found")

    candidate = (
        db.query(User)
        .outerjoin(
            UserInteraction,
            (UserInteraction.target_username == User.telegram_username)
            & (UserInteraction.user_username == telegram_username),
        )
        .filter(
            User.telegram_username != telegram_username,
            User.is_active.is_(True),
            UserInteraction.id.is_(None),
        )
        .order_by(func.random())
        .first()
    )

    if not candidate:
        raise HTTPException(status_code=404, detail="No more profiles available")

    return candidate


@app.post("/interactions/", response_model=InteractionResponse)
def record_interaction(interaction: InteractionCreate, db: Session = Depends(get_db)):
    action = interaction.action.lower()
    if action not in {"like", "dislike"}:
        raise HTTPException(status_code=400, detail="Invalid action")

    if interaction.user_username == interaction.target_username:
        raise HTTPException(status_code=400, detail="Cannot interact with yourself")

    user = db.query(User).filter(User.telegram_username == interaction.user_username).first()
    target_user = (
        db.query(User).filter(User.telegram_username == interaction.target_username).first()
    )

    if not user or not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    match_record: Optional[Match] = None

    try:
        existing = (
            db.query(UserInteraction)
            .filter(
                UserInteraction.user_username == interaction.user_username,
                UserInteraction.target_username == interaction.target_username,
            )
            .first()
        )

        if existing:
            existing.action = action
            existing.created_at = datetime.now(timezone.utc)
        else:
            new_interaction = UserInteraction(
                user_username=interaction.user_username,
                target_username=interaction.target_username,
                action=action,
            )
            db.add(new_interaction)

        if action == "like":
            reverse_like = (
                db.query(UserInteraction)
                .filter(
                    UserInteraction.user_username == interaction.target_username,
                    UserInteraction.target_username == interaction.user_username,
                    UserInteraction.action == "like",
                )
                .first()
            )

            if reverse_like:
                sorted_usernames = sorted(
                    [interaction.user_username, interaction.target_username]
                )
                match_record = (
                    db.query(Match)
                    .filter(
                        Match.user1_username == sorted_usernames[0],
                        Match.user2_username == sorted_usernames[1],
                    )
                    .first()
                )

                if not match_record:
                    match_record = Match(
                        user1_username=sorted_usernames[0],
                        user2_username=sorted_usernames[1],
                    )
                    db.add(match_record)

        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to record interaction") from exc

    match_info: Optional[MatchInfo] = None

    if match_record:
        db.refresh(match_record)
        matched_username = (
            match_record.user2_username
            if match_record.user1_username == interaction.user_username
            else match_record.user1_username
        )
        matched_user = (
            db.query(User).filter(User.telegram_username == matched_username).first()
        )
        if matched_user:
            match_info = MatchInfo(
                id=match_record.id,
                matched_at=match_record.matched_at,
                user=UserResponse.model_validate(matched_user),
            )

    return InteractionResponse(status="recorded", is_match=bool(match_record), match=match_info)


@app.get("/matches/{telegram_username}", response_model=MatchListResponse)
def get_user_matches(telegram_username: str, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.telegram_username == telegram_username).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    matches = (
        db.query(Match)
        .filter(
            or_(
                Match.user1_username == telegram_username,
                Match.user2_username == telegram_username,
            )
        )
        .order_by(Match.matched_at.desc())
        .all()
    )

    results: MatchListResponse = []

    for match in matches:
        partner_username = (
            match.user2_username
            if match.user1_username == telegram_username
            else match.user1_username
        )
        partner = (
            db.query(User).filter(User.telegram_username == partner_username).first()
        )
        if not partner:
            continue

        results.append(
            MatchInfo(
                id=match.id,
                matched_at=match.matched_at,
                user=UserResponse.model_validate(partner),
            )
        )

    return results

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
