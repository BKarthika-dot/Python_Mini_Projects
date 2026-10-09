"""SQLAlchemy models + session (SQLite by default; set DATABASE_URL for PostgreSQL)."""
import os, datetime as dt
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

engine = create_engine(os.getenv("DATABASE_URL", "sqlite:///fjpc.db"), connect_args={"check_same_thread": False} if "sqlite" in os.getenv("DATABASE_URL", "sqlite") else {})
SessionLocal = sessionmaker(bind=engine, autoflush=False)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    pw_hash = Column(String, nullable=False)
    role = Column(String, default="job_seeker")  # job_seeker | admin


class Company(Base):  # whitelist / blacklist of employer domains
    __tablename__ = "companies"
    id = Column(Integer, primary_key=True)
    domain = Column(String, unique=True, nullable=False)
    status = Column(String, nullable=False)  # whitelist | blacklist


class Submission(Base):  # a submission and its classification result
    __tablename__ = "submissions"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    input_type = Column(String)
    source_url = Column(String, nullable=True)
    content = Column(Text)  # extracted text (kept for retraining)
    category = Column(String)
    confidence = Column(Float)
    rule_score = Column(Float)
    ml_score = Column(Float)
    rag_score = Column(Float)
    explanation = Column(Text)
    created_at = Column(DateTime, default=dt.datetime.utcnow)
    feedback_status = Column(String, default="none")  # none | reported | confirmed
    suggested_label = Column(Integer, nullable=True)  # user's claim: 1 scam / 0 legit
    final_label = Column(Integer, nullable=True)  # admin-confirmed label
    used_for_training = Column(Boolean, default=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
