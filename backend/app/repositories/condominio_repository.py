from typing import Dict, List, Optional
from sqlalchemy import func, select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.condominio import Condominio
from app.models.reservation import Reservation
from app.models.ticket import Ticket
from app.models.user import Unit, User


class CondominioRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def get_by_id(self, condominio_id: int) -> Optional[Condominio]:
        """Obtém o condomínio pelo ID numérico único."""
        stmt = select(Condominio).where(Condominio.id == condominio_id)
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_cnpj(self, cnpj: str) -> Optional[Condominio]:
        """Busca condomínio pelo CNPJ formatado ou limpo."""
        stmt = select(Condominio).where(Condominio.cnpj == cnpj.strip())
        result = await self.db.execute(stmt)
        return result.scalars().first()

    async def get_by_slug(self, slug: str) -> Optional[Condominio]:
        """Busca condomínio pela slug amigável da URL (suporta com e sem hífen)."""
        clean_slug = slug.strip().lower()
        stmt = select(Condominio).where(Condominio.slug == clean_slug)
        result = await self.db.execute(stmt)
        condo = result.scalars().first()
        if not condo:
            # Fallback flexível: busca ignorando hífens (ex: solar-das-palmeiras vs solardaspalmeiras)
            slug_flat = clean_slug.replace("-", "")
            stmt_fallback = select(Condominio).where(
                func.replace(Condominio.slug, "-", "") == slug_flat
            )
            result_fb = await self.db.execute(stmt_fallback)
            condo = result_fb.scalars().first()
        return condo

    async def count_relations(self, condominio_id: int) -> Dict:
        """Contagem detalhada de todos os módulos vinculados ao condomínio."""
        from app.models.delivery import Delivery
        from app.models.reservation import CommonArea

        stmt_u = select(func.count(Unit.id)).where(Unit.condominio_id == condominio_id)
        total_u = (await self.db.execute(stmt_u)).scalar() or 0

        stmt_m = select(func.count(User.id)).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "MORADOR",
            User.ativo == True
        )
        total_m = (await self.db.execute(stmt_m)).scalar() or 0

        stmt_p = select(func.count(User.id)).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "PORTARIA",
            User.ativo == True
        )
        total_p = (await self.db.execute(stmt_p)).scalar() or 0

        stmt_enc = select(func.count(Delivery.id)).where(
            Delivery.condominio_id == condominio_id,
            Delivery.status == "AGUARDANDO_RETIRADA"
        )
        total_enc = (await self.db.execute(stmt_enc)).scalar() or 0

        stmt_oco = select(func.count(Ticket.id)).where(
            Ticket.condominio_id == condominio_id,
            Ticket.status.in_(["ABERTO", "EM_ANALISE"])
        )
        total_oco = (await self.db.execute(stmt_oco)).scalar() or 0

        stmt_res = select(func.count(Reservation.id)).join(CommonArea).where(
            CommonArea.condominio_id == condominio_id
        )
        total_res = (await self.db.execute(stmt_res)).scalar() or 0

        stmt_areas = select(func.count(CommonArea.id)).where(
            CommonArea.condominio_id == condominio_id
        )
        total_areas = (await self.db.execute(stmt_areas)).scalar() or 0

        stmt_sindico = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "SINDICO",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        sindico = (await self.db.execute(stmt_sindico)).scalars().first()
        if not sindico:
            stmt_fallback = select(User).where(
                User.condominio_id == condominio_id,
                User.tipo_usuario.in_(["SINDICO", "ADMIN"]),
                User.ativo == True
            ).order_by(User.id.asc()).limit(1)
            sindico = (await self.db.execute(stmt_fallback)).scalars().first()

        stmt_adm = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "ADMIN",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        adm_user = (await self.db.execute(stmt_adm)).scalars().first()

        stmt_sub = select(User).where(
            User.condominio_id == condominio_id,
            User.tipo_usuario == "SUBSINDICO",
            User.ativo == True
        ).order_by(User.id.asc()).limit(1)
        sub_user = (await self.db.execute(stmt_sub)).scalars().first()
        if not sub_user:
            stmt_sub_fallback = select(User).where(
                User.condominio_id == condominio_id,
                User.tipo_usuario == "ADMIN",
                User.nome.ilike("%sub%"),
                User.ativo == True
            ).order_by(User.id.asc()).limit(1)
            sub_user = (await self.db.execute(stmt_sub_fallback)).scalars().first()

        return {
            "total_unidades": total_u,
            "total_moradores": total_m,
            "total_porteiros": total_p,
            "total_encomendas_pendentes": total_enc,
            "total_ocorrencias_abertas": total_oco,
            "total_reservas": total_res,
            "total_areas_comuns": total_areas,
            "sindico_id": sindico.id if sindico else None,
            "sindico_nome": sindico.nome if sindico else None,
            "sindico_email": sindico.email if sindico else None,
            "sindico_telefone": sindico.telefone if sindico else None,
            "sindico_ativo": sindico.ativo if sindico else False,
            "tem_subsindico": sub_user is not None,
            "subsindico_id": sub_user.id if sub_user else None,
            "subsindico_nome": sub_user.nome if sub_user else None,
            "subsindico_email": sub_user.email if sub_user else None,
            "subsindico_telefone": sub_user.telefone if sub_user else None,
            "subsindico_ativo": sub_user.ativo if sub_user else False,
            "administradora_id": adm_user.id if adm_user else None,
            "administradora_ativo": adm_user.ativo if adm_user else False
        }

    async def list_all(self, skip: int = 0, limit: int = 100) -> List[Dict]:
        """Lista condomínios com contagem agregada de unidades, moradores e métricas."""
        stmt = select(Condominio).order_by(Condominio.id.asc()).offset(skip).limit(limit)
        result = await self.db.execute(stmt)
        condominios = list(result.scalars().all())

        items = []
        for c in condominios:
            counts = await self.count_relations(c.id)
            items.append({
                "condominio": c,
                **counts
            })
        return items

    async def create(self, condominio: Condominio) -> Condominio:
        """Cadastra um novo condomínio no sistema SaaS."""
        self.db.add(condominio)
        await self.db.commit()
        await self.db.refresh(condominio)
        return condominio

    async def update(self, condominio: Condominio) -> Condominio:
        """Atualiza dados cadastrais, plano ou cores de um condomínio."""
        await self.db.commit()
        await self.db.refresh(condominio)
        return condominio

    async def update_status(self, condominio_id: int, novo_status: str, motivo: Optional[str] = None) -> Optional[Condominio]:
        """Bloqueia, desbloqueia ou cancela o acesso do condomínio sem deletar dados."""
        condo = await self.get_by_id(condominio_id)
        if not condo:
            return None
        condo.status = novo_status
        if novo_status == "BLOQUEADO":
            condo.motivo_bloqueio = motivo
        elif novo_status == "ATIVO":
            condo.motivo_bloqueio = None
        await self.db.commit()
        await self.db.refresh(condo)
        return condo

    set_status = update_status


    async def get_saas_metrics(self) -> Dict:
        """Retorna métricas consolidadas da plataforma SaaS para o SuperAdmin."""
        # Total de condomínios
        total_condos = (await self.db.execute(select(func.count(Condominio.id)))).scalar() or 0
        condos_ativos = (await self.db.execute(select(func.count(Condominio.id)).where(Condominio.status == "ATIVO"))).scalar() or 0
        condos_bloqueados = (await self.db.execute(select(func.count(Condominio.id)).where(Condominio.status == "BLOQUEADO"))).scalar() or 0

        # Total de unidades em todos os condomínios
        total_unidades = (await self.db.execute(select(func.count(Unit.id)))).scalar() or 0

        # Total de usuários
        total_usuarios = (await self.db.execute(select(func.count(User.id)).where(User.tipo_usuario != "SUPERADMIN"))).scalar() or 0

        # Total de reservas processadas na plataforma
        total_reservas = (await self.db.execute(select(func.count(Reservation.id)))).scalar() or 0

        # Total de ocorrências registradas
        total_ocorrencias = (await self.db.execute(select(func.count(Ticket.id)))).scalar() or 0

        # Estimativa de faturamento SaaS mensal (Planos: Básico R$ 199, Pro R$ 449, Enterprise R$ 899)
        stmt_planos = select(Condominio.plano, func.count(Condominio.id)).where(Condominio.status == "ATIVO").group_by(Condominio.plano)
        res_planos = (await self.db.execute(stmt_planos)).fetchall()
        tabela_precos = {"BASICO": 199.00, "PRO": 449.00, "ENTERPRISE": 899.00}
        faturamento_estimado = sum(tabela_precos.get(p[0], 299.00) * p[1] for p in res_planos)

        return {
            "total_condominios": total_condos,
            "condominios_ativos": condos_ativos,
            "condominios_bloqueados": condos_bloqueados,
            "total_unidades": total_unidades,
            "total_usuarios": total_usuarios,
            "total_reservas": total_reservas,
            "total_ocorrencias": total_ocorrencias,
            "faturamento_mensal_estimado": faturamento_estimado
        }

    async def delete_condominio_cascade(self, condominio_id: int) -> bool:
        """Exclui condomínio e todas as suas entidades dependentes em cascata com integridade."""
        from app.models.delivery import Delivery
        from app.models.notice import Notice
        from app.models.reservation import CommonArea, Reservation
        from app.models.settings import CondoSettings
        from app.models.ticket import Ticket
        from app.models.user import AccessLog, Unit, User
        from app.models.visitor import Visitor

        condo = await self.get_by_id(condominio_id)
        if not condo:
            return False

        # 1. Desvincular referências circulares entre usuários e unidades
        await self.db.execute(
            update(User).where(User.condominio_id == condominio_id).values(unidade_id=None)
        )
        await self.db.execute(
            update(Unit).where(Unit.condominio_id == condominio_id).values(morador_responsavel_id=None)
        )
        await self.db.flush()

        # 2. Desvincular usuários com papel executivo (DIRETORIA / SUPERADMIN / Master) para não violar integridade
        await self.db.execute(
            update(User).where(
                User.condominio_id == condominio_id,
                User.tipo_usuario.in_(["SUPERADMIN", "DIRETORIA"])
            ).values(condominio_id=None)
        )
        await self.db.flush()

        # 3. Identificar usuários remanescentes deste condomínio para limpar reservas associadas
        users_res = await self.db.execute(select(User.id).where(User.condominio_id == condominio_id))
        uids = [r[0] for r in users_res.all()]
        if uids:
            await self.db.execute(delete(Reservation).where(Reservation.usuario_id.in_(uids)))

        # 4. Excluir dados operacionais dependentes
        await self.db.execute(delete(CommonArea).where(CommonArea.condominio_id == condominio_id))
        await self.db.execute(delete(AccessLog).where(AccessLog.condominio_id == condominio_id))
        await self.db.execute(delete(Visitor).where(Visitor.condominio_id == condominio_id))
        await self.db.execute(delete(Ticket).where(Ticket.condominio_id == condominio_id))
        await self.db.execute(delete(Delivery).where(Delivery.condominio_id == condominio_id))
        await self.db.execute(delete(Notice).where(Notice.condominio_id == condominio_id))
        await self.db.execute(delete(CondoSettings).where(CondoSettings.condominio_id == condominio_id))

        # 5. Excluir usuários locais deste condomínio (moradores, porteiros, síndicos locais)
        await self.db.execute(delete(User).where(User.condominio_id == condominio_id))

        # 6. Excluir unidades e o condomínio
        await self.db.execute(delete(Unit).where(Unit.condominio_id == condominio_id))
        await self.db.execute(delete(Condominio).where(Condominio.id == condominio_id))
        await self.db.commit()
        return True
