from flask_mail import Message
from app import mail


def send_email(subject, sender, recipients, body, body_html):
    info = {
        'subject': subject,
        'sender': sender,
        'recipients': recipients,
        'body': body,
        'html': body_html
    }
    msg = Message(**info)
    mail.send(msg)
