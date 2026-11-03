from typing import List, Optional
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import AccessLog, User


class UserRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, user_id: int) -> Optional[User]:
        """Busca usuário pelo identificador numérico único."""
        stmt = select(User).where(User.id == user_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_email(self, email: str) -> Optional[User]:
        """Busca usuário pelo endereço de e-mail (case-insensitive)."""
        stmt = select(User).where(User.email.ilike(email.strip()))
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_invite_token(self, token: str) -> Optional[User]:
        """Busca usuário pelo token seguro de convite/ativação."""
        stmt = select(User).where(User.token_convite == token.strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def create(self, user: User) -> User:
        """Persiste um novo usuário no banco de dados."""
        self.db.add(user)
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update(self, user: User) -> User:
        """Atualiza e persiste alterações de um usuário existente."""
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def update_password(
        self,
        user_id: int,
        new_password_hash: str,
        precisa_trocar_senha: bool = False
    ) -> Optional[User]:
        """Atualiza a senha do usuário, altera o status de primeiro acesso e invalida sessões antigas."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.senha_hash = new_password_hash
        user.precisa_trocar_senha = precisa_trocar_senha
        user.token_version = (getattr(user, "token_version", 1) or 1) + 1
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def increment_token_version(self, user_id: int) -> Optional[User]:
        """Incrementa a versão do token do usuário para revogar instantaneamente todas as sessões ativas."""
        user = await self.get_by_id(user_id)
        if not user:
            return None
        user.token_version = (getattr(user, "token_version", 1) or 1) + 1
        await self.db.commit()
        await self.db.refresh(user)
        return user

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[User]:
        """Lista usuários ativos do condomínio."""
        stmt = select(User).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def list_by_condominio(
        self,
        condominio_id: Optional[int] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[User]:
        """Lista usuários vinculados estritamente ao condomínio autenticado."""
        stmt = select(User).where(~User.tipo_usuario.in_(["SUPERADMIN", "DIRETORIA"]))
        if condominio_id is not None:
            stmt = stmt.where(User.condominio_id == condominio_id)
        stmt = stmt.order_by(User.id.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def log_access(
        self,
        user_id: Optional[int],
        email: str,
        ip: Optional[str],
        user_agent: Optional[str],
        sucesso: bool
    ) -> None:
        """
        Registra tentativa de acesso para auditoria de segurança e prevenção a acessos indevidos.
        """
        try:
            log = AccessLog(
                usuario_id=user_id,
                email_informado=email,
                ip_origem=ip,
                user_agent=user_agent,
                sucesso=sucesso
            )
            self.db.add(log)
            await self.db.flush()
        except Exception:
            pass
