from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Notice(Base):
    __tablename__ = "avisos"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="RESTRICT"), nullable=False, default=1, index=True)
    titulo = Column(String(150), nullable=False)
    mensagem = Column(Text, nullable=False)
    categoria = Column(String(50), default="GERAL", nullable=False)  # GERAL, MANUTENCAO, URGENTE, ASSEMBLEIA
    link_anexo = Column(String(500), nullable=True)  # Links para Google Meet, Zoom, YouTube, etc.
    autor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False)
    ativo = Column(Boolean, default=True, nullable=False, index=True)  # Soft-hide / visibilidade no mural
    batch_id = Column(String(60), nullable=True, index=True)  # ID do lote de transmissão master
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    condominio = relationship("Condominio", back_populates="avisos")
    autor = relationship("User")

