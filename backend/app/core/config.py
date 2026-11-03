import os
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "CondoHub - Sistema de Gestão Condominial"
    SECRET_KEY: str = "sgc_super_secret_jwt_key_segura_para_desenvolvimento_e_producao"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120

    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASSWORD: str = "12345678"
    DB_NAME: str = "pim_iv_condominio"
    DATABASE_URL: str = "postgresql+asyncpg://postgres:12345678@localhost:5432/pim_iv_condominio"

    # Configurações de SMTP para Envio de E-mails Reais (Gmail)
    MAIL_SERVER: str = "smtp.gmail.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = "sistema.academico.pim@gmail.com"
    MAIL_PASSWORD: str = "rple kevp ihwz meso"
    MAIL_DEFAULT_SENDER: str = "sistema.academico.pim@gmail.com"
    MAIL_TLS: bool = True
    MAIL_SSL: bool = False
    MAIL_SENDER_NAME: str = "CondoHub"

    # Configurações de Segurança do Console / Diretoria (Whitelist de IPs)
    CONSOLE_ALLOWED_IPS: str = ""
    SUPERADMIN_ALLOWED_IPS: str = ""

    # Proxies Reversos Confiáveis (ex: "10.0.0.1,192.168.1.1"). Vazio = nenhum proxy confiável (ignora X-Forwarded-For)
    TRUSTED_PROXIES: str = ""

    model_config = SettingsConfigDict(
        env_file=os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )


settings: Settings = Settings()
