# backend/app/models.py
import uuid
import time
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Enum, Boolean, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class SubscriptionTier(str, PyEnum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class JobStatus(str, PyEnum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    clerk_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String)
    tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    credits_balance: Mapped[int] = mapped_column(Integer, default=50)  # Free signup bonus
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

    jobs: Mapped[List["VideoJob"]] = relationship("VideoJob", back_populates="user", cascade="all, delete-orphan")
    credit_transactions: Mapped[List["CreditTransaction"]] = relationship("CreditTransaction", back_populates="user")

class VideoJob(Base):
    __tablename__ = "video_jobs"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False, index=True)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    enhanced_prompt: Mapped[Optional[str]] = mapped_column(Text)
    provider: Mapped[str] = mapped_column(String, default="runway")  # runway, replicate, kling, wan
    model_version: Mapped[str] = mapped_column(String, default="gen3a_turbo")
    style: Mapped[str] = mapped_column(String, default="cinematic")
    duration_sec: Mapped[int] = mapped_column(Integer, default=5)
    resolution: Mapped[str] = mapped_column(String, default="1280x720")
    
    # Camera Motion Vectors
    camera_pan: Mapped[float] = mapped_column(Float, default=0.0)
    camera_tilt: Mapped[float] = mapped_column(Float, default=0.0)
    camera_zoom: Mapped[float] = mapped_column(Float, default=0.0)
    
    status: Mapped[JobStatus] = mapped_column(Enum(JobStatus), default=JobStatus.PENDING, index=True)
    progress: Mapped[int] = mapped_column(Integer, default=0)
    stage: Mapped[str] = mapped_column(String, default="queued")
    
    credits_cost: Mapped[int] = mapped_column(Integer, default=10)
    result_url: Mapped[Optional[str]] = mapped_column(Text)
    error_message: Mapped[Optional[str]] = mapped_column(Text)
    
    created_at: Mapped[float] = mapped_column(Float, default=time.time, index=True)
    completed_at: Mapped[Optional[float]] = mapped_column(Float)

    user: Mapped["User"] = relationship("User", back_populates="jobs")

class CreditTransaction(Base):
    __tablename__ = "credit_transactions"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    amount: Mapped[int] = mapped_column(Integer, nullable=False)  # positive for refill, negative for burn
    description: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

    user: Mapped["User"] = relationship("User", back_populates="credit_transactions")
