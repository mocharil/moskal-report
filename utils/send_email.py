
import smtplib, os
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from dotenv import load_dotenv
load_dotenv()

def send_email(FILE, to, TOPIC, RANGE_DATE):


    sender_email = os.getenv('EMAIL_SENDER')
    sender_password = os.getenv("EMAIL_PASSWORD")
   
    # Subject
    subject = f"Your {TOPIC} Report from {RANGE_DATE} is Ready!"

    # Body email (HTML version)
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
    
    filenames  = [FILE]
    message = MIMEMultipart()
    message['Subject'] = subject
    message['From'] = sender_email
    message['To'] = to
    message['Cc'] = cc
    
    # Attach HTML content
    html_part = MIMEText(message_text, "html")
    message.attach(html_part)

    # Attach files
    for filename in filenames:
        with open(filename, "rb") as attachment:
            part = MIMEBase("application", "octet-stream")
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f"attachment; filename= {filename}")
            message.attach(part)

    # Send email
    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, [to] + [cc], message.as_string())
