import os
import re
import secrets


AMBIENTE = os.getenv("APP_ENV", "development").strip().lower()
EM_PRODUCAO = AMBIENTE == "production"

SEGREDOS_INVALIDOS = {
    "chave_forte_e_aleatoria",
    "troque_esta_chave_em_producao",
    "troque_por_uma_chave_grande_e_aleatoria",
}

CREDENCIAIS_ADMIN_INVALIDAS = {
    "admin123",
    "admin1234",
    "password",
    "senha123",
}


def obter_secret_key() -> str:
    valor = os.getenv("SECRET_KEY", "").strip()
    invalido = len(valor) < 32 or valor.lower() in SEGREDOS_INVALIDOS
    if not invalido:
        return valor
    if os.getenv("APP_ENV", "development").strip().lower() == "production":
        raise RuntimeError(
            "SECRET_KEY ausente ou insegura. Defina uma chave aleatoria com pelo menos 32 caracteres."
        )
    return secrets.token_urlsafe(48)


def obter_admin_inicial() -> tuple[str, str, str]:
    email = os.getenv("ADMIN_EMAIL", "").strip()
    senha = os.getenv("ADMIN_PASSWORD", "")
    nome = os.getenv("ADMIN_NAME", "Administrador").strip() or "Administrador"

    if not email or "@" not in email or not senha:
        raise RuntimeError(
            "Banco sem usuarios. Defina ADMIN_EMAIL e ADMIN_PASSWORD para criar o administrador inicial."
        )
    if email.lower() == "admin@teste.com" or senha.lower() in CREDENCIAIS_ADMIN_INVALIDAS:
        raise RuntimeError("As credenciais do administrador inicial nao podem usar valores de exemplo.")
    if len(senha) < 8 or not re.search(r"[A-Za-z]", senha) or not re.search(r"\d", senha):
        raise RuntimeError("ADMIN_PASSWORD deve ter pelo menos 8 caracteres, com letras e numeros.")
    if len(senha.encode("utf-8")) > 72:
        raise RuntimeError("ADMIN_PASSWORD nao pode ter mais de 72 bytes.")

    return email, senha, nome


SECRET_KEY = obter_secret_key()
