from typing import List, Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.notice import Notice
from app.models.user import User
from app.repositories.notice_repository import NoticeRepository
from app.schemas.notice import NoticeCreate, NoticeResponse


class NoticeService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = NoticeRepository(db)

    async def list_notices(
        self,
        current_user: Optional[User] = None,
        condominio_id: Optional[int] = None
    ) -> List[NoticeResponse]:
        """Lista todos os avisos do condomínio para visualização pública dos condôminos."""
        condo_id = condominio_id or (current_user.condominio_id if current_user else None)
        notices = await self.repo.list_all(condominio_id=condo_id)
        return [
            NoticeResponse(
                id=n.id,
                titulo=n.titulo,
                mensagem=n.mensagem,
                categoria=n.categoria,
                link_anexo=n.link_anexo,
                autor_id=n.autor_id,
                autor_nome=n.autor.nome if n.autor else "Administração",
                criado_em=n.criado_em,
                atualizado_em=n.atualizado_em
            )
            for n in notices
        ]

    async def create_notice(self, current_user: User, data: NoticeCreate) -> NoticeResponse:
        """Cria um novo aviso oficial (exclusivo para Síndico ou Administrador do condomínio)."""
        if current_user.tipo_usuario not in ["ADMIN", "SINDICO"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o síndico ou administrador podem publicar avisos oficiais."
            )

        cat = data.categoria.upper().strip()
        if cat not in ["GERAL", "MANUTENCAO", "URGENTE", "ASSEMBLEIA"]:
            cat = "GERAL"

        link_clean = None
        if data.link_anexo and data.link_anexo.strip():
            raw_link = data.link_anexo.strip()
            # Bloqueia vetores de XSS
            lower_link = raw_link.lower()
            if lower_link.startswith("javascript:") or lower_link.startswith("data:"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Esquema de URL inválido ou não seguro."
                )
            if not (lower_link.startswith("http://") or lower_link.startswith("https://")):
                raw_link = f"https://{raw_link}"
            link_clean = raw_link

        from app.core.security import sanitize_text

        notice = Notice(
            condominio_id=current_user.condominio_id,
            titulo=sanitize_text(data.titulo),
            mensagem=sanitize_text(data.mensagem),
            categoria=cat,
            link_anexo=link_clean,
            autor_id=current_user.id
        )

        created = await self.repo.create(notice)
        return NoticeResponse(
            id=created.id,
            titulo=created.titulo,
            mensagem=created.mensagem,
            categoria=created.categoria,
            link_anexo=created.link_anexo,
            autor_id=created.autor_id,
            autor_nome=current_user.nome,
            criado_em=created.criado_em,
            atualizado_em=created.atualizado_em
        )

    async def delete_notice(self, current_user: User, notice_id: int) -> dict:
        """Exclui um aviso do mural verificando condomínio de origem."""
        if current_user.tipo_usuario not in ["ADMIN", "SINDICO"]:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Apenas o síndico ou administrador podem remover avisos."
            )

        notice = await self.repo.get_by_id(notice_id, condominio_id=current_user.condominio_id)
        if not notice:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comunicado não encontrado ou pertence a outro condomínio."
            )

        await self.repo.delete(notice)
        return {"detail": "Comunicado removido com sucesso."}
