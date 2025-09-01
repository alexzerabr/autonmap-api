
# autonmap-api

API REST segura para orquestrar varreduras Nmap, de modo automático e gerenciado via token.

Este projeto fornece uma solução completa para execução de scans Nmap de forma assíncrona, com endpoints protegidos, painel de administração com autenticação 2FA e fila de tarefas baseada em Redis. A infraestrutura foi desenhada para rodar em produção via Docker Compose, utilizando Nginx como proxy reverso e PostgreSQL 16 como banco de dados. As imagens de contêiner são publicadas no **GitHub Container Registry (GHCR)**.

## ✨ Funcionalidades Principais

### API Backend (FastAPI)
- Endpoints seguros para criar, monitorar e consultar resultados de scans.
- Execução assíncrona com RQ + Redis.

### Painel de Administração (Flask)
- Gerenciamento de usuários com 2FA.
- Geração e revogação de tokens de acesso à API.
- Visualização de documentação da API e histórico de scans.

### Segurança
- Tokens com escopos configuráveis.
- 2FA com TOTP e códigos de backup.
- Allowlist de IPs configurável.
- CSP configurada no Nginx.

### Execução Assíncrona
- Scans processados em workers separados, liberando a API rapidamente.

### Ambiente Containerizado
- Toda a stack orquestrada via Docker Compose.

### Scripts Automatizados
- `setup.sh` recompõe o ambiente do zero, gera segredos, cria admin e token inicial.

## 🚀 Como Executar em Produção

### Pré-requisitos
- Docker (20.10+) e Docker Compose (v2).
- `openssl`.

### Método Automatizado
```bash
git clone https://github.com/alexzerabr/autonmap-api.git
cd autonmap-api
chmod +x setup.sh
./setup.sh
```

Painel: [http://localhost](http://localhost)  
API Swagger: [http://localhost/api/docs](http://localhost/api/docs)

### Método Manual

Remover containers/volumes antigos:
```bash
docker compose down -v --remove-orphans || true
```

Criar `.env` a partir de `.env.example` e preencher variáveis:
```bash
cp .env.example .env
# edite .env conforme necessário (DB_USER, DB_PASSWORD, API_SECRET_KEY, etc.)
```

Baixar as imagens publicadas:
```bash
docker compose --env-file .env pull
```

Subir os serviços:
```bash
docker compose --env-file .env up -d
```

Criar usuário administrador no painel:
```bash
docker compose exec frontend flask user create-admin
```

Gerar token de API e adicionar ao `.env`:
```bash
docker compose exec backend python -m scripts.create_admin_token --name super-admin-inicial
# copie o token gerado e salve em API_ADMIN_TOKEN no .env, depois:
docker compose restart frontend
```

## 🧪 Cliente de Linha de Comando
```bash
export AUTONMAP_API_URL=http://localhost/api
export AUTONMAP_API_TOKEN=<seu_token>

python3 scan_cli.py
```

## 🔄 Troubleshooting
- **Erro 500/403 em tokens**: Verifique `API_ADMIN_TOKEN` no `.env` e `GLOBAL_IP_ALLOWLIST`.
- **2FA QR não aparece**: Ajustar CSP no Nginx.
- **API 404 no CLI**: Certifique-se de usar `/api` no endpoint.
- **Redis memória**: Habilitar `vm.overcommit_memory=1` no host.

## 📁 Estrutura do Projeto
- `api/` – Backend FastAPI.
- `frontend/` – Painel Flask.
- `deploy/` – Dockerfiles, configs e Nginx.
- `scan_cli.py` – Cliente CLI.
- `docker-compose.yml` – Orquestração da stack.
- `setup.sh` – Setup automatizado.
- `.env.example` – Exemplo de configuração.

## 🤝 Contribuições
Contribuições são bem-vindas! Abra issues ou PRs com melhorias.