import base64
import pickle
from email.message import EmailMessage
from pathlib import Path

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

SCOPES = ['https://www.googleapis.com/auth/gmail.send']


def get_gmail_service():
    """Get Gmail service with OAuth2 authentication."""
    creds = None
    token_path = Path(__file__).parent / 'token.pickle'
    credentials_path = Path(__file__).parent / 'credentials.json'
    
    if token_path.exists():
        with open(token_path, 'rb') as token:
            creds = pickle.load(token)
    
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not credentials_path.exists():
                raise FileNotFoundError(
                    f"credentials.json not found at {credentials_path}. "
                    "Please download OAuth2 credentials from Google Cloud Console."
                )
            
            flow = InstalledAppFlow.from_client_secrets_file(
                credentials_path, SCOPES)
            creds = flow.run_local_server(
                port=8080,
                open_browser=True
            )
        
        with open(token_path, 'wb') as token:
            pickle.dump(creds, token)
    
    return build('gmail', 'v1', credentials=creds)


def gmail_send_message(to_email, subject, body):
    """Create and send an email message.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        body (str): Email body content
    
    Returns:
        dict: Message object, including message id, or None if error
    """
    try:
        service = get_gmail_service()
        message = EmailMessage()

        message.set_content(body)
        message["To"] = to_email
        message["From"] = "meddigest.newsletter@gmail.com"
        message["Subject"] = subject

        encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
        create_message = {"raw": encoded_message}
        
        send_message = (
            service.users()
            .messages()
            .send(userId="me", body=create_message)
            .execute()
        )
        print(f'Message Id: {send_message["id"]}')
        return send_message
    except HttpError as error:
        print(f"An error occurred: {error}")
        return None
    except Exception as error:
        print(f"An error occurred: {error}")
        return None
