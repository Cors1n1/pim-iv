from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.core.database import Base


class CondoSettings(Base):
    __tablename__ = "configuracoes_condominio"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="CASCADE"), nullable=False, unique=True, index=True, default=1)
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

    condominio = relationship("Condominio", back_populates="configuracao")


class PlatformSettings(Base):
    __tablename__ = "configuracoes_plataforma"

    id = Column(Integer, primary_key=True, index=True, default=1)
    suporte_email = Column(String(150), nullable=False, default="suporte@condohub.com.br")
    suporte_telefone = Column(String(50), nullable=False, default="(11) 98765-4321")
    suporte_horario = Column(String(100), nullable=True, default="Segunda a Sexta, das 08h às 18h")
    titulo_regularizacao = Column(String(150), nullable=True, default="O que fazer para regularizar?")
    mensagem_regularizacao = Column(
        Text,
        nullable=True,
        default="Para restabelecer o acesso ao portal, o síndico ou responsável predial deve entrar em contato com nossa equipe de atendimento:\n• Verifique eventuais pendências administrativas, cadastrais ou contratuais.\n• Após a regularização, a liberação dos acessos é realizada em tempo real."
    )
    titulo_suspensao = Column(String(150), nullable=True, default="Acesso ao Condomínio Suspenso")
    subtitulo_suspensao = Column(String(255), nullable=True, default="O acesso ao portal do seu condomínio foi temporariamente pausado pela administração central.")
    atualizado_em = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)
