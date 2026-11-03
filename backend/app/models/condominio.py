from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Condominio(Base):
    __tablename__ = "condominios"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), nullable=False)
    slug = Column(String(100), unique=True, index=True, nullable=True)
    cnpj = Column(String(20), unique=True, nullable=True)
    endereco = Column(String(255), nullable=True)
    telefone = Column(String(50), nullable=True)
    email_contato = Column(String(150), nullable=True)
    plano = Column(String(50), default="PRO", nullable=False)  # 'BASICO', 'PRO', 'ENTERPRISE'
    limite_unidades = Column(Integer, default=100, nullable=False)
    status = Column(String(20), default="ATIVO", nullable=False)  # 'ATIVO', 'BLOQUEADO', 'CANCELADO'
    motivo_bloqueio = Column(String(255), nullable=True)
    cor_primaria = Column(String(20), default="#2563eb", nullable=False)
    cor_secundaria = Column(String(20), default="#1d4ed8", nullable=False)
    cor_sidebar = Column(String(20), default="#09090b", nullable=False)
    cor_fundo = Column(String(20), default="AUTO", nullable=True)
    tipo_gestao = Column(String(30), default="AUTOGESTAO", nullable=False)  # 'AUTOGESTAO', 'COMPARTILHADA'
    administradora_nome = Column(String(150), nullable=True)
    administradora_email = Column(String(150), nullable=True)
    logo_url = Column(String(255), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    usuarios = relationship("User", back_populates="condominio")
    unidades = relationship("Unit", back_populates="condominio")
    areas_comuns = relationship("CommonArea", back_populates="condominio")
    configuracao = relationship("CondoSettings", back_populates="condominio", uselist=False)
    encomendas = relationship("Delivery", back_populates="condominio")
    avisos = relationship("Notice", back_populates="condominio")
    ocorrencias = relationship("Ticket", back_populates="condominio")
    visitantes = relationship("Visitor", back_populates="condominio")
