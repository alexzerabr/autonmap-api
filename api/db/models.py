import uuid
from sqlalchemy import (
    Column, Integer, String, DateTime, ForeignKey,
    Text, Boolean, JSON, Index
)
from sqlalchemy.orm import relationship, DeclarativeBase
from sqlalchemy.sql import func, text
from sqlalchemy.dialects.postgresql import UUID


class Base(DeclarativeBase):
    pass


class Token(Base):
    __tablename__ = 'tokens'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False, index=True)
    hashed_token = Column(String(255), nullable=False, unique=True)
    scopes = Column(JSON, nullable=False)
    expires_at = Column(DateTime, nullable=True)
    is_revoked = Column(Boolean, nullable=False, server_default='false')
    owner_username = Column(String(80), nullable=True, index=True)
    allowed_ips = Column(JSON, default=list)
    allowed_targets = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    __table_args__ = (
        Index(
            '_owner_name_active_uc',
            'owner_username', 'name',
            unique=True,
            postgresql_where=text('is_revoked = false')
        ),
    )


class Scan(Base):
    __tablename__ = 'scans'

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    status = Column(String(50), nullable=False, server_default='queued')
    profile = Column(String(100), nullable=False)
    targets = Column(JSON, nullable=False)
    ports = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    callback_url = Column(String(2048), nullable=True)
    tags = Column(JSON, default=list)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    finished_at = Column(DateTime(timezone=True), nullable=True)
    result_xml = Column(Text, nullable=True)
    token_id = Column(Integer, ForeignKey('tokens.id'))
    token = relationship("Token")
