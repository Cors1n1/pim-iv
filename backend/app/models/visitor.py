from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Visitor(Base):
    __tablename__ = "visitantes"

    id = Column(Integer, primary_key=True, index=True)
    condominio_id = Column(Integer, ForeignKey("condominios.id", ondelete="RESTRICT"), nullable=False, default=1, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True)
    autorizado_por_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    nome = Column(String(150), nullable=False)
    documento = Column(String(30), nullable=True)
    tipo = Column(String(30), default="VISITANTE", nullable=False)  # VISITANTE, PRESTADOR_SERVICO, DELIVERY
    data_prevista = Column(Date, nullable=False, index=True)
    status = Column(String(30), default="AGUARDANDO", nullable=False, index=True)  # AGUARDANDO, NO_LOCAL, FINALIZADO, CANCELADO
    hora_entrada = Column(DateTime(timezone=True), nullable=True)
    porteiro_entrada_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    hora_saida = Column(DateTime(timezone=True), nullable=True)
    porteiro_saida_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    observacoes = Column(Text, nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    condominio = relationship("Condominio", back_populates="visitantes")
    unidade = relationship("Unit")
    morador = relationship("User", foreign_keys=[autorizado_por_id])
    porteiro_entrada = relationship("User", foreign_keys=[porteiro_entrada_id])
    porteiro_saida = relationship("User", foreign_keys=[porteiro_saida_id])
