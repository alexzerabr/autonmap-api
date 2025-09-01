from fastapi import APIRouter
from typing import List
from ..schemas import ScanProfile, ProfileResponse

router = APIRouter(prefix="/v1/profiles", tags=["Profiles"])

PROFILE_DESCRIPTIONS = {
    "version_detect": "Detecção de versão de serviços (-sV). Rápido e útil.",
    "aggressive": "Varredura agressiva (-A) com detecção de OS, versão e scripts.",
    "vuln": "Verifica vulnerabilidades conhecidas usando scripts da categoria 'vuln'.",
    "full_ports": "Varredura completa de todas as 65535 portas TCP com detecção de serviços.",
    "evasion": "Usa técnicas de evasão para evitar detecção por firewalls simples.",
    "proxychains_full": "Varredura completa através de um proxy (requer configuração)."
}

@router.get("/", response_model=List[ProfileResponse])
def get_supported_profiles():
    profiles = []
    for profile in ScanProfile:
        profiles.append(
            ProfileResponse(
                name=profile.value,
                description=PROFILE_DESCRIPTIONS.get(profile.value, "Sem descrição.")
            )
        )
    return profiles
