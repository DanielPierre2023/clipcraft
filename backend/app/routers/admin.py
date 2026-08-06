# backend/app/routers/admin.py
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from pydantic import BaseModel, Field
from typing import Optional, List
import time

from ..database import get_db
from ..models import User, UserRole, SubscriptionTier, SupportTicket, TicketStatus, VideoJob
from ..auth import require_admin

router = APIRouter(prefix="/api/v1/admin", tags=["Executive Admin"])

TIER_PRICES = {
    SubscriptionTier.FREE: 0.0,
    SubscriptionTier.STARTER: 19.99,
    SubscriptionTier.PRO: 49.99,
    SubscriptionTier.ENTERPRISE: 149.99
}

# --- DTO Models ---
class UpdatePlanRequest(BaseModel):
    tier: SubscriptionTier

class GrantCreditsRequest(BaseModel):
    credits: int = Field(..., description="Number of credits to grant or deduct")
    reason: str

class ResolveTicketRequest(BaseModel):
    status: TicketStatus
    admin_notes: Optional[str] = None

# --- Endpoints ---

@router.get("/analytics")
async def get_earnings_and_metrics(
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Provides financial overview, MRR calculation, and usage telemetry."""
    total_users = (await db.execute(select(func.count(User.id)))).scalar_one()
    total_jobs = (await db.execute(select(func.count(VideoJob.id)))).scalar_one()
    
    # Calculate Monthly Recurring Revenue (MRR) based on active user tiers
    tier_counts = (await db.execute(
        select(User.tier, func.count(User.id)).group_by(User.tier)
    )).all()
    
    mrr = sum(TIER_PRICES[tier] * count for tier, count in tier_counts)
    
    open_tickets = (await db.execute(
        select(func.count(SupportTicket.id)).where(SupportTicket.status == TicketStatus.OPEN)
    )).scalar_one()

    return {
        "mrr_usd": round(mrr, 2),
        "total_users": total_users,
        "total_renders": total_jobs,
        "open_tickets": open_tickets,
        "tier_breakdown": {tier.value: count for tier, count in tier_counts}
    }

@router.get("/users")
async def list_users(
    search: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Lists users with search, tier filtering, and credit balances."""
    query = select(User).order_by(User.created_at.desc()).offset(offset).limit(limit)
    if search:
        query = query.where(User.email.ilike(f"%{search}%"))
    
    users = (await db.execute(query)).scalars().all()
    return [{"id": u.id, "email": u.email, "role": u.role, "tier": u.tier, "credits": u.credits_balance, "created_at": u.created_at} for u in users]

@router.patch("/users/{user_id}/plan")
async def override_user_plan(
    user_id: str,
    payload: UpdatePlanRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Manually upgrades or downgrades a user's subscription tier."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.tier = payload.tier
    await db.commit()
    return {"status": "success", "user_id": user.id, "new_tier": user.tier}

@router.post("/users/{user_id}/credits")
async def grant_user_credits(
    user_id: str,
    payload: GrantCreditsRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Gifts or deducts credits for a user to resolve complaints or custom deals."""
    user = (await db.execute(select(User).where(User.id == user_id))).scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.credits_balance += payload.credits
    await db.commit()
    return {"status": "success", "user_id": user.id, "updated_balance": user.credits_balance, "granted": payload.credits}

@router.get("/tickets")
async def list_support_tickets(
    status_filter: Optional[TicketStatus] = None,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Lists customer complaint and bug report tickets."""
    query = select(SupportTicket).order_by(SupportTicket.created_at.desc())
    if status_filter:
        query = query.where(SupportTicket.status == status_filter)
    
    tickets = (await db.execute(query)).scalars().all()
    return tickets

@router.patch("/tickets/{ticket_id}")
async def resolve_ticket(
    ticket_id: str,
    payload: ResolveTicketRequest,
    admin: User = Depends(require_admin),
    db: AsyncSession = Depends(get_db)
):
    """Updates support ticket status and attaches resolution notes."""
    ticket = (await db.execute(select(SupportTicket).where(SupportTicket.id == ticket_id))).scalar_one_or_none()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")

    ticket.status = payload.status
    if payload.admin_notes:
        ticket.admin_notes = payload.admin_notes
    ticket.updated_at = time.time()
    await db.commit()
    return {"status": "success", "ticket_id": ticket.id, "new_status": ticket.status}
