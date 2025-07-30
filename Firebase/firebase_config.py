"""
Firebase configuration for MedDigest.

This module handles Firebase Admin SDK configuration for server-side operations.
"""

import os
from typing import Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)


@dataclass
class FirebaseConfig:
    """
    Firebase Admin SDK configuration.
    
    Attributes:
        project_id (str): Firebase project ID
        service_account_path (Optional[str]): Path to service account JSON file
    """
    project_id: str
    service_account_path: Optional[str] = None
        
    @classmethod
    def from_env(cls) -> 'FirebaseConfig':
        """
        Create Firebase configuration from environment variables.
        
        Returns:
            FirebaseConfig: Configuration object with values from environment
            
        Raises:
            ValueError: If required environment variables are missing
        """
        project_id = os.getenv('FIREBASE_PROJECT_ID')
        if not project_id:
            raise ValueError("FIREBASE_PROJECT_ID environment variable is required")
        
        service_account_path = os.getenv('FIREBASE_SERVICE_ACCOUNT_PATH')
        
        return cls(
            project_id=project_id,
            service_account_path=service_account_path
        )
    
    def validate(self) -> bool:
        """
        Validate the configuration.
        
        Returns:
            bool: True if configuration is valid, False otherwise
        """
        return bool(self.project_id and isinstance(self.project_id, str)) 