from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Ticket(Base):
    __tablename__ = "ocorrencias"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="RESTRICT"), nullable=False, default=1, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    titulo = Column(String(150), nullable=False)
    descricao = Column(Text, nullable=False)
    categoria = Column(String(50), default="GERAL", nullable=False)  # BARULHO, MANUTENCAO, VAZAMENTO, SEGURANCA, OUTROS
    status = Column(String(30), default="ABERTO", nullable=False, index=True)  # ABERTO, EM_ANALISE, CONCLUIDO, CANCELADO
    resposta_sindico = Column(Text, nullable=True)
    respondido_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    respondido_em = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    condominio = relationship("Condominio", back_populates="ocorrencias")
    unidade = relationship("Unit")
    usuario = relationship("User", foreign_keys=[usuario_id])
    sindico = relationship("User", foreign_keys=[respondido_por])
