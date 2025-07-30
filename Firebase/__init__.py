"""
Firebase database connection and operations for MedDigest.

This package provides Firebase Firestore integration for storing and retrieving
medical research papers and their analyses.
"""

from .firebase_client import FirebaseClient
from .firebase_config import FirebaseConfig

__all__ = ['FirebaseClient', 'FirebaseConfig'] 