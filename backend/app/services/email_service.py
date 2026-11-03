import asyncio
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import logging
import smtplib
from typing import Optional

from app.core.config import settings

logger = logging.getLogger("email_service")


class EmailService:
    @staticmethod
    def _send_sync(to_email: str, subject: str, html_body: str, sender_name: Optional[str] = None) -> bool:
        """Envia e-mail síncrono via SMTP com TLS (projetado para rodar em asyncio.to_thread)."""
        if not settings.MAIL_USERNAME or not settings.MAIL_PASSWORD:
            logger.warning(f"[EMAIL MOCK] Credenciais ausentes. Simulação para {to_email} | Assunto: {subject}")
            return False

        display_name = sender_name or settings.MAIL_SENDER_NAME or "Sistema de Condomínio"
        from_header = f"{Header(display_name, 'utf-8').encode()} <{settings.MAIL_DEFAULT_SENDER}>"

        msg = MIMEMultipart("alternative")
        msg["From"] = from_header
        msg["To"] = to_email
        msg["Subject"] = Header(subject, "utf-8").encode()

        part = MIMEText(html_body, "html", "utf-8")
        msg.attach(part)

        try:
            logger.info(f"[EMAIL INICIANDO] Conectando a {settings.MAIL_SERVER}:{settings.MAIL_PORT} para enviar a {to_email}...")
            with smtplib.SMTP(settings.MAIL_SERVER, settings.MAIL_PORT, timeout=12) as server:
                if settings.MAIL_TLS:
                    server.starttls()
                server.login(settings.MAIL_USERNAME, settings.MAIL_PASSWORD)
                server.sendmail(settings.MAIL_DEFAULT_SENDER, [to_email], msg.as_string())
            logger.info(f"[EMAIL ENVIADO COM SUCESSO] Para: {to_email} | Assunto: {subject}")
            return True
        except Exception as exc:
            logger.error(f"[EMAIL ERRO] Falha ao enviar para {to_email}: {exc}")
            return False

    @classmethod
    async def send_email_async(cls, to_email: str, subject: str, html_body: str, sender_name: Optional[str] = None) -> bool:
        """Executa o envio em thread dedicada sem travar o event loop do FastAPI."""
        return await asyncio.to_thread(cls._send_sync, to_email, subject, html_body, sender_name)

    # ==========================================================
    # TEMPLATES CORPORATIVOS EM HTML
    # ==========================================================

    @classmethod
    def get_base_template(cls, title: str, content_html: str, condo_name: str, condo_address: Optional[str] = None) -> str:
        address_line = f"<p style='margin: 4px 0 0 0; color: #64748b; font-size: 13px;'>{condo_address}</p>" if condo_address else ""
        return f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
          <meta charset="UTF-8" />
          <title>{title}</title>
        </head>
        <body style="margin: 0; padding: 24px; background-color: #f8fafc; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #0f172a;">
          <table align="center" border="0" cellpadding="0" cellspacing="0" width="100%" style="max-width: 600px; background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);">
            <!-- Topo / Cabeçalho -->
            <tr>
              <td style="padding: 24px 32px; background: linear-gradient(135deg, #1e3a8a 0%, #172554 100%); color: #ffffff;">
                <table width="100%" border="0" cellpadding="0" cellspacing="0">
                  <tr>
                    <td>
                      <span style="display: inline-block; width: 10px; height: 10px; border-radius: 50%; background-color: #22c55e; margin-right: 8px;"></span>
                      <strong style="font-size: 18px; letter-spacing: -0.2px;">{condo_name}</strong>
                      <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 13px;">Portal de Gestão e Serviços</p>
                    </td>
                  </tr>
                </table>
              </td>
            </tr>

            <!-- Conteúdo Principal -->
            <tr>
              <td style="padding: 32px;">
                {content_html}
              </td>
            </tr>

            <!-- Rodapé Institucional -->
            <tr>
              <td style="padding: 20px 32px; background-color: #f1f5f9; border-top: 1px solid #e2e8f0; text-align: center;">
                <strong style="color: #334155; font-size: 14px;">{condo_name}</strong>
                {address_line}
                <p style="margin: 8px 0 0 0; color: #94a3b8; font-size: 12px;">Mensagem automática gerada pelo sistema de governança condominial.</p>
              </td>
            </tr>
          </table>
        </body>
        </html>
        """

    @classmethod
    async def send_guest_invitation(
        cls,
        to_email: str,
        guest_name: str,
        host_name: str,
        unit_desc: str,
        area_name: str,
        date_str: str,
        time_start: str,
        time_end: str,
        condo_name: str,
        condo_address: Optional[str] = None
    ) -> bool:
        """Dispara convite digital ao visitante."""
        title = f"Convite para Evento - {condo_name}"
        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #1e3a8a; font-size: 22px;">Olá, {guest_name}!</h2>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Você foi convidado(a) por <strong>{host_name}</strong> ({unit_desc}) para um evento exclusivo no <strong>{condo_name}</strong>.
        </p>

        <div style="background-color: #f8fafc; border-left: 4px solid #1e3a8a; padding: 16px 20px; border-radius: 6px; margin-bottom: 24px;">
          <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Local:</strong> {area_name}</p>
          <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Data:</strong> {date_str}</p>
          <p style="margin: 0; font-size: 14px;"><strong>Horário:</strong> das {time_start} às {time_end}</p>
        </div>

        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 14px 18px; border-radius: 8px; margin-bottom: 20px;">
          <strong style="color: #1e40af; font-size: 14px;">Instruções para Acesso na Portaria:</strong>
          <p style="margin: 4px 0 0 0; color: #1e3a8a; font-size: 13px; line-height: 1.4;">
            Ao chegar na portaria principal, informe seu nome completo e apresente um documento oficial com foto. Sua entrada já está autorizada na lista do anfitrião!
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_name, condo_address)
        return await cls.send_email_async(to_email, f"Convite: {area_name} no {condo_name}", html, condo_name)

    @classmethod
    async def send_slot_recovery_offer(
        cls,
        to_email: str,
        resident_name: str,
        area_name: str,
        date_str: str,
        expires_str: str,
        condo_name: str
    ) -> bool:
        """Avisa o morador desbancado que a data voltou a ficar disponível com direito de preferência."""
        title = f"Data disponível para agendamento - {condo_name}"
        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #047857; font-size: 22px;">Boa notícia, {resident_name}!</h2>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          A vaga para <strong>{area_name}</strong> na data de <strong>{date_str}</strong> ficou disponível novamente após o cancelamento do solicitante anterior.
        </p>

        <div style="background-color: #ecfdf5; border: 1px solid #a7f3d0; padding: 16px 20px; border-radius: 8px; margin-bottom: 24px;">
          <strong style="color: #065f46; font-size: 15px;">Direito de Preferência Garantido</strong>
          <p style="margin: 6px 0 0 0; color: #047857; font-size: 14px; line-height: 1.4;">
            Como sua unidade havia sido desbancada nesta data, você tem prioridade exclusiva para reativar sua reserva como <strong>CONFIRMADA DEFINITIVA</strong> até <strong>{expires_str}</strong>.
          </p>
        </div>

        <p style="margin: 0 0 20px 0; font-size: 14px; color: #475569;">
          Acesse agora o portal do condomínio para aceitar ou dispensar a vaga.
        </p>
        """
        html = cls.get_base_template(title, content, condo_name)
        return await cls.send_email_async(to_email, f"Vaga Liberada: {area_name} em {date_str}", html, condo_name)

    @classmethod
    async def send_preemption_alert(
        cls,
        to_email: str,
        resident_name: str,
        area_name: str,
        date_str: str,
        condo_name: str
    ) -> bool:
        """Avisa o morador que sua solicitação de standby foi desbancada por morador prioritário."""
        title = f"Atualização de Solicitação - {condo_name}"
        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #1e3a8a; font-size: 20px;">Olá, {resident_name}</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Informamos que a sua solicitação em Standby para a <strong>{area_name}</strong> no dia <strong>{date_str}</strong> foi cedida para outro condômino que possuía prioridade regular.
        </p>
        <div style="background-color: #f1f5f9; border-left: 4px solid #64748b; padding: 14px 18px; border-radius: 6px; margin-bottom: 20px;">
          <p style="margin: 0; color: #334155; font-size: 13px; line-height: 1.4;">
            Caso o solicitante desista desta data, o sistema oferecerá a vaga imediatamente de volta para a sua unidade com confirmação imediata.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_name)
        return await cls.send_email_async(to_email, f"Atualização de Reserva: {area_name} em {date_str}", html, condo_name)

    @classmethod
    async def send_sindico_activation_email(
        cls,
        to_email: str,
        sindico_nome: str,
        condo_nome: str,
        condo_slug: str,
        activation_url: str,
        senha_provisoria: Optional[str] = None
    ) -> bool:
        """Dispara convite oficial de onboarding com link seguro e exclusivo de ativação para o novo síndico."""
        title = f"Bem-vindo ao CondoHub - Convite de Ativação de Síndico"

        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 22px; font-weight: 800;">Olá, {sindico_nome}!</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Você foi cadastrado na plataforma <strong>CondoHub</strong> para assumir a governança e gestão digital do seu condomínio.
        </p>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Para garantir sua total autonomia e privacidade (LGPD), clique no botão abaixo para <strong>definir sua senha definitiva pessoal</strong> e concluir a ativação do ambiente do condomínio.
        </p>

        <div style="background-color: #f0f7ff; border: 1px solid #bfdbfe; padding: 24px; border-radius: 12px; margin-bottom: 24px; text-align: center;">
          <p style="margin: 0 0 14px 0; font-size: 14px; color: #1e40af; font-weight: 600;">
            Seu e-mail cadastrado: <strong>{to_email}</strong>
          </p>
          <div style="margin-top: 10px;">
            <a href="{activation_url}" style="display: inline-block; background: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 12px rgba(37,99,235,0.25);">
              Definir Senha e Ativar Portal &rarr;
            </a>
          </div>
          <p style="margin: 16px 0 0 0; font-size: 12px; color: #64748b;">
            Ou acesse diretamente pelo link seguro:<br/>
            <a href="{activation_url}" style="color: #2563eb; word-break: break-all; font-size: 12px;">{activation_url}</a>
          </p>
        </div>

        <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
          <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.45;">
            <strong>Segurança da Informação:</strong> Este link é exclusivo para a sua conta, de <strong>uso único</strong> e expira em 7 dias. Assim que você cadastrar sua senha definitiva, este link será desativado automaticamente.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_nome or "CondoHub")
        return await cls.send_email_async(to_email, f"Convite de Ativação de Síndico: CondoHub", html, "CondoHub Operações")

    @classmethod
    async def send_administradora_activation_email(
        cls,
        to_email: str,
        gestor_nome: str,
        condo_nome: str,
        condo_slug: str,
        activation_url: str
    ) -> bool:
        """Dispara convite oficial de onboarding com link seguro e exclusivo para a Administradora parceira."""
        title = f"Bem-vindo ao CondoHub - Ativação da Administradora"

        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 22px; font-weight: 800;">Olá, {gestor_nome}!</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Sua administradora foi associada à gestão corporativa do condomínio <strong>{condo_nome}</strong> na plataforma <strong>CondoHub</strong> sob modelo de <strong>Gestão Compartilhada</strong>.
        </p>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Como gestor administrativo credenciado, você terá autonomia total para cadastrar apartamentos, cadastrar condôminos, gerenciar encomendas e emitir comunicados em conjunto com o corpo diretivo do condomínio.
        </p>

        <div style="background-color: #f0fdf4; border: 1px solid #bbf7d0; padding: 24px; border-radius: 12px; margin-bottom: 24px; text-align: center;">
          <p style="margin: 0 0 14px 0; font-size: 14px; color: #166534; font-weight: 600;">
            E-mail institucional da administradora: <strong>{to_email}</strong>
          </p>
          <div style="margin-top: 10px;">
            <a href="{activation_url}" style="display: inline-block; background: #059669; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 12px rgba(5,150,105,0.25);">
              Definir Senha e Acessar Gestão &rarr;
            </a>
          </div>
          <p style="margin: 16px 0 0 0; font-size: 12px; color: #64748b;">
            Ou acesse diretamente pelo link seguro:<br/>
            <a href="{activation_url}" style="color: #059669; word-break: break-all; font-size: 12px;">{activation_url}</a>
          </p>
        </div>

        <div style="background-color: #f8fafc; border-left: 4px solid #10b981; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
          <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.45;">
            <strong>Segurança da Informação:</strong> Este link é exclusivo para a sua conta de Administradora, de <strong>uso único</strong> e expira em 7 dias. O síndico titular também possui acesso independente ao mesmo condomínio.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_nome or "CondoHub")
        return await cls.send_email_async(to_email, f"Convite de Ativação - Administradora: {condo_nome}", html, "CondoHub Operações")

    @classmethod
    async def send_subsindico_activation_email(
        cls,
        to_email: str,
        subsindico_nome: str,
        condo_nome: str,
        condo_slug: str,
        activation_url: str
    ) -> bool:
        """Dispara convite oficial de onboarding com link seguro e exclusivo para o Subsíndico(a)."""
        title = f"Bem-vindo ao CondoHub - Ativação de Subsíndico(a)"

        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 22px; font-weight: 800;">Olá, {subsindico_nome}!</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Você foi cadastrado como <strong>Subsíndico(a)</strong> no condomínio <strong>{condo_nome}</strong> na plataforma <strong>CondoHub</strong>.
        </p>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Como membro ativo do corpo diretivo de governança, você tem acesso aos módulos operacionais do condomínio, ocorrências, comunicados e reservas.
        </p>

        <div style="background-color: #f5f3ff; border: 1px solid #ddd6fe; padding: 24px; border-radius: 12px; margin-bottom: 24px; text-align: center;">
          <p style="margin: 0 0 14px 0; font-size: 14px; color: #6d28d9; font-weight: 600;">
            Seu e-mail institucional: <strong>{to_email}</strong>
          </p>
          <div style="margin-top: 10px;">
            <a href="{activation_url}" style="display: inline-block; background: #7c3aed; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 12px rgba(124,58,237,0.25);">
              Definir Senha e Ativar Acesso &rarr;
            </a>
          </div>
          <p style="margin: 16px 0 0 0; font-size: 12px; color: #64748b;">
            Ou acesse diretamente pelo link seguro:<br/>
            <a href="{activation_url}" style="color: #7c3aed; word-break: break-all; font-size: 12px;">{activation_url}</a>
          </p>
        </div>

        <div style="background-color: #f8fafc; border-left: 4px solid #7c3aed; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
          <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.45;">
            <strong>Segurança da Informação:</strong> Este link é exclusivo para a sua conta, de <strong>uso único</strong> e expira em 7 dias. Após cadastrar sua senha pessoal, você poderá entrar no portal a qualquer momento.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_nome or "CondoHub")
        return await cls.send_email_async(to_email, f"Convite de Ativação - Subsíndico(a): {condo_nome}", html, "CondoHub Operações")

    @classmethod
    async def send_resident_invitation(
        cls,
        to_email: str,
        resident_name: str,
        condo_nome: str,
        unit_desc: str,
        activation_url: str,
        tipo_usuario: str = "MORADOR"
    ) -> bool:
        """Dispara convite digital de ativação de morador ou membro da portaria."""
        role_label = "Morador" if tipo_usuario == "MORADOR" else "Portaria"
        title = f"Convite para o Portal - {condo_nome}"

        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 22px; font-weight: 800;">Olá, {resident_name}!</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          A administração do <strong>{condo_nome}</strong> cadastrou o seu acesso como <strong>{role_label}</strong> ({unit_desc}).
        </p>
        <p style="margin: 0 0 20px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Para ativar sua conta, definir sua senha pessoal e ter acesso ao portal de encomendas, reservas de áreas comuns e comunicados, clique no botão abaixo:
        </p>

        <div style="background-color: #f0f7ff; border: 1px solid #bfdbfe; padding: 24px; border-radius: 12px; margin-bottom: 24px; text-align: center;">
          <p style="margin: 0 0 14px 0; font-size: 14px; color: #1e40af; font-weight: 600;">
            E-mail cadastrado: <strong>{to_email}</strong>
          </p>
          <div style="margin-top: 10px;">
            <a href="{activation_url}" style="display: inline-block; background: #2563eb; color: #ffffff; text-decoration: none; padding: 14px 30px; border-radius: 8px; font-weight: 700; font-size: 15px; box-shadow: 0 4px 12px rgba(37,99,235,0.25);">
              Definir Minha Senha e Acessar &rarr;
            </a>
          </div>
          <p style="margin: 16px 0 0 0; font-size: 12px; color: #64748b;">
            Ou acesse diretamente pelo link seguro:<br/>
            <a href="{activation_url}" style="color: #2563eb; word-break: break-all; font-size: 12px;">{activation_url}</a>
          </p>
        </div>

        <div style="background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 12px 16px; border-radius: 4px; margin-bottom: 16px;">
          <p style="margin: 0; font-size: 13px; color: #475569; line-height: 1.45;">
            <strong>Acesso Seguro:</strong> Este convite é pessoal e intransferível. Após a definição da sua senha, o link é invalidado automaticamente.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_nome or "CondoHub")
        return await cls.send_email_async(to_email, f"Convite de Acesso - {condo_nome}", html, condo_nome)

    @classmethod
    async def send_delivery_alert(
        cls,
        to_email: str,
        resident_name: str,
        condo_nome: str,
        unit_desc: str,
        package_desc: str,
        tracking_code: Optional[str] = None
    ) -> bool:
        """Dispara aviso ao morador de que uma nova encomenda chegou na portaria."""
        title = f"Nova Encomenda na Portaria - {condo_nome}"
        tracking_line = f"<p style='margin: 0 0 8px 0; font-size: 14px;'><strong>Código/Rastreio:</strong> {tracking_code}</p>" if tracking_code else ""

        content = f"""
        <h2 style="margin: 0 0 12px 0; color: #0f172a; font-size: 22px; font-weight: 800;">Olá, {resident_name}!</h2>
        <p style="margin: 0 0 16px 0; font-size: 15px; line-height: 1.5; color: #334155;">
          Uma nova encomenda destinada à sua unidade (<strong>{unit_desc}</strong>) foi recebida e registrada na portaria do <strong>{condo_nome}</strong>.
        </p>

        <div style="background-color: #f8fafc; border-left: 4px solid #2563eb; padding: 16px 20px; border-radius: 6px; margin-bottom: 24px;">
          <p style="margin: 0 0 8px 0; font-size: 14px;"><strong>Pacote:</strong> {package_desc}</p>
          {tracking_line}
          <p style="margin: 0; font-size: 14px; color: #64748b;">Status: <strong>Aguardando Retirada</strong></p>
        </div>

        <div style="background-color: #eff6ff; border: 1px solid #bfdbfe; padding: 14px 18px; border-radius: 8px; margin-bottom: 16px;">
          <strong style="color: #1e40af; font-size: 14px;">Como retirar:</strong>
          <p style="margin: 4px 0 0 0; color: #1e3a8a; font-size: 13px; line-height: 1.4;">
            Dirija-se à guarita do condomínio e informe o seu apartamento para que a equipe da portaria realize a baixa da entrega.
          </p>
        </div>
        """
        html = cls.get_base_template(title, content, condo_nome or "CondoHub")
        return await cls.send_email_async(to_email, f"📦 Encomenda Recebida na Portaria - {condo_nome}", html, condo_nome)





