import getpass
from werkzeug.security import generate_password_hash

def main():
    """
    Solicita uma senha de forma segura e imprime seu hash, já formatado para o .env.
    """
    print("--- Gerador de Hash de Senha para o Painel Admin ---")
    password = getpass.getpass("Digite a senha do admin: ")
    password_confirm = getpass.getpass("Confirme a senha do admin: ")

    if password != password_confirm:
        print("\nAs senhas não coincidem. Abortando.")
        return

    if not password:
        print("\nSenha não pode ser vazia. Abortando.")
        return

    hashed_password = generate_password_hash(password)

    print("\n--- HASH GERADO ---")
    print("Copie a linha abaixo e cole no seu arquivo .env para a variável ADMIN_PASSWORD_HASH:")
    print(f"'{hashed_password}'")
    print("-------------------")

if __name__ == "__main__":
    main()
