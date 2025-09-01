from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from typing import List
import secrets
from datetime import datetime, timedelta, timezone

from .. import schemas
from ..db import models
from ..db.session import get_db
from ..security import auth

router = APIRouter(prefix="/v1/tokens", tags=["Admin & Tokens"])

@router.post("/", response_model=schemas.NewTokenResponse, status_code=201)
def create_token(
    token_req: schemas.TokenCreateRequest,
    db: Session = Depends(get_db),
    current_token: models.Token = Depends(auth.require_scope("admin:write"))
):
    api_token = secrets.token_urlsafe(32)
    hashed_token = auth.hash_token(api_token)
    
    expires_at = None
    if token_req.expires_in_days is not None:
        expires_at = datetime.now(timezone.utc) + timedelta(days=token_req.expires_in_days)
        
    db_token = models.Token(
        name=token_req.name,
        hashed_token=hashed_token,
        scopes=token_req.scopes,
        expires_at=expires_at,
        owner_username=token_req.owner_username
    )
    
    try:
        db.add(db_token)
        db.commit()
        db.refresh(db_token)
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail=f"Um token com o nome '{token_req.name}' já existe para este usuário."
        )
    
    return schemas.NewTokenResponse(
        token_details=schemas.TokenResponse.from_orm(db_token),
        api_token=api_token
    )

@router.get("/", response_model=List[schemas.TokenResponse])
def list_tokens(
    db: Session = Depends(get_db),
    current_token: models.Token = Depends(auth.require_scope("admin:read"))
):
    tokens = db.query(models.Token).filter(models.Token.is_revoked == False).all()
    return tokens

@router.delete("/{token_id}", status_code=204)
def revoke_token(
    token_id: int,
    db: Session = Depends(get_db),
    current_token: models.Token = Depends(auth.require_scope("admin:write"))
):
    db_token = db.query(models.Token).filter(models.Token.id == token_id).first()
    if not db_token:
        raise HTTPException(status_code=404, detail="Token not found")
    
    db_token.is_revoked = True
    db.commit()
    return None
