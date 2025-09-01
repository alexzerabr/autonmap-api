from fastapi import FastAPI
from .routers import scans, admin, profiles
from .config import settings
from .security.ip_allowlist import IPAllowlistMiddleware

app = FastAPI(
    title="autonmap-api",
    description="API segura para orquestrar varreduras Nmap.",
    version="1.0.0",
    docs_url="/docs" if settings.DEBUG else None,
    redoc_url="/redoc" if settings.DEBUG else None,
)

# Adiciona o middleware de Allowlist de IP
app.add_middleware(IPAllowlistMiddleware)

# Inclui os roteadores da aplicação
app.include_router(scans.router)
app.include_router(admin.router)
app.include_router(profiles.router)

@app.get("/", tags=["Root"])
def read_root():
    return {"message": "autonmap-api is running"}
