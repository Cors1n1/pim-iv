import asyncio
import os
from sqlalchemy import select
from app.core.database import AsyncSessionLocal, Base, engine
import app.models.condominio
import app.models.delivery
import app.models.guest
import app.models.notice
import app.models.reservation
import app.models.settings
import app.models.ticket
import app.models.user
import app.models.visitor
from app.models.user import User
from app.core.security import get_password_hash


async def create_or_update_superadmin():
    email = os.getenv("ADMIN_EMAIL", "admin@condohub.com.br")
    senha_plana = os.getenv("ADMIN_PASSWORD", "Admin@2026")

    # Garante que todas as tabelas sejam criadas no banco primeiro
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        user = (await session.execute(select(User).where(User.email == email))).scalars().first()
        if user:
            user.senha_hash = get_password_hash(senha_plana)
            user.tipo_usuario = "DIRETORIA"
            user.ativo = True
            user.status_cadastro = "ATIVO"
            print(f"[OK] Usuário '{email}' atualizado como DIRETORIA com sucesso!")
        else:
            user = User(
                nome="Administrador Geral",
                email=email,
                senha_hash=get_password_hash(senha_plana),
                tipo_usuario="DIRETORIA",
                ativo=True,
                status_cadastro="ATIVO",
                token_version=1
            )
            session.add(user)
            print(f"[OK] Usuário Superadmin '{email}' criado com sucesso!")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(create_or_update_superadmin())
