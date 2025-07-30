import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

def send_email(recipient_email: str, subject: str, body: str) -> bool:
    """
    Send an email using Gmail SMTP.
    
    Args:
        recipient_email (str): Email address of the recipient
        subject (str): Subject line of the email
        body (str): Body text of the email
        
    Returns:
        bool: True if email was sent successfully, False otherwise
    """
    # Get Gmail credentials from environment variables
    sender_email = os.getenv('GMAIL_USER')
    sender_password = os.getenv('GMAIL_PASSWORD')

    if not sender_email or not sender_password:
        logger.error("Gmail credentials not found in environment variables")
        return False

    # Create message
    message = MIMEMultipart()
    message["From"] = sender_email
    message["To"] = recipient_email
    message["Subject"] = subject

    # Add body to email
    message.attach(MIMEText(body, "plain"))

    try:
        # Create SMTP session
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            
            # Send email
            server.send_message(message)
            
        logger.info(f"Email sent successfully to {recipient_email}")
        return True

    except Exception as e:
        logger.error(f"Failed to send email: {str(e)}")
        return False