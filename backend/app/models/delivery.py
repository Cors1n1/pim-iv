from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.orm import relationship

from app.core.database import Base


class Delivery(Base):
    __tablename__ = "encomendas"

    id = Column(Integer, primary_key=True, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id", ondelete="CASCADE"), nullable=False, index=True)
    descricao = Column(String(255), nullable=False)
    codigo_rastreio = Column(String(100), nullable=True)
    porteiro_recebedor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    status = Column(String(30), default="AGUARDANDO_RETIRADA", nullable=False, index=True)
    data_chegada = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    data_retirada = Column(DateTime(timezone=True), nullable=True)
    retirado_por = Column(String(150), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    unidade = relationship("Unit", backref="encomendas")
    porteiro = relationship("User", foreign_keys=[porteiro_recebedor_id])
