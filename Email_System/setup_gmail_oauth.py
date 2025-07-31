#!/usr/bin/env python3
"""
Gmail OAuth2 Setup Script
This script helps you set up OAuth2 credentials for Gmail API access.
"""

import os
import sys
from pathlib import Path

def print_setup_instructions():
    """Print step-by-step instructions for setting up Gmail OAuth2."""
    print("🔧 Gmail OAuth2 Setup Instructions")
    print("=" * 50)
    print()
    print("To fix the authentication error, you need to set up OAuth2 credentials:")
    print()
    print("1. Go to Google Cloud Console:")
    print("   https://console.cloud.google.com/")
    print()
    print("2. Select your project (meddigest-5c293)")
    print()
    print("3. Enable the Gmail API:")
    print("   - Go to 'APIs & Services' > 'Library'")
    print("   - Search for 'Gmail API' and enable it")
    print()
    print("4. Create OAuth2 credentials:")
    print("   - Go to 'APIs & Services' > 'Credentials'")
    print("   - Click 'Create Credentials' > 'OAuth client ID'")
    print("   - Choose 'Desktop application' as the application type")
    print("   - Give it a name like 'MedDigest Email Sender'")
    print("   - Click 'Create'")
    print()
    print("5. Configure the redirect URI (IMPORTANT!):")
    print("   - After creating the OAuth client, click on it to edit")
    print("   - In the 'Authorized redirect URIs' section, add:")
    print("     http://localhost:8080/")
    print("   - Click 'Save'")
    print()
    print("6. Download the credentials:")
    print("   - Click the download button (⬇️) next to your OAuth client")
    print("   - Save the file as 'credentials.json'")
    print("   - Move it to the Email_System directory:")
    print(f"     {Path(__file__).parent}")
    print()
    print("7. Install required packages:")
    print("   pip install -r requirements.txt")
    print()
    print("8. Run the email script:")
    print("   python3 Email_System/send_email.py")
    print()
    print("The first time you run the script, it will open a browser window")
    print("for you to authorize the application. After authorization, it will")
    print("save the tokens and won't need to authenticate again.")
    print()

def check_credentials():
    """Check if credentials.json exists."""
    credentials_path = Path(__file__).parent / 'credentials.json'
    if credentials_path.exists():
        print("✅ credentials.json found!")
        return True
    else:
        print("❌ credentials.json not found!")
        print(f"Expected location: {credentials_path}")
        return False

def main():
    """Main setup function."""
    print_setup_instructions()
    
    if check_credentials():
        print("🎉 Setup looks good! You can now run:")
        print("   python3 Email_System/send_email.py")
    else:
        print("Please follow the instructions above to create and download")
        print("your OAuth2 credentials file.")

if __name__ == "__main__":
    main() 