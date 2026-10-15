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
