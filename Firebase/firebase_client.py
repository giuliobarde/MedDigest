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
                service_account_dict = self.config.get_service_account_dict()
                
                if service_account_dict:
                    # Use service account credentials from JSON
                    cred = credentials.Certificate(service_account_dict)
                    firebase_admin.initialize_app(cred, {
                        'projectId': self.config.project_id
                    })
                elif self.config.service_account_path:
                    # Use service account file path (for local development)
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

    def store_user_signup(self, email: str, first_name: str, last_name: str, medical_interests: List[str], reading_time: str) -> bool:
        """Simple method to store user signup data."""
        try:
            user_data = {
                'email': email.lower().strip(),
                'first_name': first_name.strip(),
                'last_name': last_name.strip(),
                'medical_interests': medical_interests,
                'reading_time': reading_time,
                'signed_up_at': datetime.datetime.utcnow()
            }
            
            self.db.collection('user_signups').document(email.lower().strip()).set(user_data)
            logger.info(f"Stored user signup: {email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to store signup: {str(e)}")
            return False
 
    def store_paper_analysis(self, paper_id: str, analysis: Dict[str, Any]) -> bool:
        """
        Store a paper analysis in Firestore.
        
        Args:
            paper_id (str): Unique identifier for the paper
            analysis (Dict[str, Any]): Analysis data to store
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Store in paper_analyses collection with paper_id as document ID
            analysis_ref = self.db.collection('paper_analyses').document(paper_id)
            
            # Add timestamp for when the analysis was stored
            analysis['stored_at'] = firestore.SERVER_TIMESTAMP
            
            analysis_ref.set(analysis)
            logger.info(f"Stored paper analysis for paper ID: {paper_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to store paper analysis for paper ID {paper_id}: {str(e)}")
            return False
    
    def get_paper_analysis(self, paper_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a paper analysis from Firestore.
        
        Args:
            paper_id (str): ID of the paper to retrieve analysis for
            
        Returns:
            Optional[Dict[str, Any]]: Analysis data if found, None otherwise
        """
        try:
            analysis_ref = self.db.collection('paper_analyses').document(paper_id)
            analysis_doc = analysis_ref.get()
            
            if analysis_doc.exists:
                return analysis_doc.to_dict()
            else:
                logger.warning(f"Paper analysis not found: {paper_id}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to retrieve paper analysis {paper_id}: {str(e)}")
            return None

    def get_analyses_by_specialty(self, specialty: str, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve paper analyses filtered by specialty.
        
        Args:
            specialty (str): Medical specialty to filter by
            limit (int): Maximum number of analyses to return
            
        Returns:
            List[Dict[str, Any]]: List of analysis data
        """
        try:
            analyses_ref = self.db.collection('paper_analyses')
            query = analyses_ref.where('specialty', '==', specialty).limit(limit)
            docs = query.stream()
            
            analyses = []
            for doc in docs:
                analysis_data = doc.to_dict()
                analysis_data['paper_id'] = doc.id
                analyses.append(analysis_data)
            
            logger.info(f"Retrieved {len(analyses)} analyses for specialty: {specialty}")
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to retrieve analyses for specialty {specialty}: {str(e)}")
            return []

    def get_high_interest_analyses(self, min_score: float = 7.0, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve paper analyses with high interest scores.
        
        Args:
            min_score (float): Minimum interest score threshold
            limit (int): Maximum number of analyses to return
            
        Returns:
            List[Dict[str, Any]]: List of high-interest analysis data
        """
        try:
            analyses_ref = self.db.collection('paper_analyses')
            query = analyses_ref.where('interest_score', '>=', min_score).order_by('interest_score', direction=firestore.Query.DESCENDING).limit(limit)
            docs = query.stream()
            
            analyses = []
            for doc in docs:
                analysis_data = doc.to_dict()
                analysis_data['paper_id'] = doc.id
                analyses.append(analysis_data)
            
            logger.info(f"Retrieved {len(analyses)} high-interest analyses (score >= {min_score})")
            return analyses
            
        except Exception as e:
            logger.error(f"Failed to retrieve high-interest analyses: {str(e)}")
            return []

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

    def get_all_user_subscriptions(self) -> Optional[Dict[str, Any]]:
        """
        Retrieve all user subscriptions from Firestore.
        """
        try:
            subscriptions_ref = self.db.collection('user_signups')
            docs = subscriptions_ref.stream()
            
            subscriptions = {}
            for doc in docs:
                subscription_data = doc.to_dict()
                subscriptions[doc.id] = subscription_data
            
            logger.info(f"Retrieved {len(subscriptions)} user subscriptions")
            return subscriptions
                
        except Exception as e:
            logger.error(f"Failed to retrieve user subscriptions: {str(e)}")
            return None

    def get_highest_rated_paper_focus_per_interest(self, user_interests: List[str]) -> Dict[str, str]:
        """
        Get the focus field of the highest rated paper for each individual medical interest.
        Only considers papers from the latest newsletter generation.
        
        Args:
            user_interests (List[str]): List of user's medical interests
            
        Returns:
            Dict[str, str]: Dictionary mapping each interest to its highest rated paper focus
        """
        try:
            interest_focuses = {}
            
            # Get the latest digest to access papers from the latest newsletter generation
            latest_digest = self.get_latest_digest()
            if not latest_digest:
                logger.warning("No latest digest found, returning default messages")
                return {interest: f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}." 
                       for interest in user_interests}
            
            # Extract papers from the latest digest's specialty_data
            latest_papers = {}
            if 'specialty_data' in latest_digest:
                for specialty, spec_info in latest_digest['specialty_data'].items():
                    if 'papers' in spec_info:
                        latest_papers[specialty] = spec_info['papers']
            
            # If no specialty_data in latest digest, try to get from digest_summary
            if not latest_papers and 'digest_summary' in latest_digest:
                digest_summary = latest_digest['digest_summary']
                if 'specialty_data' in digest_summary:
                    for specialty, spec_info in digest_summary['specialty_data'].items():
                        if 'papers' in spec_info:
                            latest_papers[specialty] = spec_info['papers']
            
            for interest in user_interests:
                # Check if this interest has papers in the latest digest
                if interest in latest_papers:
                    papers = latest_papers[interest]
                    
                    # Find the highest rated paper in this specialty from latest digest
                    highest_rated_paper = None
                    highest_score = 0.0
                    
                    for paper in papers:
                        # Get the full analysis for this paper to access interest_score
                        paper_analysis = self.get_paper_analysis(paper.get('id', ''))
                        if paper_analysis:
                            score = paper_analysis.get('interest_score', 0.0)
                            if score > highest_score:
                                highest_score = score
                                highest_rated_paper = paper_analysis
                    
                    if highest_rated_paper and highest_rated_paper.get('focus'):
                        interest_focuses[interest] = f"🎯 **{interest} Research Focus**: {highest_rated_paper['focus']}"
                    else:
                        interest_focuses[interest] = f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}."
                else:
                    # This interest wasn't covered in the latest newsletter
                    interest_focuses[interest] = f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}."
            
            return interest_focuses
                
        except Exception as e:
            logger.error(f"Error getting highest rated paper focus per interest: {e}")
            # Return default messages for each interest
            return {interest: f"🔬 **{interest}**: Stay updated with cutting-edge developments in {interest}." 
                   for interest in user_interests}
