# autonmap-api

API REST segura para orquestrar varreduras Nmap, de modo automático e gerenciado via token.

Este projeto fornece uma solução completa para execução de scans Nmap de forma assíncrona, com endpoints protegidos, painel de administração com autenticação 2FA e fila de tarefas baseada em Redis. A infraestrutura foi desenhada para rodar em produção via Docker Compose, utilizando Nginx como proxy reverso, PostgreSQL 16 como banco de dados.

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

### Pré‑requisitos
- Docker (20.10+) e Docker Compose (v2).
- `openssl`.
- Opcional: `make`.

### Método Automatizado
```bash
git clone https://github.com/alexzerabr/autonmap-api.git
cd autonmap-api
chmod +x setup.sh
./setup.sh
```

- Painel: http://localhost  
- API Swagger: http://localhost/api/docs  

### Método Manual
1. Remover containers/volumes antigos.
2. Criar `.env` a partir de `.env.example` e preencher variáveis.
3. Subir os serviços com:
   ```bash
   docker compose --env-file .env up -d --build
   ```
4. Criar usuário administrador:
   ```bash
   docker compose exec frontend flask user create-admin
   ```
5. Gerar token de API e adicionar ao `.env`:
   ```bash
   docker compose exec backend python -m scripts.create_admin_token --name super-admin-inicial
   ```
6. Reiniciar frontend:
   ```bash
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
Contribuições são bem‑vindas! Abra issues ou PRs com melhorias.
