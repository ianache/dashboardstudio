from datetime import datetime
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import httpx
from app.core.config import get_settings

settings = get_settings()
security = HTTPBearer(auto_error=False)


class TokenData:
    def __init__(self, sub: str, roles: list[str], email: Optional[str] = None, name: Optional[str] = None):
        self.sub = sub
        self.roles = roles
        self.email = email
        self.name = name


async def get_jwks():
    async with httpx.AsyncClient() as client:
        response = await client.get(settings.keycloak_jwks_url)
        return response.json()


async def verify_token(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> TokenData:
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    
    try:
        unverified_header = jwt.get_unverified_header(token)
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token header",
        )

    jwks = await get_jwks()
    jwk = next((k for k in jwks.get("keys", []) if k.get("kid") == unverified_header.get("kid")), None)
    
    if not jwk:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unable to find appropriate key",
        )

    try:
        payload = jwt.decode(
            token,
            jwk,
            algorithms=["RS256"],
            audience=settings.keycloak_client_id,
            issuer=f"{settings.keycloak_url}/realms/{settings.keycloak_realm}",
        )
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(e)}",
        )

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