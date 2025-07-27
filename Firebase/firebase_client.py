"""
Minimal Firebase client for MedDigest.

This module provides the essential Firebase Firestore connection and basic CRUD operations.
"""

import logging
from typing import Optional, Dict, Any
import firebase_admin
from firebase_admin import credentials, firestore
from firebase_admin.exceptions import FirebaseError

from AI_Processing.research_digest import ResearchDigest

from .firebase_config import FirebaseConfig
from Data_Classes.classes import Paper, PaperAnalysis

logger = logging.getLogger(__name__)



class FirebaseClient:
    """
    Minimal Firebase client for basic Firestore operations.
    """
    
    def __init__(self, config: FirebaseConfig):
        """
        Initialize Firebase connection.
        
        Args:
            config (FirebaseConfig): Firebase configuration
        """
        if not config.validate():
            raise ValueError("Invalid Firebase configuration")
        
        self.config = config
        self.db = None
        self._initialize_firebase()
    
    def _initialize_firebase(self):
        """Initialize Firebase Admin SDK and Firestore connection."""
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
                    # Use default credentials
                    firebase_admin.initialize_app()
            
            self.db = firestore.client()
            logger.info(f"Connected to Firebase project: {self.config.project_id}")
            
        except FirebaseError as e:
            logger.error(f"Failed to initialize Firebase: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error initializing Firebase: {str(e)}")
            raise
    
    def store_analysis(self, paper_id: str, analysis: PaperAnalysis) -> bool:
        """
        Store a paper analysis in Firestore.
        
        Args:
            paper_id (str): ID of the paper this analysis belongs to
            analysis (PaperAnalysis): Analysis object to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            analysis_ref = self.db.collection('papers').document(paper_id).collection('analyses').document('latest')
            analysis_data = {
                'specialty': analysis.specialty,
                'keywords': analysis.keywords,
                'focus': analysis.focus,
                'interest_score': analysis.interest_score,
                'score_breakdown': analysis.score_breakdown
            }
            analysis_ref.set(analysis_data)
            logger.info(f"Stored analysis for paper: {paper_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store analysis for paper {paper_id}: {str(e)}")
            return False
        
    def store_newsletter(self, newsletter: ResearchDigest) -> bool:
        """
        Store a newsletter in Firestore.
        """
        try:
            newsletter_ref = self.db.collection('newsletters').document(newsletter.id)
            newsletter_ref.set(newsletter.to_dict())
            logger.info(f"Stored newsletter: {newsletter.id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store newsletter: {str(e)}")
            return False
    
    
    def get_analysis(self, paper_id: str) -> Optional[PaperAnalysis]:
        """
        Retrieve the latest analysis for a paper from Firestore.
        
        Args:
            paper_id (str): ID of the paper to get analysis for
            
        Returns:
            Optional[PaperAnalysis]: Analysis object if found, None otherwise
        """
        try:
            analysis_ref = self.db.collection('papers').document(paper_id).collection('analyses').document('latest')
            analysis_doc = analysis_ref.get()
            
            if analysis_doc.exists:
                data = analysis_doc.to_dict()
                return PaperAnalysis(
                    specialty=data['specialty'],
                    keywords=data['keywords'],
                    focus=data['focus'],
                    interest_score=data['interest_score'],
                    score_breakdown=data.get('score_breakdown')
                )
            else:
                logger.warning(f"Analysis not found for paper: {paper_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve analysis for paper {paper_id}: {str(e)}")
            return None 