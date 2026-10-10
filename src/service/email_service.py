from src.settings.config import settings
from src.utils.logging import get_logger
import resend

logger = get_logger("email_service")


resend.api_key = settings.RESEND_API_KEY

class Email_Service:

    def __init__(self):
        self.email_from = settings.EMAIL_FROM
        self.front = settings.FRONT

    def send_verification_email (self, to_email: str, token: str):


        try:
            logger.info("Sending verification email to %s", to_email)
            verification_url = f"{self.front}/v1/user/verify-email?token={token}"
            
            params = {
                "from": self.email_from,
                "to": [to_email],
                "subject": "Confirme seu cadastro",
                "html": f"""
                    <h1>Bem-vindo à Lenos IA</h1>
                    <p>Clique no link abaixo para confirmar seu email:</p>
                    <a href="{verification_url}">Confirmar Email</a>
                """
            }

            resend.Emails.send(params)
            logger.info("Verification email sent successfully to %s", to_email)
        
        except Exception as e:
            logger.error("Unexpected error in background task sending verification email to %s: %s", to_email, str(e), exc_info=True)
            return
        
    def send_reset_password_email (self, to_email: str, token: str):


        try:
            logger.info("Sending verification password to %s", to_email)
            verification_url = f"{self.front}/v1/user/reset-password?token={token}"
            
            params = {
                "from": self.email_from,
                "to": [to_email],
                "subject": "Altere sua senha",
                "html": f"""
                    <h1>Recuperação de conta Lenos IA</h1>
                    <p>Clique no link abaixo para alterar sua senha:</p>
                    <a href="{verification_url}">Alterar Senha</a>
                """
            }

            resend.Emails.send(params)
            logger.info("Verification password sent successfully to %s", to_email)
        
        except Exception as e:
            logger.error("Unexpected error in background task sending verification password email to %s: %s", to_email, str(e), exc_info=True)
            return

    def send_verification_update_email (self, to_email: str, token: str):


        try:
            logger.info("Sending verification update email to %s", to_email)
            verification_url = f"{self.front}/v1/user/confirm-email?token={token}"
            
            params = {
                "from": self.email_from,
                "to": [to_email],
                "subject": "Confirme seu email",
                "html": f"""
                    <h1>Alterar email da conta Lenos IA</h1>
                    <p>Clique no link abaixo para confirmar seu email:</p>
                    <a href="{verification_url}">Confirmar Email</a>
                """
            }

            resend.Emails.send(params)
            logger.info("Verification update email sent successfully to %s", to_email)
        
        except Exception as e:
            logger.error("Unexpected error in background task sending verification update email to %s: %s", to_email, str(e), exc_info=True)
            return
