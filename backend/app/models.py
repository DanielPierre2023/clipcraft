# backend/app/models.py
import uuid
import time
from enum import Enum as PyEnum
from typing import Optional, List
from sqlalchemy import String, Integer, Float, Text, ForeignKey, Enum, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class UserRole(str, PyEnum):
    USER = "user"
    ADMIN = "admin"

class SubscriptionTier(str, PyEnum):
    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"

class TicketStatus(str, PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"

class User(Base):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String, unique=True, index=True, nullable=False)
    clerk_id: Mapped[Optional[str]] = mapped_column(String, unique=True, index=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole), default=UserRole.USER)
    
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String, unique=True)
    stripe_subscription_id: Mapped[Optional[str]] = mapped_column(String)
    tier: Mapped[SubscriptionTier] = mapped_column(Enum(SubscriptionTier), default=SubscriptionTier.FREE)
    credits_balance: Mapped[int] = mapped_column(Integer, default=50)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)

    jobs: Mapped[List["VideoJob"]] = relationship("VideoJob", back_populates="user")
    tickets: Mapped[List["SupportTicket"]] = relationship("SupportTicket", back_populates="user")

class SupportTicket(Base):
    __tablename__ = "support_tickets"

    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String, ForeignKey("users.id"), nullable=False)
    subject: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[TicketStatus] = mapped_column(Enum(TicketStatus), default=TicketStatus.OPEN)
    admin_notes: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[float] = mapped_column(Float, default=time.time)
    updated_at: Mapped[float] = mapped_column(Float, default=time.time)

    user: Mapped["User"] = relationship("User", back_populates="tickets")
