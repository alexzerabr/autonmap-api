# autonmap-api

API REST segura para orquestrar varreduras Nmap, de modo automático e
gerenciado via token.

Este projeto fornece uma solução completa para execução de scans Nmap de
forma assíncrona, com endpoints protegidos, painel de administração com
autenticação 2FA e fila de tarefas baseada em Redis. A infraestrutura
foi redesenhada para rodar em produção via Docker Compose, utilizando
Nginx como proxy reverso, PostgreSQL 16 como banco de dados e um único
arquivo .env para configuração.

✨ **Funcionalidades Principais**

### API Backend (FastAPI)

-   Endpoints seguros para criar, monitorar e consultar resultados de
    scans.\
-   Respostas assíncronas com filas de tarefas (RQ + Redis).

### Painel de Administração (Flask)

-   Criar e gerenciar usuários (com 2FA opcional);\
-   Gerar e revogar tokens de acesso à API;\
-   Visualizar documentação da API e histórico de scans.

### Segurança por Padrão

-   Permissões baseadas em escopos de token;\
-   Senhas fortes e 2FA (TOTP + códigos de backup);\
-   Allowlist de IPs configurável via `.env`;\
-   Política de segurança de conteúdo (CSP) no Nginx.

### Execução Assíncrona

-   Scans processados por worker separado, liberando a API rapidamente.

### Ambiente Containerizado

-   Orquestração com Docker Compose (API, painel, worker, DB, cache e
    proxy).

### Scripts Automatizados

-   `setup.sh` recompõe todo o ambiente, gera segredos, cria usuário
    admin e token inicial.

------------------------------------------------------------------------

## 🚀 Como Executar em Produção

### Pré‑requisitos

-   Docker (20.10+) e Docker Compose (v2);\
-   `openssl` para geração de segredos;\
-   Opcional: `make`.

### Método Automatizado

``` bash
git clone https://github.com/alexzerabr/autonmap-api.git
cd autonmap-api
chmod +x setup.sh
./setup.sh
```

-   Painel: <http://localhost>\
-   API Docs (Swagger): <http://localhost/api/docs>

### Método Manual (Passo a Passo)

``` bash
docker compose down --remove-orphans -v
docker volume rm autonmap-api_postgres_data || true
rm -rf frontend/migrations || true

cp .env.example .env
# Editar API_SECRET_KEY, DB_USER, DB_PASSWORD, GLOBAL_IP_ALLOWLIST etc.

docker compose --env-file .env up -d --build

docker compose exec frontend flask user create-admin
docker compose exec backend python -m scripts.create_admin_token --name super-admin-inicial

docker compose restart frontend
```

------------------------------------------------------------------------

## 🛠️ Cliente de Linha de Comando (scan_cli.py)

``` bash
export AUTONMAP_API_URL=http://localhost/api
export AUTONMAP_API_TOKEN=<seu_token>
python3 scan_cli.py
```

------------------------------------------------------------------------

## 🔄 Troubleshooting

-   **Token retorna 500/403** → Verifique `API_ADMIN_TOKEN` no `.env`.\
-   **QR Code 2FA não aparece** → Ajustar CSP no Nginx.\
-   **API responde 404 no CLI** → Verifique `AUTONMAP_API_URL` com
    `/api`.\
-   **Redis memory error** → Ativar `vm.overcommit_memory=1`.

------------------------------------------------------------------------

## 📁 Estrutura do Projeto

-   `api/` -- Backend FastAPI\
-   `frontend/` -- Painel Flask\
-   `deploy/` -- Dockerfiles e Nginx\
-   `scan_cli.py` -- Cliente CLI\
-   `docker-compose.yml` -- Orquestração\
-   `setup.sh` -- Script de setup\
-   `.env.example` -- Exemplo de configuração

------------------------------------------------------------------------

## 🤝 Contribuições

Contribuições são bem‑vindas! Abra issues ou pull requests com
melhorias.
