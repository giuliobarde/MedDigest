#!/usr/bin/env python3
"""
Verify OAuth2 Credentials Script
This script verifies that your OAuth2 credentials are properly configured.
"""

import json
from pathlib import Path

def verify_credentials():
    """Verify that credentials.json is properly configured."""
    credentials_path = Path(__file__).parent / 'credentials.json'
    
    if not credentials_path.exists():
        print("❌ credentials.json not found!")
        print(f"Expected location: {credentials_path}")
        return False
    
    try:
        with open(credentials_path, 'r') as f:
            data = json.load(f)
        
        print("✅ credentials.json found and readable")
        
        # Check if it's a desktop application
        if 'installed' in data:
            print("✅ Credentials type: Desktop application (correct)")
            client_id = data['installed'].get('client_id', 'Not found')
            print(f"Client ID: {client_id}")
            return True
        elif 'web' in data:
            print("⚠️  Credentials type: Web application (incorrect for desktop use)")
            print("Please create new credentials as 'Desktop application'")
            return False
        else:
            print("❓ Unknown credentials type")
            return False
            
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return False

def main():
    """Main function."""
    print("🔍 OAuth2 Credentials Verification")
    print("=" * 40)
    
    if verify_credentials():
        print("\n🎉 Your credentials look good!")
        print("You can now try running the email script:")
        print("   python3 Email_System/send_email.py")
    else:
        print("\n❌ Please fix your credentials before proceeding.")
        print("Follow the instructions to create new Desktop application credentials.")

if __name__ == "__main__":
    main() 