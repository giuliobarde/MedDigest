#!/usr/bin/env python3
"""
Email Sender Script
Uses the existing email configuration to send emails via Gmail API.
"""

from .email_config import gmail_send_message
from Firebase.firebase_client import FirebaseClient
from Firebase.firebase_config import FirebaseConfig


def send_newsletter_email(to_email, subject, body, is_markdown=False):
    """
    Send a newsletter email using the Gmail API.
    
    Args:
        to_email (str): Recipient email address
        subject (str): Email subject line
        body (str): Email body content
        is_markdown (bool): Whether the body content is markdown
    
    Returns:
        dict: Response from Gmail API or None if error
    """
    try:
        result = gmail_send_message(to_email, subject, body, is_markdown)
        if result:
            print(f"✅ Email sent successfully to {to_email}")
            return result
        else:
            print(f"❌ Failed to send email to {to_email}")
            return None
    except Exception as e:
        print(f"❌ Error sending email: {e}")
        return None


def send_bulk_emails(recipients, subject, body, is_markdown=False):
    """
    Send emails to multiple recipients.
    
    Args:
        recipients (list): List of email addresses
        subject (str): Email subject line
        body (str): Email body content
        is_markdown (bool): Whether the body content is markdown
    
    Returns:
        dict: Summary of results
    """
    results = {
        'successful': [],
        'failed': []
    }
    
    for recipient in recipients:
        email = recipient['email']
        result = send_newsletter_email(email, subject, body, is_markdown)
        if result:
            results['successful'].append(email)
        else:
            results['failed'].append(email)
    
    print(f"\n📊 Email Summary:")
    print(f"✅ Successful: {len(results['successful'])}")
    print(f"❌ Failed: {len(results['failed'])}")
    
    return results 


def send_email_to_user(subject, body, is_markdown=False):
    """
    Send an email to a specific hardcoded user for testing purposes.
    Customizes the email content with user's personal information and highest rated paper focus.
    """
    user = {
        "email": "giuliobarde@gmail.com",
        "first_name": "Giulio",
        "last_name": "Bardelli",
        "medical_interests": ["Cardiology", "Radiology", "Oncology"],
        "signed_up_at": {
            "date": "2025-01-01",
            "time": "12:00:00"
        }
    }
    
    # Get the highest rated paper's focus for each user's interest
    try:
        # Initialize Firebase client
        firebase_config = FirebaseConfig.from_env()
        firebase_client = FirebaseClient(firebase_config)
        
        # Get focus for each individual interest
        interest_focuses = firebase_client.get_highest_rated_paper_focus_per_interest(user['medical_interests'])
    except Exception as e:
        print(f"Error getting paper focus: {e}")
        # Fallback to default messages for each interest
        interest_focuses = {
            interest: f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}."
            for interest in user['medical_interests']
        }
    
    # Create personalized paragraphs for each interest
    interest_paragraphs = []
    for interest in user['medical_interests']:
        focus = interest_focuses.get(interest, f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}.")
        interest_paragraphs.append(focus)
    
    # Join all interest paragraphs
    interests_content = "\n\n".join(interest_paragraphs)
    
    # Create a personalized email body with proper markdown formatting
    personalized_body = f"""# MedDigest Weekly Research Newsletter

Dear **{user['first_name']} {user['last_name']}**,

---

## 🎯 Your Personalized Research Focus

{interests_content}

---

## 📊 Your Medical Interests
**Specialties**: {', '.join(user['medical_interests'])}  

---

{body}

---

*Best regards,*  
**The MedDigest Team**

---
*This newsletter is personalized based on your medical interests and the latest high-impact research in your fields.*
"""
    
    return send_newsletter_email(user['email'], subject, personalized_body, is_markdown=True)