from datetime import datetime
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from app.core.database import Base


class ReservationGuest(Base):
    __tablename__ = "convidados_reserva"

    id = Column(Integer, primary_key=True, index=True)
    reserva_id = Column(Integer, ForeignKey("reservas.id", ondelete="CASCADE"), nullable=False, index=True)
    nome_completo = Column(String(150), nullable=False)
    documento = Column(String(50), nullable=True)
    email = Column(String(150), nullable=True)
    convite_enviado = Column(Boolean, nullable=False, default=False)
    entrada_registrada = Column(Boolean, nullable=False, default=False)
    entrada_em = Column(DateTime(timezone=True), nullable=True)
    saida_registrada = Column(Boolean, nullable=False, default=False)
    saida_em = Column(DateTime(timezone=True), nullable=True)
    criado_em = Column(DateTime(timezone=True), default=datetime.utcnow)

    reserva = relationship("Reservation", back_populates="guests")
