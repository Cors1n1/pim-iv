from sqlalchemy import BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class User(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    email = Column(String(150), unique=True, index=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    telefone = Column(String(20), nullable=True)
    tipo_usuario = Column(String(20), nullable=False)  # 'ADMIN', 'SINDICO', 'PORTARIA', 'MORADOR'
    ativo = Column(Boolean, default=True, nullable=False)
    precisa_trocar_senha = Column(Boolean, default=False, nullable=False)
    unidade_id = Column(Integer, ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    logs = relationship("AccessLog", back_populates="usuario", cascade="all, delete-orphan")
    unidade = relationship("Unit", back_populates="moradores", foreign_keys=[unidade_id])


class Unit(Base):
    __tablename__ = "unidades"

    id = Column(Integer, primary_key=True, index=True)
    bloco = Column(String(20), nullable=False)
    numero = Column(String(20), nullable=False)
    andar = Column(Integer, nullable=True)
    morador_responsavel_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    morador_responsavel = relationship("User", foreign_keys=[morador_responsavel_id])
    moradores = relationship("User", back_populates="unidade", foreign_keys=[User.unidade_id])


class AccessLog(Base):
    __tablename__ = "logs_acesso"

    id = Column(BigInteger, primary_key=True, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    email_informado = Column(String(150), nullable=False)
    ip_origem = Column(String(45), nullable=True)
    user_agent = Column(Text, nullable=True)
    sucesso = Column(Boolean, nullable=False)
    data_hora = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    usuario = relationship("User", back_populates="logs")

