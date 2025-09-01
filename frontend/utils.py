import re

def is_strong_password(password: str) -> bool:
    """
    Valida a força da senha.
    Requisitos:
    - Mínimo de 8 caracteres
    - Pelo menos um símbolo (caractere não alfanumérico)
    """
    if len(password) < 8:
        return False
    
    if not re.search(r'[^a-zA-Z0-9]', password):
        return False
        
    return True
