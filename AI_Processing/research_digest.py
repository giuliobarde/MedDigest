from Data_Classes.classes import Paper, PaperAnalysis
from Data_Retrieval.data_retrieval import ArxivClient
from AI_Processing.paper_analyzer import PaperAnalyzer
from typing import List, Dict
import logging
import time
import datetime
import json
import re

logger = logging.getLogger(__name__)


class ResearchDigest:
    """
    Main class for generating medical research digests.
    
    This class orchestrates the process of:
    1. Fetching medical research papers from arXiv
    2. Analyzing papers using AI to extract key information
    3. Organizing findings by medical specialty
    4. Generating comprehensive summaries and insights
    """
    
    def __init__(self, api_key: str):
        """
        Initialize the research digest generator.
        
        Args:
            api_key (str): API key for the AI service
        """
        self.arxiv_client = ArxivClient()
        self.analyzer = PaperAnalyzer(api_key)
        self.llm = self.analyzer.llm  # Get LLM instance from analyzer
        self.specialty_data: Dict[str, Dict] = {}
    
    def generate_digest(self, search_query: str = "all:medical", max_results: int = 10) -> Dict:
        """
        Generate a research digest for medical papers.
        
        Args:
            search_query (str): The search query to use for finding papers
            max_results (int): Maximum number of papers to analyze
            
        Returns:
            Dict: The digest summary as a dictionary
            
        Note:
            The digest includes paper analysis, specialty categorization,
            and AI-generated summaries of key findings.
        """
        logger.info("Fetching papers from arXiv...")
        papers = self.arxiv_client.fetch_papers(search_query)
        logger.info(f"Found {len(papers)} papers")
        
        self._analyze_papers(papers)
        self._display_summary()
        time.sleep(60) # wait 1 minute before generating the digest
        return self._digest_summary()
    
    def _analyze_papers(self, papers: List[Paper]) -> None:
        """
        Analyze the fetched papers using AI.
        
        Args:
            papers (List[Paper]): List of papers to analyze
            
        Note:
            Each paper is analyzed to determine its specialty,
            key concepts, and main findings.
        """
        logger.info("Analyzing papers with AI...")
        
        for i, paper in enumerate(papers, 1):
            logger.info(f"Analyzing paper {i}/{len(papers)}: {paper.title[:80]}...")
            
            analysis = self.analyzer.analyze_paper(paper)
            if not analysis:
                continue
                
            self._update_specialty_data(paper, analysis)
    
    def _update_specialty_data(self, paper: Paper, analysis: PaperAnalysis) -> None:
        """
        Update the specialty data with the paper analysis.
        
        Args:
            paper (Paper): The analyzed paper
            analysis (PaperAnalysis): The AI analysis results
            
        Note:
            This method organizes papers by specialty and maintains
            metadata including keywords and author networks.
        """
        if analysis.specialty not in self.specialty_data:
            self.specialty_data[analysis.specialty] = {
                "papers": [],
                "all_keywords": [],
                "author_network": set()
            }
        
        self.specialty_data[analysis.specialty]["papers"].append({
            "id": paper.paper_id,
            "title": paper.title,
            "authors": paper.authors,
            "keywords": analysis.keywords,
            "focus": analysis.focus,
            "date": paper.published.strftime("%Y-%m-%d")
        })
        self.specialty_data[analysis.specialty]["all_keywords"].extend(analysis.keywords)
        self.specialty_data[analysis.specialty]["author_network"].update(paper.authors)
    
    def _display_summary(self) -> None:
        """
        Display the research summary organized by specialty.
        
        Note:
            This method provides a detailed breakdown of:
            - Number of papers per specialty
            - Recent papers and their focus
            - Top research terms and their frequency
        """
        logger.info("\n" + "="*60)
        logger.info("MEDICAL RESEARCH SUMMARY BY SPECIALTY:")
        logger.info("="*60)
        
        for specialty, data in sorted(
            self.specialty_data.items(), 
            key=lambda x: len(x[1]["papers"]), 
            reverse=True
        ):
            num_papers = len(data["papers"])
            num_authors = len(data["author_network"])
            
            logger.info(f"\n{specialty.upper()} ({num_papers} papers, {num_authors} unique authors)")
            logger.info("-"*50)
            
            # Recent papers
            logger.info("\nRecent Papers:")
            for j, paper in enumerate(data["papers"][:3], 1):
                logger.info(f"  {j}. [{paper['date']}] {paper['title'][:60]}...")
                logger.info(f"     Focus: {paper['focus'][:80]}...")
            
            # Top keywords
            keyword_freq = {}
            for kw in data["all_keywords"]:
                keyword_freq[kw.lower()] = keyword_freq.get(kw.lower(), 0) + 1
            
            logger.info("\nTop Research Terms:")
            top_keywords = sorted(keyword_freq.items(), key=lambda x: x[1], reverse=True)[:8]
            for keyword, count in top_keywords:
                logger.info(f"  • {keyword} ({count} papers)")

    def _extract_json_from_response(self, response_text: str) -> Dict:
        """
        Extract JSON object from LLM response that might contain additional text.
        
        Args:
            response_text (str): The full response from the LLM
            
        Returns:
            Dict: Parsed JSON object
            
        Raises:
            json.JSONDecodeError: If no valid JSON is found
        """
        # Try to find JSON object in the response
        # Look for content between { and } that spans multiple lines
        json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
        
        # Find all potential JSON objects
        matches = re.findall(json_pattern, response_text, re.DOTALL)
        
        for match in matches:
            try:
                # Try to parse each potential JSON match
                parsed_json = json.loads(match)
                # Verify it has the expected structure
                expected_keys = ['executive_summary', 'key_discoveries', 'emerging_trends', 
                               'cross_specialty_insights', 'clinical_implications', 
                               'research_gaps', 'future_directions']
                if any(key in parsed_json for key in expected_keys):
                    return parsed_json
            except json.JSONDecodeError:
                continue
        
        # If no JSON found in regex matches, try to find JSON by looking for braces
        start_brace = response_text.find('{')
        end_brace = response_text.rfind('}')
        
        if start_brace != -1 and end_brace != -1 and end_brace > start_brace:
            potential_json = response_text[start_brace:end_brace + 1]
            try:
                return json.loads(potential_json)
            except json.JSONDecodeError:
                pass
        
        # If still no valid JSON, raise an error
        raise json.JSONDecodeError("No valid JSON found in response", response_text, 0)

    def _digest_summary(self) -> Dict:
        """
        Generate a concise AI-powered summary of key findings across all papers.
        Returns a dictionary that can be used by the Newsletter class.
        
        Returns:
            Dict: The digest summary as a dictionary
        """

        # Collect all paper information for comprehensive analysis
        all_papers_info = []
        specialty_breakdown = {}

        for specialty, data in self.specialty_data.items():
            specialty_breakdown[specialty] = len(data["papers"])
            for paper in data["papers"]:
                paper_summary = {
                    "title": paper["title"],
                    "specialty": specialty,
                    "focus": paper["focus"],
                    "date": paper["date"],
                    "authors": paper["authors"],
                    "keywords": paper["keywords"]
                }
                all_papers_info.append(paper_summary)

        # If no papers were successfully analyzed, return a default structure
        if not all_papers_info:
            logger.warning("No papers were successfully analyzed. Returning empty digest.")
            return {
                "executive_summary": "No papers were successfully analyzed in this digest cycle.",
                "key_discoveries": [],
                "emerging_trends": [],
                "cross_specialty_insights": [],
                "clinical_implications": [],
                "research_gaps": [],
                "future_directions": [],
                "date_generated": datetime.datetime.now().strftime("%Y-%m-%d"),
                "total_papers": 0,
                "specialties": []
            }

        # Create comprehensive prompt for combined analysis
        try:
            # Prepare paper summaries for prompt
            papers_text = []
            for i, paper in enumerate(all_papers_info, 1):
                paper_text = f"""
                Paper {i}:
                Title: {paper['title']}
                Specialty: {paper['specialty']}
                Focus: {paper['focus']}
                Date: {paper['date']}
                Authors: {paper['authors']}
                Keywords: {paper['keywords']}
                """
                papers_text.append(paper_text)

            combined_papers = '\n'.join(papers_text)

            # System prompt that defines the AI's role and analysis requirements
            SYSTEM_ROLE = """
            You are an expert medical research analyst with deep knowledge across all medical specialties. 
            Your task is to summarize and present the key findings of recently published papers across multiple medical specialties and how they interact with each other.
            You must respond with ONLY a valid JSON object, no additional text before or after.
            """

            prompt = f"""
            Analyze this collection of {len(all_papers_info)} medical research papers published this past week and provide a comprehensive digest:
            
            PAPERS TO ANALYZE:
            {combined_papers}
            
            SPECIALTY BREAKDOWN:
            {', '.join([f"{spec}: {count} papers" for spec, count in specialty_breakdown.items()])}
            
            Provide a comprehensive analysis with the following sections. Respond with ONLY a valid JSON object:
            
            {{
                "executive_summary": "A 2-3 paragraph overview of the entire research collection",
                "key_discoveries": ["List of top 10 most significant findings across all papers"],
                "emerging_trends": ["List of 3-4 major trends or patterns identified across multiple papers"],
                "cross_specialty_insights": ["How different medical fields are interconnecting in this research"],
                "clinical_implications": ["Potential impact on medical practice and patient care"],
                "research_gaps": ["Areas that need further investigation"],
                "future_directions": ["Where this collective research is heading"]
            }}
            
            Provide actionable insights that synthesize information across all papers rather than discussing individual studies. 
            Only provide insights based on the material you have been provided with.
            """

            response = self.llm.invoke(
                input=[
                    {"role": "system", "content": SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ]
            )

            # Extract response text
            if hasattr(response, 'content'):
                response_text = response.content
            elif isinstance(response, dict) and 'content' in response:
                response_text = response['content']
            else:
                response_text = str(response)

            # Try to extract and parse JSON from the response
            try:
                digest_json = self._extract_json_from_response(response_text)
                
                # Add metadata
                digest_json['date_generated'] = datetime.datetime.now().strftime("%Y-%m-%d")
                digest_json['total_papers'] = len(all_papers_info)
                digest_json['specialties'] = list(specialty_breakdown.keys())
                digest_json['papers'] = all_papers_info
                logger.info("Successfully generated digest summary")
                return digest_json

            except json.JSONDecodeError as e:
                logger.error(f"Could not parse LLM response as JSON: {e}")
                logger.error(f"Raw response: {response_text}")
                
                # Return a fallback structure
                return {
                    "executive_summary": "Error occurred while generating AI summary. Raw analysis data available.",
                    "key_discoveries": [f"Analysis of {len(all_papers_info)} papers across {len(specialty_breakdown)} specialties"],
                    "emerging_trends": ["Unable to generate AI analysis due to parsing error"],
                    "cross_specialty_insights": ["Manual review of papers recommended"],
                    "clinical_implications": ["Individual paper review needed for clinical insights"],
                    "research_gaps": ["AI analysis unavailable"],
                    "future_directions": ["Manual analysis required"],
                    "date_generated": datetime.datetime.now().strftime("%Y-%m-%d"),
                    "total_papers": len(all_papers_info),
                    "specialties": list(specialty_breakdown.keys()),
                    "error": "JSON parsing failed"
                }
                
        except Exception as e:
            logger.error(f"Exception during digest summary: {e}")
            # Return a fallback structure
            return {
                "executive_summary": "Error occurred during digest generation.",
                "key_discoveries": [],
                "emerging_trends": [],
                "cross_specialty_insights": [],
                "clinical_implications": [],
                "research_gaps": [],
                "future_directions": [],
                "date_generated": datetime.datetime.now().strftime("%Y-%m-%d"),
                "total_papers": len(all_papers_info) if 'all_papers_info' in locals() else 0,
                "specialties": list(specialty_breakdown.keys()) if 'specialty_breakdown' in locals() else [],
                "error": str(e)
            }