#!/usr/bin/env bash

set -Eeuo pipefail

echo "--- Reset completo e configuração da autonmap-api ---"
echo ""

echo "Criando novo .env e gerando segredos aleatórios..."
if [[ ! -f .env.example ]]; then
  echo "ERRO: .env.example não encontrado." >&2
  exit 1
fi
cp .env.example .env

API_SECRET_KEY=$(openssl rand -hex 32)
WEBHOOK_HMAC_SECRET=$(openssl rand -hex 32)
FLASK_SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -hex 16)

sed -i "s|API_SECRET_KEY=.*|API_SECRET_KEY=${API_SECRET_KEY}|" .env
sed -i "s|WEBHOOK_HMAC_SECRET=.*|WEBHOOK_HMAC_SECRET=${WEBHOOK_HMAC_SECRET}|" .env
sed -i "s|^SECRET_KEY=.*|SECRET_KEY=${FLASK_SECRET_KEY}|" .env
sed -i "s|^DB_PASSWORD=.*|DB_PASSWORD=${DB_PASSWORD}|" .env

read -rp "Informe uma lista de IPs/redes a serem permitidos no backend (ex: 192.168.0.0/24,10.0.0.0/8). Deixe em branco para permitir todos: " ALLOWLIST
if [[ -n "${ALLOWLIST}" ]]; then
  if grep -q '^GLOBAL_IP_ALLOWLIST=' .env; then
    sed -i "s|^GLOBAL_IP_ALLOWLIST=.*|GLOBAL_IP_ALLOWLIST=${ALLOWLIST}|" .env
  else
    echo "GLOBAL_IP_ALLOWLIST=${ALLOWLIST}" >> .env
  fi
else
  if grep -q '^GLOBAL_IP_ALLOWLIST=' .env; then
    sed -i "s|^GLOBAL_IP_ALLOWLIST=.*|GLOBAL_IP_ALLOWLIST=|" .env
  else
    echo "GLOBAL_IP_ALLOWLIST=" >> .env
  fi
fi
echo ".env configurado com segredos e allowlist."
echo ""

set -a
source .env
set +a

echo "Derrubando contêineres anteriores e removendo volumes..."
docker compose --env-file .env down --remove-orphans -v || true

rm -rf frontend/migrations || true

echo "Atualizando imagens e subindo serviços..."
# Faz o pull das imagens publicadas (backend, frontend, worker e nginx) e depois
# levanta os serviços em segundo plano. O parâmetro --build foi removido pois
# todas as imagens são obtidas do registro e não há necessidade de compilação local.
docker compose --env-file .env pull
docker compose --env-file .env up -d

echo "Esperando pelo Postgres..."
for i in {1..60}; do
  if docker compose --env-file .env exec -T db pg_isready -U "${DB_USER}" -d "${DB_NAME}" >/dev/null 2>&1; then
    echo "Postgres está pronto."
    break
  fi
  sleep 2
  if [[ $i -eq 60 ]]; then
    echo "Postgres não respondeu a tempo." >&2
    exit 1
  fi
done

echo "Aguardando conclusão das migrações..."
wait_for_exit() {
  local service=$1
  while true; do
    cid=$(docker compose --env-file .env ps -q "$service" || true)
    if [[ -z "$cid" ]]; then
      break
    fi
    state=$(docker inspect --format '{{.State.Status}}' "$cid" 2>/dev/null || echo "unknown")
    if [[ "$state" != "running" && "$state" != "created" && "$state" != "restarting" ]]; then
      break
    fi
    sleep 2
  done
}
wait_for_exit backend-migrate
wait_for_exit frontend-migrate
echo "Migrações concluídas."

echo "Criando usuário administrador no painel..."
echo "Responda às perguntas a seguir (nome, email, username, senha)."
docker compose --env-file .env exec frontend flask user create-admin

echo "Gerando token de administrador para a API..."
ADMIN_TOKEN=$(docker compose --env-file .env run --rm backend python -m scripts.create_admin_token | head -n1 | tr -d '[:space:]') || true
if [[ -z "${ADMIN_TOKEN}" ]]; then
  echo "Token não capturado automaticamente. Você poderá gerá-lo manualmente mais tarde."
else
  if grep -q '^API_ADMIN_TOKEN=' .env; then
    sed -i "s|^API_ADMIN_TOKEN=.*|API_ADMIN_TOKEN=${ADMIN_TOKEN}|" .env
  else
    echo "API_ADMIN_TOKEN=${ADMIN_TOKEN}" >> .env
  fi
  echo "Token de admin salvo no .env."
fi

echo "Reiniciando frontend para ler variáveis atualizadas..."
docker compose --env-file .env restart frontend

echo ""
echo "Setup concluído com sucesso!"
echo "- Acesse a interface em: http://localhost"
echo "- Utilize o usuário admin criado para fazer login."
echo "- O token de API foi salvo no .env como API_ADMIN_TOKEN."