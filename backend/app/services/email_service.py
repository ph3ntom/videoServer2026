"""
Email service for sending emails
For development, emails are printed to console
For production, configure SMTP settings in .env
"""
from typing import List
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import aiosmtplib
from app.core.config import settings
from app.core.security import create_email_verification_token


class EmailService:
    """Service for sending emails"""

    @staticmethod
    async def send_email(
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str = None
    ) -> bool:
        """Send an email"""
        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["From"] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_FROM_EMAIL}>"
            message["To"] = to_email
            message["Subject"] = subject

            # Add text and HTML parts
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # For development: print to console
            if settings.DEBUG and settings.ENVIRONMENT == "development":
                print("\n" + "="*80)
                print("📧 EMAIL (Development Mode - Console Output)")
                print("="*80)
                print(f"To: {to_email}")
                print(f"Subject: {subject}")
                print("-"*80)
                print(html_content)
                print("="*80 + "\n")
                return True

            # For production: send via SMTP
            await aiosmtplib.send(
                message,
                hostname=settings.SMTP_HOST,
                port=settings.SMTP_PORT,
                username=settings.SMTP_USER if settings.SMTP_USER else None,
                password=settings.SMTP_PASSWORD if settings.SMTP_PASSWORD else None,
                use_tls=settings.SMTP_PORT == 587,
                start_tls=settings.SMTP_PORT == 587,
            )
            return True

        except Exception as e:
            print(f"Failed to send email: {e}")
            return False

    @staticmethod
    async def send_verification_email(email: str, username: str) -> bool:
        """Send email verification email"""
        # Generate verification token
        token = create_email_verification_token(email)

        # Create verification link
        verification_link = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        # Create HTML content
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #4F46E5; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; background-color: #f9f9f9; }}
                .button {{
                    display: inline-block;
                    padding: 12px 24px;
                    background-color: #4F46E5;
                    color: white !important;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .footer {{ padding: 20px; text-align: center; color: #666; font-size: 12px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>StreamFlix</h1>
                </div>
                <div class="content">
                    <h2>이메일 인증</h2>
                    <p>안녕하세요, {username}님!</p>
                    <p>StreamFlix에 가입해 주셔서 감사합니다. 아래 버튼을 클릭하여 이메일 주소를 인증해 주세요.</p>

                    <div style="text-align: center;">
                        <a href="{verification_link}" class="button">이메일 인증하기</a>
                    </div>

                    <p>버튼이 작동하지 않으면 아래 링크를 복사하여 브라우저에 붙여넣으세요:</p>
                    <p style="word-break: break-all; color: #666; font-size: 12px;">{verification_link}</p>

                    <p style="margin-top: 30px; color: #666; font-size: 12px;">
                        이 링크는 {settings.EMAIL_VERIFICATION_EXPIRE_HOURS}시간 동안 유효합니다.
                    </p>

                    <p style="color: #666; font-size: 12px;">
                        본인이 요청하지 않은 경우 이 이메일을 무시하셔도 됩니다.
                    </p>
                </div>
                <div class="footer">
                    <p>&copy; 2026 StreamFlix. All rights reserved.</p>
                </div>
            </div>
        </body>
        </html>
        """

        # Text content (fallback)
        text_content = f"""
        StreamFlix 이메일 인증

        안녕하세요, {username}님!

        StreamFlix에 가입해 주셔서 감사합니다.
        아래 링크를 클릭하여 이메일 주소를 인증해 주세요:

        {verification_link}

        이 링크는 {settings.EMAIL_VERIFICATION_EXPIRE_HOURS}시간 동안 유효합니다.
        본인이 요청하지 않은 경우 이 이메일을 무시하셔도 됩니다.

        © 2026 StreamFlix. All rights reserved.
        """

        return await EmailService.send_email(
            to_email=email,
            subject="StreamFlix 이메일 인증",
            html_content=html_content,
            text_content=text_content
        )


email_service = EmailService()
