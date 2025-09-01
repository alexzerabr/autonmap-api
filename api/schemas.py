from enum import Enum
from pydantic import BaseModel, Field, HttpUrl
from typing import List, Optional
from uuid import UUID
import datetime

# --- Enum para os Timing Templates do Nmap ---
class TimingTemplate(str, Enum):
    T0 = "T0" # Paranoid
    T1 = "T1" # Sneaky
    T2 = "T2" # Polite
    T3 = "T3" # Normal
    T4 = "T4" # Aggressive
    T5 = "T5" # Insane

# --- Enum de perfis ---
class ScanProfile(str, Enum):
    # Opção [1] do script
    BASIC_VERSION_DETECTION = "basic_version_detection"
    # Opção [2] do script
    AGGRESSIVE_SCAN = "aggressive_scan"
    
    # Opções [4] e [5] do script (TCP Connect Scan)
    VULN_TCP_EVASIVE = "vuln_tcp_evasive"
    
    # Opção [7] do script (SYN Scan Furtivo) - Requer privilégios
    VULN_SYN_STEALTH = "vuln_syn_stealth"
    
    # Opção [9] do script
    PROXY_VULN_SCAN = "proxy_vuln_scan"

# --- Modelo de Requisição de Scan ---
class ScanCreateRequest(BaseModel):
    targets: List[str] = Field(..., min_length=1, max_length=50)
    profile: ScanProfile
    ports: Optional[str] = Field(None, description="Ex: '1-1024' ou '80,443'. Se omitido, usa as portas padrão do Nmap.", pattern=r"^[0-9,-]+$")
    
    timing_template: Optional[TimingTemplate] = Field(TimingTemplate.T3, description="Velocidade e agressividade do scan (T0 a T5). Padrão: T3.")
    
    notes: Optional[str] = Field(None, max_length=512)
    callback_url: Optional[HttpUrl] = None
    tags: Optional[List[str]] = []

# --- Modelos de Resposta de Scan ---
class ScanResponse(BaseModel):
    id: UUID
    status: str
    profile: ScanProfile
    targets: List[str]
    created_at: datetime.datetime
    class Config:
        from_attributes = True

class ScanResultResponse(ScanResponse):
    started_at: Optional[datetime.datetime]
    finished_at: Optional[datetime.datetime]

# --- Schemas de Token ---
class TokenCreateRequest(BaseModel):
    name: str = Field(..., description="Um nome legível para o token")
    scopes: List[str] = Field(..., description="Lista de permissões")
    expires_in_days: Optional[int] = Field(30, description="Duração do token em dias")
    owner_username: Optional[str] = Field(None, description="Username do usuário do painel que é dono do token")

class TokenResponse(BaseModel):
    id: int
    name: str
    scopes: List[str]
    created_at: datetime.datetime
    expires_at: Optional[datetime.datetime]
    owner_username: Optional[str]
    class Config:
        from_attributes = True

class NewTokenResponse(BaseModel):
    token_details: TokenResponse
    api_token: str = Field(..., description="O token de API. Guarde-o em segurança.")

# --- Schema de Perfil ---
class ProfileResponse(BaseModel):
    name: str
    description: str
