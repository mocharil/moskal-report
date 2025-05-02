import smtplib, os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

def send_email(FILE, to, TOPIC, RANGE_DATE):
    # Config
    smtp_server = "smtp.zoho.com"
    smtp_port = 587
    sender_email = os.getenv('EMAIL_SENDER')       # e.g., info@moskal.id
    sender_password = os.getenv("EMAIL_PASSWORD")  # Zoho App Password!

    # Email subject
    subject = f"Your {TOPIC} Report from {RANGE_DATE} is Ready!"

    # HTML content
    message_text = f"""
    <html>
    <body>
        <p>Hi there,</p>

        <p>We’re happy to let you know that your report on <b>{TOPIC}</b> for the period <b>{RANGE_DATE}</b> is now ready!<br>
        You’ll find the file attached below.</p>

        <p>If you have any questions or need any adjustments, feel free to reach out — we’re here to help.</p>

        <p>Thanks for trusting <b>Moskal</b>.<br>
        Have a great day!</p>

        <p>Warm regards,<br>
        The Moskal Team<br>
        <i>Insight that matters.</i></p>
    </body>
    </html>
    """

    cc = ""

    # Construct message
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = to
    message['Cc'] = cc

    # Attach HTML
    html_part = MIMEText(message_text, "html")
    message.attach(html_part)

    if FILE:
        # Attach file
        with open(FILE, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {os.path.basename(FILE)}")
            message.attach(part)

    # Send email using Zoho SMTP with TLS
    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [to] + ([cc] if cc else []), message.as_string())
        server.quit()
        print("✅ Email sent successfully via Zoho!")
    except Exception as e:
        print(f"❌ Failed to send email: {e}")
