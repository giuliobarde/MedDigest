# Local imports for data structures and AI processing
from Data_Classes.classes import Paper, PaperAnalysis
from langchain_groq import ChatGroq
import logging
import re
import json
import hashlib
from typing import Optional
from utils.token_monitor import TokenMonitor, TokenUsage

# Configure logging for this module
logger = logging.getLogger(__name__)


class PaperAnalyzer:
    """
    Analyzes medical research papers using AI to extract key information and categorize content.
    
    This class uses the Groq LLM to analyze medical papers and extract:
    - Primary medical specialty
    - Key medical concepts and terminology
    - Concise summary of findings
    - Deterministic interest score based on content analysis
    """
    
    # Set of valid medical specialties for categorization
    VALID_SPECIALTIES = {
        'Cardiology', 'Oncology', 'Radiology', 'Neurology', 
        'Surgery', 'Psychiatry', 'Endocrinology', 'General Medicine',
        'Dermatology', 'Gastroenterology', 'Pulmonology', 'Orthopedics',
        'Ophthalmology', 'Urology', 'Gynecology', 'Pediatrics',
        'Emergency Medicine', 'Anesthesiology', 'Pathology', 'Immunology',
        'Infectious Disease', 'Nephrology', 'Hematology', 'Rheumatology',
        'Medical Imaging', 'Biomedical Engineering', 'Medical AI', 'Clinical Research'
    }
    
    # Keywords that indicate high-impact research
    HIGH_IMPACT_KEYWORDS = {
        'breakthrough', 'novel', 'innovative', 'first', 'groundbreaking', 'revolutionary',
        'significant', 'substantial', 'major', 'landmark', 'paradigm', 'transformative',
        'clinical trial', 'randomized controlled trial', 'rct', 'meta-analysis', 
        'systematic review', 'multi-center', 'multicenter', 'phase iii', 'phase 3',
        'fda approved', 'fda approval', 'regulatory approval', 'clinical guidelines',
        'treatment outcome', 'patient outcome', 'mortality reduction', 'survival',
        'efficacy', 'effectiveness', 'safety profile', 'adverse events'
    }
    
    # Keywords that indicate moderate impact
    MODERATE_IMPACT_KEYWORDS = {
        'improvement', 'enhancement', 'optimization', 'validation', 'evaluation',
        'assessment', 'comparison', 'analysis', 'investigation', 'study',
        'pilot study', 'feasibility', 'preliminary', 'observational',
        'retrospective', 'prospective', 'cohort', 'case-control',
        'diagnostic', 'predictive', 'prognostic', 'biomarker', 'screening'
    }
    
    # Keywords that indicate lower impact
    LOW_IMPACT_KEYWORDS = {
        'case report', 'case series', 'single case', 'letter', 'editorial',
        'commentary', 'review', 'survey', 'opinion', 'hypothesis',
        'theoretical', 'conceptual', 'in vitro', 'cell culture', 'animal model',
        'preliminary findings', 'limited sample', 'small cohort'
    }
    
    # System prompt that defines the AI's role and analysis requirements
    SYSTEM_ROLE = """
    You are an expert medical research analyst with deep knowledge across all medical specialties. 
    Your task is to analyze medical research papers and provide accurate categorization and key insights.
    Focus on:
    - Identifying the primary medical specialty based on the paper's content and methodology
    - Extracting the most relevant medical concepts and terminology
    - Providing a concise but comprehensive summary that captures the key findings
    - Identifying key characteristics for interest scoring (study type, sample size, clinical relevance, etc.)
    
    Be precise and professional in your analysis. Use consistent terminology and avoid subjective language.
    """
    
    def __init__(self, api_key: str, token_monitor: Optional[TokenMonitor] = None):
        """
        Initialize the paper analyzer with Groq LLM.
        
        Args:
            api_key (str): API key for Groq LLM service
            token_monitor (Optional[TokenMonitor]): Token monitor instance for rate limiting
        """
        # Use temperature=0.0 for deterministic responses
        self.llm = ChatGroq(api_key=api_key, model="llama3-8b-8192", temperature=0.0)
        self.token_monitor = token_monitor or TokenMonitor(max_tokens_per_minute=15500)
    
    def analyze_paper(self, paper: Paper) -> tuple[Optional[PaperAnalysis], Optional[TokenUsage]]:
        """
        Analyze a paper using AI to determine its specialty and key concepts.
        
        Args:
            paper (Paper): The paper to analyze
            
        Returns:
            tuple[Optional[PaperAnalysis], Optional[TokenUsage]]: Analysis results and token usage if successful, (None, None) if analysis fails
            
        Note:
            The analysis includes specialty categorization, keyword extraction,
            and a focused summary of the paper's main findings.
        """
        prompt = self._create_analysis_prompt(paper)
        try:
            input_text = self.SYSTEM_ROLE + prompt
            input_tokens = self.token_monitor.count_tokens(input_text)
            response = self.llm.invoke(
                input=[
                    {"role": "system", "content": self.SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ]
            )
            output_tokens = self.token_monitor.count_tokens(str(response.content))
            usage = self.token_monitor.record_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            # Parse the basic analysis
            result = self._parse_analysis_response(str(response.content))
            if result:
                # Calculate deterministic interest score
                interest_score, score_breakdown = self._calculate_interest_score(paper, result)
                # Update the analysis with the calculated score
                result = PaperAnalysis(
                    specialty=result.specialty,
                    keywords=result.keywords,
                    focus=result.focus,
                    interest_score=interest_score,
                    score_breakdown=score_breakdown # Add score breakdown to analysis
                )
            
            return result, usage
        except Exception as e:
            logger.error(f"Error analyzing paper {paper.paper_id}: {str(e)}")
            return None, None
    
    def _calculate_interest_score(self, paper: Paper, analysis: PaperAnalysis) -> tuple[float, dict]:
        """
        Calculate a deterministic interest score based on paper content and analysis.
        
        Args:
            paper (Paper): The original paper
            analysis (PaperAnalysis): The AI analysis results
            
        Returns:
            tuple[float, dict]: Interest score between 0.0 and 10.0, and detailed breakdown
        """
        # Combine all text for analysis
        full_text = f"{paper.title} {paper.abstract} {paper.conclusion} {' '.join(analysis.keywords)}".lower()
        
        # Initialize detailed scoring breakdown
        score_breakdown = {
            'base_score': 0.0,
            'study_type': 0.0,
            'clinical_impact_keywords': 0.0,
            'sample_size': 0.0,
            'clinical_timeline': 0.0,
            'methodological_innovation': 0.0,
            'innovation_indicators': 0.0,
            'hash_variance': 0.0,
            'total_score': 0.0,
            'details': {}
        }
        
        score = 6.0
        score_breakdown['base_score'] = 6.0
        score_breakdown['details']['base_score_reason'] = "arXiv papers get higher base score (6.0) for cutting-edge research"
        
        # Factor 1: Study type and methodology (±2.0 points)
        study_type_score = 0.0
        study_type_reason = "No specific study type identified"
        
        if any(keyword in full_text for keyword in ['randomized controlled trial', 'rct', 'clinical trial']):
            study_type_score = 2.0
            study_type_reason = "Randomized controlled trial (+2.0)"
        elif any(keyword in full_text for keyword in ['meta-analysis', 'systematic review']):
            study_type_score = 1.8
            study_type_reason = "Meta-analysis/systematic review (+1.8)"
        elif any(keyword in full_text for keyword in ['multi-center', 'multicenter', 'phase iii', 'phase 3']):
            study_type_score = 1.5
            study_type_reason = "Multi-center/Phase III study (+1.5)"
        elif any(keyword in full_text for keyword in ['prospective', 'cohort']):
            study_type_score = 1.0
            study_type_reason = "Prospective/cohort study (+1.0)"
        elif any(keyword in full_text for keyword in ['retrospective', 'case-control']):
            study_type_score = 0.5
            study_type_reason = "Retrospective/case-control study (+0.5)"
        elif any(keyword in full_text for keyword in ['case report', 'case series', 'single case']):
            study_type_score = -1.5
            study_type_reason = "Case report/series (-1.5)"
        elif any(keyword in full_text for keyword in ['in vitro', 'cell culture', 'animal model']):
            study_type_score = -1.0
            study_type_reason = "In vitro/animal model (-1.0)"
        
        score += study_type_score
        score_breakdown['study_type'] = study_type_score
        score_breakdown['details']['study_type_reason'] = study_type_reason
        
        # Factor 2: Clinical impact keywords (±1.5 points)
        high_impact_count = sum(1 for keyword in self.HIGH_IMPACT_KEYWORDS if keyword in full_text)
        moderate_impact_count = sum(1 for keyword in self.MODERATE_IMPACT_KEYWORDS if keyword in full_text)
        low_impact_count = sum(1 for keyword in self.LOW_IMPACT_KEYWORDS if keyword in full_text)
        
        high_impact_score = min(high_impact_count * 0.3, 1.5)
        moderate_impact_score = min(moderate_impact_count * 0.1, 0.5)
        low_impact_penalty = min(low_impact_count * 0.2, 1.0)
        
        clinical_impact_score = high_impact_score + moderate_impact_score - low_impact_penalty
        score += clinical_impact_score
        score_breakdown['clinical_impact_keywords'] = clinical_impact_score
        score_breakdown['details']['clinical_impact_breakdown'] = {
            'high_impact_keywords': high_impact_count,
            'high_impact_score': high_impact_score,
            'moderate_impact_keywords': moderate_impact_count,
            'moderate_impact_score': moderate_impact_score,
            'low_impact_keywords': low_impact_count,
            'low_impact_penalty': low_impact_penalty
        }
        
        # Factor 3: Sample size indicators (±1.0 point)
        sample_size_score = 0.0
        sample_size_reason = "No specific sample size indicators"
        
        if any(keyword in full_text for keyword in ['large cohort', 'large sample', 'n >']) or \
           any(f'n = {i}' in full_text for i in range(1000, 10000)):
            sample_size_score = 1.0
            sample_size_reason = "Large sample size (+1.0)"
        elif any(keyword in full_text for keyword in ['small sample', 'limited sample', 'pilot']) or \
             any(f'n = {i}' in full_text for i in range(1, 50)):
            sample_size_score = -0.5
            sample_size_reason = "Small sample size (-0.5)"
        
        score += sample_size_score
        score_breakdown['sample_size'] = sample_size_score
        score_breakdown['details']['sample_size_reason'] = sample_size_reason
        
        # IMPROVEMENT 2: Clinical Relevance Weighting with Timeline
        # Factor 4: Clinical Impact Timeline (±3.0 points)
        clinical_timeline_score = 0.0
        clinical_timeline_reason = "No immediate clinical impact indicators"
        
        if any(keyword in full_text for keyword in ['fda approved', 'fda approval', 'regulatory approval', 'clinical guidelines', 'treatment guidelines']):
            clinical_timeline_score = 3.0
            clinical_timeline_reason = "Immediate clinical impact (0-6 months): FDA approval/guidelines (+3.0)"
        elif any(keyword in full_text for keyword in ['phase iii', 'phase 3', 'phase ii', 'phase 2', 'clinical trial', 'randomized controlled trial']):
            clinical_timeline_score = 2.0
            clinical_timeline_reason = "Short-term clinical potential (6-24 months): Phase II/III trials (+2.0)"
        elif any(keyword in full_text for keyword in ['patient outcome', 'treatment outcome', 'mortality reduction', 'survival benefit', 'efficacy', 'effectiveness']):
            clinical_timeline_score = 1.0
            clinical_timeline_reason = "Medium-term potential (2-5 years): Patient outcomes (+1.0)"
        elif any(keyword in full_text for keyword in ['biomarker', 'diagnostic', 'predictive', 'prognostic', 'screening']):
            clinical_timeline_score = 0.5
            clinical_timeline_reason = "Long-term potential (5+ years): Biomarkers/diagnostics (+0.5)"
        
        score += clinical_timeline_score
        score_breakdown['clinical_timeline'] = clinical_timeline_score
        score_breakdown['details']['clinical_timeline_reason'] = clinical_timeline_reason
        
        # IMPROVEMENT 3: Methodological Innovation
        # Factor 5: AI/ML Innovation (±1.5 points)
        ai_innovation_score = 0.0
        ai_innovation_details = []
        
        # New AI/ML techniques
        if any(keyword in full_text for keyword in ['novel algorithm', 'new method', 'proposed approach', 'introduced method']):
            ai_innovation_score += 1.0
            ai_innovation_details.append("New AI/ML technique (+1.0)")
        elif any(keyword in full_text for keyword in ['artificial intelligence', 'machine learning', 'deep learning', 'neural network']):
            ai_innovation_score += 0.5
            ai_innovation_details.append("AI/ML application (+0.5)")
        
        # Novel datasets or tools
        if any(keyword in full_text for keyword in ['new dataset', 'novel dataset', 'benchmark dataset', 'open source', 'github', 'code available']):
            ai_innovation_score += 0.8
            ai_innovation_details.append("Novel dataset/open source (+0.8)")
        elif any(keyword in full_text for keyword in ['tool', 'software', 'framework', 'platform']):
            ai_innovation_score += 0.6
            ai_innovation_details.append("Software/tool (+0.6)")
        
        # Reproducible research
        if any(keyword in full_text for keyword in ['reproducible', 'replication', 'validation', 'cross-validation']):
            ai_innovation_score += 0.4
            ai_innovation_details.append("Reproducible research (+0.4)")
        
        # Cross-disciplinary innovation
        if any(keyword in full_text for keyword in ['multimodal', 'multi-modal', 'fusion', 'integration', 'hybrid']):
            ai_innovation_score += 0.3
            ai_innovation_details.append("Cross-disciplinary (+0.3)")
        
        ai_innovation_score = min(ai_innovation_score, 1.5)
        score += ai_innovation_score
        score_breakdown['methodological_innovation'] = ai_innovation_score
        score_breakdown['details']['ai_innovation_details'] = ai_innovation_details if ai_innovation_details else ["No methodological innovation detected"]
        
        # Factor 6: Innovation indicators (legacy, now enhanced above)
        innovation_indicators_score = 0.0
        innovation_indicators_reason = "No additional innovation indicators"
        
        if any(keyword in full_text for keyword in ['novel', 'innovative', 'first', 'breakthrough']):
            innovation_indicators_score = 0.5
            innovation_indicators_reason = "Innovation keywords (+0.5)"
        elif any(keyword in full_text for keyword in ['artificial intelligence', 'machine learning', 'deep learning']):
            innovation_indicators_score = 0.3
            innovation_indicators_reason = "AI/ML keywords (+0.3)"
        
        score += innovation_indicators_score
        score_breakdown['innovation_indicators'] = innovation_indicators_score
        score_breakdown['details']['innovation_indicators_reason'] = innovation_indicators_reason
        
        # Factor 7: Add deterministic variance based on content hash
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        hash_factor = (int(content_hash[:8], 16) % 100) / 1000.0  # 0.000 to 0.099
        score += hash_factor
        score_breakdown['hash_variance'] = hash_factor
        score_breakdown['details']['hash_variance_reason'] = f"Deterministic variance based on content hash (+{hash_factor:.3f})"
        
        # Ensure score is within bounds
        score = max(0.0, min(10.0, score))
        
        # Update final score in breakdown
        score_breakdown['total_score'] = round(score, 1)
        
        # Round to 1 decimal place for consistency
        return round(score, 1), score_breakdown
    
    def get_high_interest_papers(self, papers_with_analyses: list) -> list:
        """
        Filter papers to get only those with high interest scores (>= 7.0).
        
        Args:
            papers_with_analyses (list): List of papers with their analysis results
            
        Returns:
            list: Papers with high interest scores, sorted by score (highest first)
        """
        high_interest = []
        for paper_data in papers_with_analyses:
            if 'interest_score' in paper_data and paper_data['interest_score'] >= 7.0:
                high_interest.append(paper_data)
        
        # Sort by interest score (highest first)
        high_interest.sort(key=lambda x: x['interest_score'], reverse=True)
        return high_interest
    
    def get_papers_by_interest_range(self, papers_with_analyses: list, min_score: float = 0.0, max_score: float = 10.0) -> list:
        """
        Get papers within a specific interest score range.
        
        Args:
            papers_with_analyses (list): List of papers with their analysis results
            min_score (float): Minimum interest score (inclusive)
            max_score (float): Maximum interest score (inclusive)
            
        Returns:
            list: Papers within the specified interest score range, sorted by score
        """
        filtered_papers = []
        for paper_data in papers_with_analyses:
            if 'interest_score' in paper_data and min_score <= paper_data['interest_score'] <= max_score:
                filtered_papers.append(paper_data)
        
        # Sort by interest score (highest first)
        filtered_papers.sort(key=lambda x: x['interest_score'], reverse=True)
        return filtered_papers
    
    def _create_analysis_prompt(self, paper: Paper) -> str:
        """
        Create the prompt for paper analysis.
        
        Args:
            paper (Paper): The paper to analyze
            
        Returns:
            str: Formatted prompt for the LLM
            
        Note:
            The prompt includes paper metadata and specific instructions
            for the analysis format and requirements.
        """
        return f"""
        Analyze this medical research paper and provide a JSON response with the exact structure shown below.
        
        Title: {paper.title}
        Abstract: {paper.abstract}
        Conclusion: {paper.conclusion}
        Authors: {', '.join(paper.authors)}
        arXiv Categories: {', '.join(paper.categories)}
        
        Instructions:
        1. Write a 2-3 sentence summary of the paper's key findings
        2. Identify the primary medical specialty from this list: {', '.join(sorted(self.VALID_SPECIALTIES))}
        3. Extract 5 key medical concepts/terms from this research
        4. Identify study characteristics (study type, sample size, clinical relevance, etc.)
        
        IMPORTANT: Return ONLY a valid JSON object with this exact structure:
        {{
            "summary": "2-3 sentence summary of the paper's key findings",
            "specialty": "exact specialty name from the provided list",
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"],
            "study_type": "type of study (e.g., clinical trial, observational study, etc.)",
            "sample_size_indicator": "indication of sample size (e.g., large, small, not specified)",
            "clinical_relevance": "level of clinical relevance (high, moderate, low)"
        }}
        
        Do not include any text before or after the JSON object. Ensure all quotes are properly escaped.
        """
    
    def _parse_analysis_response(self, response: str) -> Optional[PaperAnalysis]:
        """
        Parse the AI response into a PaperAnalysis object.
        
        Args:
            response (str): Raw response from the LLM
            
        Returns:
            Optional[PaperAnalysis]: Parsed analysis if successful, None if parsing fails
            
        Note:
            This method includes validation of the response format,
            required fields, and specialty categorization.
        """
        try:
            # Clean the response - remove any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            # Find JSON object in the response
            json_match = re.search(r'\{.*\}', cleaned_response, re.DOTALL)
            if not json_match:
                logger.error(f"Could not find JSON in response: {response[:200]}...")
                return None
                
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate and sanitize required fields
            summary = data.get('summary')
            if not isinstance(summary, str):
                summary = str(summary) if summary is not None else ''
            
            keywords = data.get('keywords')
            if not isinstance(keywords, list):
                keywords = []
            else:
                # Ensure all keywords are strings
                keywords = [str(kw) for kw in keywords if isinstance(kw, (str, int, float))]
            keywords = keywords[:5]
            
            specialty = data.get('specialty')
            if not isinstance(specialty, str):
                logger.error(f"Invalid specialty type: {type(specialty)}")
                return None
                
            # Try to match specialty with valid ones (case-insensitive)
            specialty_lower = specialty.lower()
            matched_specialty = None
            for valid_specialty in self.VALID_SPECIALTIES:
                if valid_specialty.lower() == specialty_lower:
                    matched_specialty = valid_specialty
                    break
            
            if not matched_specialty:
                # Try partial matching for common variations
                for valid_specialty in self.VALID_SPECIALTIES:
                    if any(word in specialty_lower for word in valid_specialty.lower().split()):
                        matched_specialty = valid_specialty
                        break
                
                if not matched_specialty:
                    logger.error(f"Invalid specialty: {specialty}")
                    return None
            
            # Return analysis without interest score (will be calculated separately)
            return PaperAnalysis(
                specialty=matched_specialty,
                keywords=keywords,
                focus=summary,
                interest_score=0.0  # Placeholder, will be calculated
            )
            
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {str(e)}")
            logger.error(f"Response content: {response[:300]}...")
            return None
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            logger.error(f"Response content: {response[:300]}...")
            return None