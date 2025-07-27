"""
Minimal Firebase configuration for MedDigest.

This module handles essential Firebase project configuration.
"""

import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FirebaseConfig:
    """
    Essential Firebase configuration.
    
    Attributes:
        project_id (str): Firebase project ID
        api_key (str): Firebase API key
        auth_domain (str): Firebase auth domain
        storage_bucket (str): Firebase storage bucket
        messaging_sender_id (str): Firebase messaging sender ID
        app_id (str): Firebase app ID
        service_account_path (Optional[str]): Path to service account JSON file
    """
    project_id: str
    api_key: str
    auth_domain: str
    storage_bucket: str
    messaging_sender_id: str
    app_id: str
    service_account_path: Optional[str] = None
    measurement_id: str
        
    @classmethod
    def from_env(cls) -> 'FirebaseConfig':
        """
        Create Firebase configuration from environment variables.
        
        Returns:
            FirebaseConfig: Configuration object with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        required_vars = [
            'FIREBASE_PROJECT_ID',
            'FIREBASE_API_KEY',
            'FIREBASE_AUTH_DOMAIN',
            'FIREBASE_STORAGE_BUCKET',
            'FIREBASE_MESSAGING_SENDER_ID',
            'FIREBASE_APP_ID'
        ]
        
        missing_vars = [var for var in required_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
        return cls(
            project_id=os.getenv('FIREBASE_PROJECT_ID', ''),
            api_key=os.getenv('FIREBASE_API_KEY', ''),
            auth_domain=os.getenv('FIREBASE_AUTH_DOMAIN', ''),
            storage_bucket=os.getenv('FIREBASE_STORAGE_BUCKET', ''),
            messaging_sender_id=os.getenv('FIREBASE_MESSAGING_SENDER_ID', ''),
            app_id=os.getenv('FIREBASE_APP_ID', ''),
            measurement_id=os.getenv('FIREBASE_MEASUREMENT_ID', '')
        )
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        required_fields = [
            self.project_id, self.api_key, self.auth_domain,
            self.storage_bucket, self.messaging_sender_id, self.app_id
        ]
        
        return all(field and isinstance(field, str) for field in required_fields) 