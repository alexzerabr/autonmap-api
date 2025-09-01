from fastapi import Depends, HTTPException, Security
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session
from passlib.context import CryptContext
import secrets
from datetime import datetime, timezone

from ..db import models
from ..db.session import get_db

api_key_header = APIKeyHeader(name="X-API-Token", auto_error=False)
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def hash_token(token: str) -> str:
    return pwd_context.hash(token)

def verify_token(plain_token: str, hashed_token: str) -> bool:
    return pwd_context.verify(plain_token, hashed_token)

async def get_current_token(
    api_key: str = Security(api_key_header), db: Session = Depends(get_db)
) -> models.Token:
    if not api_key:
        raise HTTPException(status_code=401, detail="API Token required")

    all_tokens = db.query(models.Token).filter(models.Token.is_revoked == False).all()
    
    db_token = None
    for token in all_tokens:
        if verify_token(api_key, token.hashed_token):
            db_token = token
            break
            
    if db_token is None:
        raise HTTPException(status_code=401, detail="Invalid API Token")

    if db_token.expires_at and db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="API Token has expired")

    return db_token

def require_scope(required_scope: str):
    def dependency(token: models.Token = Depends(get_current_token)) -> models.Token:
        if required_scope not in token.scopes:
            raise HTTPException(
                status_code=403,
                detail=f"Insufficient permissions. Scope '{required_scope}' required.",
            )
        return token
    return dependency
