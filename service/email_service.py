from dotenv import load_dotenv
import os
from utils.exceptions import BadGateway
import resend

load_dotenv()

resend.api_key = os.getenv("key_resend")

class Email_Service:

    def __init__(self):
        self.email_from = os.getenv("email_from")
        self.api = os.getenv("api")

    def send_verification_email (self, to_email: str, token: str):

        verification_url = f"{self.api}/v1/verify_email?token={token}"

        try:

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
        
        except Exception:
            raise BadGateway