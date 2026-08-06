# backend/app/auth.py
import os
import jwt
import httpx
from typing import Optional, Dict, Any
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from .database import get_db
from .models import User, SubscriptionTier

CLERK_JWKS_URL = os.getenv("CLERK_JWKS_URL")  # e.g. https://<clerk-domain>.clerk.accounts.dev/.well-known/jwks.json
security = HTTPBearer()

_jwks_cache: Optional[Dict[str, Any]] = None

async def get_jwks() -> Dict[str, Any]:
    global _jwks_cache
    if not _jwks_cache:
        async with httpx.AsyncClient() as client:
            resp = await client.get(CLERK_JWKS_URL)
            resp.raise_for_status()
            _jwks_cache = resp.json()
    return _jwks_cache

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """Authenticates request via Clerk JWT and returns or auto-provisions the DB user."""
    token = credentials.credentials
    try:
        jwks = await get_jwks()
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header["kid"]
        
        key = next((k for k in jwks["keys"] if k["kid"] == kid), None)
        if not key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid key ID")

        public_key = jwt.algorithms.RSAAlgorithm.from_jwk(key)
        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"verify_aud": False}
        )
        
        clerk_id = payload.get("sub")
        email = payload.get("email") or f"{clerk_id}@clerk.user"

        # Lookup or provision user record
        stmt = select(User).where(User.clerk_id == clerk_id)
        result = await db.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            user = User(
                clerk_id=clerk_id,
                email=email,
                tier=SubscriptionTier.FREE,
                credits_balance=50
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)

        return user

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Authentication failed: {str(e)}"
        )
