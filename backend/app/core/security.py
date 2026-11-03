import re
import unicodedata
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional
import bcrypt
from jose import JWTError, jwt

from app.core.config import settings


def slugify(text: str) -> str:
    """Gera slug limpo e amigável para URL a partir do nome informado."""
    normalized = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('ascii')
    cleaned = re.sub(r'[^\w\s-]', '', normalized).strip().lower()
    return re.sub(r'[-\s]+', '-', cleaned)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica se uma senha em texto puro corresponde ao hash Bcrypt."""
    try:
        return bcrypt.checkpw(
            plain_password.encode("utf-8"),
            hashed_password.encode("utf-8")
        )
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    """Gera um hash Bcrypt seguro para a senha."""
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def create_access_token(data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
    """Gera um token JWT com tempo de expiração definido."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)
    return encoded_jwt


def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica e valida a assinatura e validade do token JWT."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        return payload
    except JWTError:
        return None


def create_activation_token(user_id: int, condominio_id: int, email: str, days: int = 7, scope: str = "sindico_activation") -> str:
    """Gera um token criptográfico para o link de convite e ativação do primeiro síndico ou gestor de administradora."""
    return create_access_token(
        data={
            "sub": str(user_id),
            "condominio_id": condominio_id,
            "email": email.strip().lower(),
            "scope": scope
        },
        expires_delta=timedelta(days=days)
    )


def decode_activation_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica e valida o token exclusivo de primeiro acesso e ativação (síndico ou administradora)."""
    payload = decode_access_token(token)
    if not payload or payload.get("scope") not in ("sindico_activation", "admin_activation", "subsindico_activation"):
        return None
    return payload


COMMON_WEAK_PASSWORDS = {
    "123456", "12345678", "123456789", "password", "senha123", "senha1234",
    "condominio", "condohub", "admin123", "mudar123", "qwerty", "qwerty123",
    "portaria", "morador", "sindico", "brasil", "master"
}


def validate_strong_password(password: str) -> str:
    """
    Validador de complexidade de senha:
    - Mínimo de 8 caracteres
    - Pelo menos 1 caractere maiúsculo (A-Z)
    - Pelo menos 1 caractere minúsculo (a-z)
    - Pelo menos 1 número (0-9)
    - Pelo menos 1 símbolo especial (!@#$%^&*...)
    - Rejeição de senhas comuns/óbvias
    """
    if len(password) < 8:
        raise ValueError("A senha deve ter no mínimo 8 caracteres.")
    if password.lower() in COMMON_WEAK_PASSWORDS:
        raise ValueError("Senha muito comum ou previsível. Escolha uma senha mais segura.")
    if not re.search(r"[A-Z]", password):
        raise ValueError("A senha deve conter pelo menos uma letra maiúscula (A-Z).")
    if not re.search(r"[a-z]", password):
        raise ValueError("A senha deve conter pelo menos uma letra minúscula (a-z).")
    if not re.search(r"\d", password):
        raise ValueError("A senha deve conter pelo menos um número (0-9).")
    if not re.search(r"[!@#$%^&*()_+\-=\[\]{}|;:,.<>?/~`]", password):
        raise ValueError("A senha deve conter pelo menos um caractere especial (!@#$%^&*...).")
    return password


def sanitize_text(content: Optional[str]) -> Optional[str]:
    """
    Sanitiza strings de entrada para evitar injeção de HTML e scripts.
    Converte caracteres perigosos (<, >, &, \", \') em entidades seguras.
    """
    import html
    if content is None:
        return None
    return html.escape(content.strip(), quote=True)


def get_client_ip(request: Any) -> str:
    """
    Extrai o endereço IP do cliente considerando proxies configurados.
    
    1. O IP de conexão direta (socket TCP: request.client.host) é usado por padrão.
    2. Cabeçalhos como X-Forwarded-For ou X-Real-IP só são considerados
       se a conexão direta provier de um proxy listado em settings.TRUSTED_PROXIES.
    3. Valida se a string extraída é um endereço IP válido.
    """
    import ipaddress
    client = getattr(request, "client", None)
    if not client or not getattr(client, "host", None):
        return "unknown"

    direct_ip = client.host.strip()
    trusted_str = (settings.TRUSTED_PROXIES or "").strip()

    if not trusted_str:
        return direct_ip

    trusted_proxies = {p.strip() for p in trusted_str.split(",") if p.strip()}
    if direct_ip not in trusted_proxies:
        return direct_ip

    # Se o IP direto for um proxy confiável, inspeciona headers de encaminhamento
    headers = getattr(request, "headers", {})
    forwarded = headers.get("x-forwarded-for")
    if forwarded:
        parts = [p.strip() for p in forwarded.split(",") if p.strip()]
        for candidate in reversed(parts):
            try:
                ip_obj = ipaddress.ip_address(candidate)
                if candidate not in trusted_proxies:
                    return str(ip_obj)
            except ValueError:
                continue
        if parts:
            try:
                return str(ipaddress.ip_address(parts[0]))
            except ValueError:
                pass

    real_ip = headers.get("x-real-ip") or headers.get("cf-connecting-ip")
    if real_ip:
        try:
            return str(ipaddress.ip_address(real_ip.strip()))
        except ValueError:
            pass

    return direct_ip


