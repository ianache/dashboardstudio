from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.core.config import get_settings
from app.core.database import SessionLocal

import logging

logger = logging.getLogger("uvicorn.error")
settings = get_settings()
security = HTTPBearer(auto_error=False)

# Simple in-memory cache for JWKS
JWKS_CACHE = None
JWKS_LAST_FETCH = None

class TokenData:
    def __init__(self, sub: str, roles: list[str], email: Optional[str] = None, name: Optional[str] = None):
        self.sub = sub
        self.roles = roles
        self.email = email
        self.name = name


async def ensure_user_exists(token_data: TokenData):
    """Ensure user exists in database, create if not"""
    from app.models import models
    
    db = SessionLocal()
    try:
        # Check if user exists
        user = db.query(models.User).filter(models.User.id == token_data.sub).first()
        
        if not user:
            # Auto-create user from Keycloak token
            user = models.User(
                id=token_data.sub,
                email=token_data.email,
                username=token_data.name or token_data.sub,
                full_name=token_data.name,
                first_name=token_data.name.split()[0] if token_data.name else None,
                last_name=" ".join(token_data.name.split()[1:]) if token_data.name and len(token_data.name.split()) > 1 else None,
                role=token_data.roles[0] if token_data.roles else "viewer",
                avatar=token_data.name[:2].upper() if token_data.name else token_data.sub[:2].upper(),
                is_active=True
            )
            db.add(user)
            db.commit()
        else:
            # Synchronize details from Keycloak token
            updated = False
            token_role = token_data.roles[0] if token_data.roles else "viewer"
            if user.role != token_role:
                user.role = token_role
                updated = True
            if token_data.email and user.email != token_data.email:
                user.email = token_data.email
                updated = True
            if token_data.name and user.full_name != token_data.name:
                user.full_name = token_data.name
                updated = True
            if updated:
                db.add(user)
                db.commit()
    except Exception as e:
        print(f"Error ensuring user exists: {e}")
        # We don't want to crash the whole request if user creation fails
        # but we should log it
    finally:
        db.close()


async def get_jwks():
    global JWKS_CACHE, JWKS_LAST_FETCH
    
    now = datetime.utcnow().timestamp()
    if JWKS_CACHE and JWKS_LAST_FETCH and (now - JWKS_LAST_FETCH < 3600):
        return JWKS_CACHE

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(settings.keycloak_jwks_url)
            response.raise_for_status()
            JWKS_CACHE = response.json()
            JWKS_LAST_FETCH = now
            return JWKS_CACHE
    except Exception as e:
        if JWKS_CACHE:
            return JWKS_CACHE
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Could not fetch JWKS from Keycloak: {str(e)}"
        )


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> TokenData:
    logger.warning("--- [VERIFY_TOKEN ENTRY] ---")
    logger.warning(f"Credentials object: {credentials}")
    
    if not credentials:
        logger.warning("ERROR: No credentials/header provided!")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    logger.warning(f"Token length: {len(token)} chars")
    
    try:
        unverified_header = jwt.get_unverified_header(token)
        logger.warning(f"Unverified Header: {unverified_header}")
    except JWTError as e:
        logger.warning(f"ERROR: Failed to parse unverified header: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    try:
        jwks = await get_jwks()
        logger.warning(f"Fetched JWKS successfully. Keys count: {len(jwks.get('keys', []))}")
    except Exception as e:
        logger.warning(f"ERROR: Failed to fetch JWKS: {e}")
        raise
        
    jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    logger.warning(f"JWK match for kid '{unverified_header.get('kid')}': {jwk is not None}")
    
    if not jwk:
        logger.warning(f"ERROR: Could not find JWK for kid '{unverified_header.get('kid')}'")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate key",
        )

    # Decode and verify the token. We bypass strict audience verification in dev/QA,
    # but strictly verify the cryptographic signature and the issuer.
    try:
        unverified_claims = jwt.get_unverified_claims(token)
    except Exception as e:
        unverified_claims = f"Failed to parse claims: {e}"

    logger.warning("--- [TOKEN VERIFICATION DEBUG] ---")
    logger.warning(f"Token (first 30 chars): {token[:30]}...")
    logger.warning(f"Unverified claims: {unverified_claims}")
    logger.warning(f"Expected issuer: {settings.keycloak_url}/realms/{settings.keycloak_realm}")
    
    try:
        payload = jwt.decode(
            token,
            jwk,
            algorithms=["RS256"],
            issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
            options={"verify_aud": False, "leeway": 120}
        )
        logger.warning("Successfully verified token signature and issuer!")
    except JWTError as e:
        logger.warning(f"ERROR: Token validation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )
    logger.warning("---------------------------------")

    realm_access = payload.get("realm_access", {})
    roles = realm_access.get("roles", []) if isinstance(realm_access, dict) else []
    
    # Filter only app roles
    app_roles = [r for r in roles if r in ["admin", "designer", "viewer"]]

    return TokenData(
        sub=payload.get("sub", ""),
        roles=app_roles,
        email=payload.get("email"),
        name=payload.get("name"),
    )


async def get_current_user(token_data: TokenData = Depends(verify_token)) -> TokenData:
    await ensure_user_exists(token_data)
    return token_data


def require_role(allowed_roles: list[str]):
    async def role_checker(current_user: TokenData = Depends(get_current_user)) -> TokenData:
        if not any(role in current_user.roles for role in allowed_roles):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user
    return role_checker
