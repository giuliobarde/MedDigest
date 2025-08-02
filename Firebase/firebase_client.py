"""
Firebase client for MedDigest.

This module provides Firebase Firestore operations for storing research digests and managing user subscriptions.
"""

import logging
from typing import Dict, Any, Optional, List
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError
import datetime

from .firebase_config import FirebaseConfig

logger = logging.getLogger(__name__)


class FirebaseClient:
    """
    Firebase client for storing research digests and managing user subscriptions in Firestore.
    """
    
    def __init__(self, config: FirebaseConfig):
        """
        Initialize Firebase connection.
        
        Args:
            config (FirebaseConfig): Firebase configuration
            
        Raises:
            ValueError: If configuration is invalid
            FirebaseError: If Firebase initialization fails
        """
        if not config.validate():
            raise ValueError("Invalid Firebase configuration")
        
        self.config = config
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self) -> None:
        """
        Initialize Firebase Admin SDK and Firestore connection.
        
        Raises:
            FirebaseError: If Firebase initialization fails
        """
        try:
            # Check if Firebase app is already initialized
            if not firebase_admin._apps:
                if self.config.service_account_path:
                    # Use service account credentials
                    cred = credentials.Certificate(self.config.service_account_path)
                    firebase_admin.initialize_app(cred, {
                        'projectId': self.config.project_id
                    })
                else:
                    # Use default credentials (for development/testing)
                    firebase_admin.initialize_app()
            
            self.db = firestore.client()
            logger.info(f"Connected to Firebase project: {self.config.project_id}")
            
        except FirebaseError as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Firebase: {str(e)}")
            raise
    
    def store_digest(self, digest_data: Dict[str, Any], digest_id: str) -> bool:
        """
        Store a research digest in Firestore.
        
        Args:
            digest_data (Dict[str, Any]): Digest data as dictionary
            digest_id (str): Unique ID for the digest
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            digest_ref = self.db.collection('research_digests').document(digest_id)
            digest_ref.set(digest_data)
            logger.info(f"Stored research digest: {digest_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store research digest: {str(e)}")
            return False
    
    def get_digest(self, digest_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a research digest from Firestore.
        
        Args:
            digest_id (str): ID of the digest to retrieve
            
        Returns:
            Optional[Dict[str, Any]]: Digest data if found, None otherwise
        """
        try:
            digest_ref = self.db.collection('research_digests').document(digest_id)
            digest_doc = digest_ref.get()
            
            if digest_doc.exists:
                return digest_doc.to_dict()
            else:
                logger.warning(f"Digest not found: {digest_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve digest {digest_id}: {str(e)}")
            return None
    
    def get_latest_digest(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve the most recent research digest from Firestore.
        Returns:
            Optional[Dict[str, Any]]: The latest digest data if found, None otherwise.
        """
        try:
            digests = (
                self.db.collection('research_digests')
                .order_by('date_generated', direction=firestore.Query.DESCENDING)
                .limit(1)
                .stream()
            )
            for doc in digests:
                data = doc.to_dict()
                data['id'] = doc.id  
                return data
            return None  
        except Exception as e:
            logger.error(f"Failed to retrieve latest digest: {str(e)}")
            return None

    def store_user_signup(self, email: str, first_name: str, last_name: str, medical_interests: List[str]) -> bool:
        """Simple method to store user signup data."""
        try:
            user_data = {
                'email': email.lower().strip(),
                'first_name': first_name.strip(),
                'last_name': last_name.strip(),
                'medical_interests': medical_interests,
                'signed_up_at': datetime.datetime.utcnow()
            }
            
            self.db.collection('user_signups').document(email.lower().strip()).set(user_data)
            logger.info(f"Stored user signup: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store signup: {str(e)}")
            return False

