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
    
    # High Impact Methodologies/Techniques (Evidence Level 1-2)
    HIGH_IMPACT_METHODOLOGIES = [
        # Clinical Trial Methodologies
        "Randomized Controlled Trial (RCT)",
        "Double-blind Randomized Controlled Trial",
        "Triple-blind Randomized Controlled Trial",
        "Cluster Randomized Controlled Trial",
        "Crossover Randomized Controlled Trial",
        "Adaptive Randomized Trial",
        "Pragmatic Clinical Trial",
        "Phase III Clinical Trial",
        "Phase IV Post-marketing Surveillance",
        "Multi-center Clinical Trial",
        "International Multi-center Trial",
        
        # Meta-analysis and Systematic Reviews
        "Systematic Review with Meta-analysis",
        "Network Meta-analysis",
        "Individual Patient Data Meta-analysis",
        "Cochrane Systematic Review",
        "Living Systematic Review",
        "Umbrella Review",
        "Scoping Review with Meta-analysis",
        
        # Advanced Statistical Methods
        "Bayesian Randomized Controlled Trial",
        "Mendelian Randomization",
        "Propensity Score Matching",
        "Instrumental Variable Analysis",
        "Regression Discontinuity Design",
        "Difference-in-Differences Analysis",
        "Interrupted Time Series Analysis",
        "Causal Inference Methods",
        
        # Genomics and Precision Medicine
        "Genome-Wide Association Study (GWAS)",
        "Whole Genome Sequencing",
        "Whole Exome Sequencing",
        "Pharmacogenomics Study",
        "Polygenic Risk Score Analysis",
        "Multi-omics Integration",
        "Single-cell RNA Sequencing",
        "Spatial Transcriptomics",
        
        # Advanced AI/ML in Medicine
        "Deep Learning for Medical Imaging",
        "Federated Learning in Healthcare",
        "Explainable AI in Clinical Decision Making",
        "Large Language Models for Medical Tasks",
        "Computer Vision for Pathology",
        "Reinforcement Learning for Treatment Optimization",
        "Transfer Learning in Medical AI",
        "Multi-modal AI for Healthcare",
        
        # Regulatory and Implementation
        "FDA Breakthrough Therapy Designation",
        "Real-World Evidence (RWE) Study",
        "Comparative Effectiveness Research",
        "Health Technology Assessment",
        "Implementation Science Study",
        "Pragmatic-Explanatory Continuum Indicator Summary (PRECIS-2)",
    ]

    # Medium Impact Methodologies/Techniques (Evidence Level 3-4)
    MEDIUM_IMPACT_METHODOLOGIES = [
        # Observational Studies
        "Prospective Cohort Study",
        "Retrospective Cohort Study",
        "Case-Control Study",
        "Nested Case-Control Study",
        "Cross-sectional Study",
        "Longitudinal Study",
        "Population-based Study",
        "Registry-based Study",
        "Electronic Health Record (EHR) Study",
        
        # Phase I/II Trials
        "Phase I Clinical Trial",
        "Phase II Clinical Trial",
        "Dose-escalation Study",
        "Pilot Clinical Trial",
        "Feasibility Study",
        "Proof-of-Concept Study",
        "First-in-Human Study",
        
        # Diagnostic Studies
        "Diagnostic Accuracy Study",
        "Biomarker Validation Study",
        "Screening Study",
        "Predictive Model Development",
        "Prognostic Model Validation",
        "Risk Stratification Study",
        
        # Experimental Methods
        "In Vivo Animal Study",
        "Preclinical Study",
        "Translational Research",
        "Mechanistic Study",
        "Pharmacokinetic/Pharmacodynamic Study",
        "Toxicology Study",
        
        # Survey and Qualitative Methods
        "Cross-sectional Survey",
        "Longitudinal Survey",
        "Mixed Methods Study",
        "Qualitative Study",
        "Ethnographic Study",
        "Phenomenological Study",
        "Grounded Theory Study",
        
        # Intermediate AI/ML Methods
        "Machine Learning for Risk Prediction",
        "Natural Language Processing for Clinical Notes",
        "Computer-Aided Diagnosis",
        "Radiomics Analysis",
        "Predictive Modeling",
        "Time Series Analysis for Healthcare",
        "Survival Analysis with ML",
        
        # Specialized Techniques
        "Proteomics Study",
        "Metabolomics Study",
        "Microbiome Analysis",
        "Epigenetic Study",
        "Immunophenotyping",
        "Flow Cytometry Analysis",
        "Mass Spectrometry Analysis",
        "Pharmacovigilance Study",
        
        # Health Services Research
        "Health Economic Evaluation",
        "Quality of Life Assessment",
        "Patient-Reported Outcome Measures (PROMs)",
        "Cost-effectiveness Analysis",
        "Budget Impact Analysis",
        "Markov Modeling",
    ]

    # Low Impact Methodologies/Techniques (Evidence Level 5 and below)
    LOW_IMPACT_METHODOLOGIES = [
        # Case Studies and Reports
        "Case Report",
        "Case Series",
        "Single Case Study",
        "Multiple Case Report",
        "Case-based Review",
        
        # Basic Laboratory Methods
        "In Vitro Study",
        "Cell Culture Study",
        "Tissue Culture Study",
        "Biochemical Assay",
        "Enzyme Activity Assay",
        "Protein Expression Analysis",
        "Western Blot Analysis",
        "PCR Analysis",
        "qPCR Analysis",
        "ELISA",
        "Immunohistochemistry",
        "Histological Analysis",
        
        # Basic Animal Models
        "Mouse Model Study",
        "Rat Model Study",
        "Cell Line Study",
        "Xenograft Model",
        "Organoid Study",
        
        # Descriptive Studies
        "Descriptive Study",
        "Ecological Study",
        "Correlation Study",
        "Prevalence Study",
        "Incidence Study",
        "Mortality Study",
        
        # Reviews and Commentaries
        "Literature Review",
        "Narrative Review",
        "Editorial",
        "Commentary",
        "Opinion Piece",
        "Perspective Article",
        "Letter to Editor",
        "Short Communication",
        
        # Basic Statistical Methods
        "Descriptive Statistics",
        "Correlation Analysis",
        "Simple Linear Regression",
        "Chi-square Test",
        "T-test Analysis",
        "ANOVA",
        "Basic Survival Analysis",
        
        # Theoretical and Conceptual
        "Theoretical Model",
        "Conceptual Framework",
        "Hypothesis Generation",
        "Mathematical Model",
        "Simulation Study",
        "Modeling Study",
        
        # Basic Surveys
        "Cross-sectional Survey (Small Sample)",
        "Convenience Sample Survey",
        "Online Survey",
        "Questionnaire Study",
        "Interview Study",
        "Focus Group Study",
        
        # Basic Imaging
        "Imaging Study (Descriptive)",
        "Radiological Case Series",
        "Ultrasound Study",
        "CT Scan Analysis",
        "MRI Analysis",
        "X-ray Analysis",
        
        # Preliminary Work
        "Pilot Study (Small N)",
        "Preliminary Results",
        "Feasibility Assessment",
        "Method Development",
        "Protocol Development",
        "Validation Study (Small Scale)",
    ]
    
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
                ],
                output_type="json"
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
        
    # Usage example for API-based methodology detection
    def detect_methodologies_api_call(paper_text: str, methodology_list: list) -> list:
        """
        Placeholder function for API call to detect methodologies in paper text.
        
        Args:
            paper_text (str): Full text of the paper
            methodology_list (list): List of methodologies to check for
            
        Returns:
            list: Detected methodologies from the input list
        """
    
    def _calculate_paper_score(detected_methodologies: dict) -> float:
        """
        Calculate score based on detected methodologies.
    
        Args:
            detected_methodologies (dict): Dictionary with keys 'high', 'medium', 'low'
                                        and values as lists of detected methodologies
                                        
        Returns:
            float: Calculated methodology score
        """
        
    
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