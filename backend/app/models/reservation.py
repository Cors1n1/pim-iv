from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, Numeric, String, Text, Time, func
from sqlalchemy.orm import relationship

from app.core.database import Base
from app.models.guest import ReservationGuest


class CommonArea(Base):
    __tablename__ = "areas_comuns"

    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), nullable=False)
    descricao = Column(Text, nullable=True)
    capacidade_pessoas = Column(Integer, nullable=False)
    taxa_limpeza = Column(Numeric(10, 2), default=0.00, nullable=False)
    hora_inicio = Column(Time, default="08:00:00", nullable=False)
    hora_fim = Column(Time, default="22:00:00", nullable=False)
    duracao_maxima_horas = Column(Integer, default=4, nullable=False)
    intervalo_dias_prioridade = Column(Integer, default=30, nullable=False)
    max_reservas_ativas = Column(Integer, default=2, nullable=False)
    prazo_standby_horas = Column(Integer, default=48, nullable=False)
    ativo = Column(Boolean, default=True, nullable=False)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    reservas = relationship("Reservation", back_populates="area_comum", cascade="all, delete-orphan")


class Reservation(Base):
    __tablename__ = "reservas"

    id = Column(Integer, primary_key=True, index=True)
    area_comum_id = Column(Integer, ForeignKey("areas_comuns.id", ondelete="CASCADE"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True)
    unidade_id = Column(Integer, ForeignKey("unidades.id", ondelete="SET NULL"), nullable=True)
    data_reserva = Column(Date, nullable=False, index=True)
    hora_inicio = Column(Time, default="08:00:00", nullable=False)
    hora_fim = Column(Time, default="12:00:00", nullable=False)
    status = Column(String(20), default="CONFIRMADA", nullable=False, index=True)
    prioridade = Column(String(20), default="ALTA", nullable=False, index=True)
    prioridade_queimada = Column(Boolean, default=False, nullable=False)
    oferta_retomada_ate = Column(DateTime(timezone=True), nullable=True)
    observacoes = Column(Text, nullable=True)
    chave_entregue = Column(Boolean, default=False, nullable=False)
    chave_entregue_por = Column(Integer, ForeignKey("usuarios.id", ondelete="SET NULL"), nullable=True)
    chave_entregue_para = Column(String(150), nullable=True)
    chave_entregue_em = Column(DateTime(timezone=True), nullable=True)
    chave_devolvida = Column(Boolean, default=False, nullable=False)
    chave_devolvida_em = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    atualizado_em = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    area_comum = relationship("CommonArea", back_populates="reservas")
    usuario = relationship("User", foreign_keys=[usuario_id])
    porteiro_chave = relationship("User", foreign_keys=[chave_entregue_por])
    unidade = relationship("Unit")
    guests = relationship("ReservationGuest", back_populates="reserva", cascade="all, delete-orphan", lazy="selectin")

