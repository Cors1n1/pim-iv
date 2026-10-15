from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.core.database import Base


class CondoSettings(Base):
    __tablename__ = "configuracoes_condominio"

    id = Column(Integer, primary_key=True, index=True)
    nome_condominio = Column(String(150), nullable=False, default="Condomínio Residencial")
    endereco = Column(String(255), nullable=True, default="Rua das Flores, 123 - Centro")
    telefone_portaria = Column(String(50), nullable=True, default="(11) 98765-4321")
    email_contato = Column(String(100), nullable=True, default="contato@condominio.com")
    prazo_retomada_horas = Column(Integer, nullable=False, default=24)
    prazo_standby_horas = Column(Integer, nullable=False, default=48)
    intervalo_padrao_dias = Column(Integer, nullable=False, default=30)
    dias_penalidade_queima = Column(Integer, nullable=False, default=30)
    queima_prioridade_cancelamento = Column(Boolean, nullable=False, default=True)
    enviar_email_ativo = Column(Boolean, nullable=False, default=True)
    atualizado_em = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
