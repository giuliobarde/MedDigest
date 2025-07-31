#!/usr/bin/env python3
"""
OAuth2 Fix Script
This script helps diagnose and fix OAuth2 redirect URI issues.
"""

import json
import os
from pathlib import Path

def find_credentials_file():
    """Find the credentials.json file."""
    possible_locations = [
        Path(__file__).parent / 'credentials.json',
        Path(__file__).parent.parent / 'credentials.json',
        Path.cwd() / 'credentials.json',
        Path.home() / 'credentials.json'
    ]
    
    for location in possible_locations:
        if location.exists():
            print(f"✅ Found credentials.json at: {location}")
            return location
    
    print("❌ credentials.json not found in common locations")
    return None

def check_credentials_content(credentials_path):
    """Check the content of credentials.json to see redirect URIs."""
    try:
        with open(credentials_path, 'r') as f:
            data = json.load(f)
        
        print("\n📋 Credentials file content:")
        print(f"Client ID: {data.get('client_id', 'Not found')}")
        print(f"Project ID: {data.get('project_id', 'Not found')}")
        
        # Check for redirect URIs
        if 'web' in data:
            redirect_uris = data['web'].get('redirect_uris', [])
            print(f"Web redirect URIs: {redirect_uris}")
        
        if 'installed' in data:
            redirect_uris = data['installed'].get('redirect_uris', [])
            print(f"Installed redirect URIs: {redirect_uris}")
        
        return data
    except Exception as e:
        print(f"❌ Error reading credentials file: {e}")
        return None

def provide_fix_instructions():
    """Provide instructions to fix the redirect URI issue."""
    print("\n🔧 To fix the redirect_uri_mismatch error:")
    print()
    print("Option 1: Update Google Cloud Console (Recommended)")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Find your OAuth 2.0 Client ID and click on it")
    print("3. In 'Authorized redirect URIs', add:")
    print("   http://localhost:8080/")
    print("4. Click 'Save'")
    print()
    print("Option 2: Create new credentials")
    print("1. Go to: https://console.cloud.google.com/apis/credentials")
    print("2. Click 'Create Credentials' > 'OAuth client ID'")
    print("3. Choose 'Desktop application'")
    print("4. Name it 'MedDigest Email Sender'")
    print("5. Download the new credentials.json")
    print("6. Replace your current credentials.json file")
    print()
    print("Option 3: Use a different port")
    print("If you want to use a different port, edit email_config.py")
    print("and change the port number in the run_local_server() call")

def main():
    """Main function."""
    print("🔍 OAuth2 Credentials Diagnostic")
    print("=" * 40)
    
    # Find credentials file
    credentials_path = find_credentials_file()
    
    if credentials_path:
        # Check content
        data = check_credentials_content(credentials_path)
        
        if data:
            # Check if it's the right type
            if 'installed' in data:
                print("✅ Credentials type: Desktop application")
            elif 'web' in data:
                print("⚠️  Credentials type: Web application (may cause issues)")
            else:
                print("❓ Unknown credentials type")
    
    # Provide fix instructions
    provide_fix_instructions()

if __name__ == "__main__":
    main() 