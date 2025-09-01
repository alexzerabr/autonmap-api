# scripts/create_admin_token.py
import sys
import secrets
import argparse

from api.db.session import SessionLocal
from api.db.models import Token
from api.security.auth import hash_token


def issue_admin_token(name: str, force: bool) -> int:
    """
    Cria (ou rotaciona, se --force) um token de administrador.
    - Mensagens informativas/decorativas vão para STDERR.
    - O token cru (única linha) vai para STDOUT.

    Retorna 0 em sucesso; encerra com código != 0 em erro.
    """
    db = SessionLocal()
    try:
        scopes = ['admin:read', 'admin:write', 'scan:read', 'scan:write']

        existing = db.query(Token).filter(Token.name == name).first()

        if existing and not force:
            print(
                f"Token '{name}' já existe. Nenhum token novo foi criado.",
                file=sys.stderr,
                flush=True,
            )
            return 0

        # Gera token novo
        admin_token_raw = secrets.token_urlsafe(32)
        hashed = hash_token(admin_token_raw)

        if existing and force:
            existing.hashed_token = hashed
            existing.scopes = scopes
        else:
            db_token = Token(
                name=name,
                hashed_token=hashed,
                scopes=scopes,
            )
            db.add(db_token)

        db.commit()

        # Cabeçalho e rodapé no STDERR
        print('--- ADMIN TOKEN GERADO (NUNCA EXPIRA) ---', file=sys.stderr, flush=True)
        print('Guarde este token em um local seguro. Ele só será exibido uma vez:', file=sys.stderr, flush=True)

        print(admin_token_raw, flush=True)

        print('-----------------------------------------', file=sys.stderr, flush=True)
        return 0

    except Exception as e:
        db.rollback()
        print(f'Erro ao criar/rotacionar o token: {e}', file=sys.stderr, flush=True)
        sys.exit(1)
    finally:
        db.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Cria ou rotaciona o primeiro token de administrador.")
    parser.add_argument(
        "--name",
        default="super-admin-inicial",
        help="Nome do token (chave única para evitar duplicadas). Padrão: super-admin-inicial",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Se existir, rotaciona o token (gera outro valor e atualiza o hash).",
    )
    args = parser.parse_args()

    rc = issue_admin_token(name=args.name, force=args.force)
    sys.exit(rc)


if __name__ == "__main__":
    main()
