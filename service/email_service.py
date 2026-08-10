from core.config import Settings
import resend
from utils.logging import get_logger

logger = get_logger("email_service")

settings = Settings()

resend.api_key = settings.key_resend

class Email_Service:

    def __init__(self):
        self.email_from = settings.email_from
        self.front = settings.front

    def send_verification_email (self, to_email: str, token: str):


        try:
            logger.info("Sending verification email to %s", to_email)
            verification_url = f"{self.front}/v1/verify-email?token={token}"
            
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
            verification_url = f"{self.front}/v1/reset-password?token={token}"
            
            params = {
                "from": self.email_from,
                "to": [to_email],
                "subject": "Altere sua senha",
                "html": f"""
                    <h1>Bem-vindo à Lenos IA</h1>
                    <p>Clique no link abaixo para alterar sua senha:</p>
                    <a href="{verification_url}">Alterar Senha</a>
                """
            }

            resend.Emails.send(params)
            logger.info("Verification password sent successfully to %s", to_email)
        
        except Exception as e:
            logger.error("Unexpected error in background task sending verification password email to %s: %s", to_email, str(e), exc_info=True)
            return
