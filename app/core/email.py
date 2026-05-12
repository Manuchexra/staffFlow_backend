import smtplib
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.config import settings

def _send_smtp_email(msg, email: str) -> bool:
    """Synchronous SMTP sending function"""
    try:
        with smtplib.SMTP(settings.SMTP_SERVER, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_EMAIL, settings.SMTP_PASSWORD)
            server.send_message(msg)
        print(f"✅ OTP email sent to {email}")
        return True
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False

async def send_otp_email(email: str, otp: str, user_name: str = "Foydalanuvchi") -> bool:
    """
    OTP kodini emailga yuborish
    """
    try:
        subject = "StaffFlow - Tasdiqlash Kodi"
        html_content = f"""
        <html>
            <body style="font-family: Arial, sans-serif;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                    <h2 style="color: #333;">Assalomu alaykum {user_name}!</h2>
                    <p style="color: #666; font-size: 16px;">
                        Yangi qurilmadan tizimga kirish uchun quyidagi tasdiqlash kodini ishlating:
                    </p>
                    <div style="background-color: #f0f0f0; padding: 20px; border-radius: 5px; text-align: center; margin: 20px 0;">
                        <p style="font-size: 32px; font-weight: bold; color: #007bff; letter-spacing: 2px; margin: 0;">
                            {otp}
                        </p>
                    </div>
                    <p style="color: #666; font-size: 14px;">
                        ⏰ Bu kod 10 daqiqa davomida amal qiladi.
                    </p>
                    <p style="color: #666; font-size: 14px;">
                        🔒 Agar siz bu so'rovni yubormagansiz, bu emailni e'tiborsiz qoldiring.
                    </p>
                    <hr style="border: none; border-top: 1px solid #ddd; margin: 20px 0;">
                    <p style="color: #999; font-size: 12px; text-align: center;">
                        StaffFlow © 2026 - Barcha huquqlar himoyalangan
                    </p>
                </div>
            </body>
        </html>
        """
        
        # Test rejimida mock email
        if settings.SMTP_MOCK:
            print(f"\n{'='*60}")
            print(f"📧 OTP Email (MOCK MODE)")
            print(f"{'='*60}")
            print(f"To: {email}")
            print(f"Subject: {subject}")
            print(f"User: {user_name}")
            print(f"\n🔐 OTP CODE: {otp}")
            print(f"{'='*60}\n")
            return True
        
        # Real SMTP orqali yuborish
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = f"{settings.SMTP_FROM_NAME} <{settings.SMTP_EMAIL}>"
        msg['To'] = email
        
        part = MIMEText(html_content, 'html')
        msg.attach(part)
        
        # Async wrapper: Run synchronous SMTP in a thread to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(None, _send_smtp_email, msg, email)
        return result
        
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return False
