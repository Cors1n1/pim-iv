from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict


class AuditLogResponse(BaseModel):
    id: int
    usuario_id: Optional[int] = None
    email_informado: str
    ip_origem: Optional[str] = None
    user_agent: Optional[str] = None
    sucesso: bool
    data_hora: datetime

    model_config = ConfigDict(from_attributes=True)
