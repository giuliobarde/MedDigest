import datetime
import logging
import requests
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import List, Dict, Set, Optional
from urllib.parse import urlencode
from langchain_groq import ChatGroq
import time
from dotenv import load_dotenv
import os
import json
import re

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@dataclass
class Paper:
    """Data class representing a research paper."""
    paper_id: str
    title: str
    published: datetime.datetime
    abstract: str
    authors: List[str]
    categories: List[str]
    conclusion: str

@dataclass
class PaperAnalysis:
    """Data class representing the analysis of a paper."""
    specialty: str
    keywords: List[str]
    focus: str

class ArxivClient:
    """Client for interacting with the arXiv API."""
    
    BASE_URL = "https://export.arxiv.org/api/query"
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/xml,application/xhtml+xml,text/html;q=0.9',
        }
        self.session = requests.Session()
        self.session.headers.update(self.headers)
    
    def fetch_papers(self, search_query: str, max_results: int = 20) -> List[Paper]:
        """
        Fetch papers from arXiv API with retry logic.
        
        Args:
            search_query: The search query to use
            max_results: Maximum number of results to return
            
        Returns:
            List of Paper objects
        """
        params = {
            "search_query": search_query,
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": max_results,
        }
        
        url = f"{self.BASE_URL}?{urlencode(params)}"
        
        max_retries = 3
        retry_delay = 5  # seconds
        
        for attempt in range(max_retries):
            try:
                logger.info(f"Attempting to fetch papers (attempt {attempt + 1}/{max_retries})...")
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return self._parse_response(response.content)
                
            except requests.exceptions.RequestException as e:
                if attempt < max_retries - 1:
                    logger.warning(f"Request failed: {str(e)}. Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    logger.error(f"Failed to fetch papers after {max_retries} attempts: {str(e)}")
                    raise
        
        return []  # This line should never be reached due to the raise in the loop
    
    def _parse_response(self, content: bytes) -> List[Paper]:
        """Parse the XML response from arXiv."""
        root = ET.fromstring(content)
        ns = {'atom': 'http://www.w3.org/2005/Atom'}
        papers = []
        
        for entry in root.findall('atom:entry', ns):
            paper = Paper(
                paper_id=entry.find('atom:id', ns).text.split('/')[-1],
                title=entry.find('atom:title', ns).text.strip(),
                published=datetime.datetime.strptime(
                    entry.find('atom:published', ns).text, 
                    '%Y-%m-%dT%H:%M:%SZ'
                ).replace(tzinfo=datetime.timezone.utc),
                abstract=entry.find('atom:summary', ns).text.strip(),
                authors=[author.find('atom:name', ns).text for author in entry.findall('atom:author', ns)],
                categories=[cat.get('term') for cat in entry.findall('atom:category', ns)],
                conclusion=entry.find('atom:summary', ns).text.strip()
            )
            papers.append(paper)
        
        return papers

class PaperAnalyzer:
    """Analyzes medical research papers using AI."""
    
    VALID_SPECIALTIES = {
        'Cardiology', 'Oncology', 'Radiology', 'Neurology', 
        'Surgery', 'Psychiatry', 'Endocrinology', 'General Medicine'
    }
    
    SYSTEM_ROLE = """You are an expert medical research analyst with deep knowledge across all medical specialties. 
Your task is to analyze medical research papers and provide accurate categorization and key insights.
Focus on:
- Identifying the primary medical specialty based on the paper's content and methodology
- Extracting the most relevant medical concepts and terminology
- Providing a concise but comprehensive summary that captures the key findings
Be precise and professional in your analysis."""
    
    def __init__(self, api_key: str):
        self.llm = ChatGroq(api_key=api_key, model="llama3-8b-8192")
    
    def analyze_paper(self, paper: Paper) -> Optional[PaperAnalysis]:
        """
        Analyze a paper using AI to determine its specialty and key concepts.
        
        Args:
            paper: The paper to analyze
            
        Returns:
            PaperAnalysis object if successful, None if analysis fails
        """
        prompt = self._create_analysis_prompt(paper)
        
        try:
            response = self.llm.invoke(
                messages=[
                    {"role": "system", "content": self.SYSTEM_ROLE},
                    {"role": "user", "content": prompt}
                ]
            )
            return self._parse_analysis_response(response.content)
        except Exception as e:
            logger.error(f"Error analyzing paper {paper.paper_id}: {str(e)}")
            return None
    
    def _create_analysis_prompt(self, paper: Paper) -> str:
        """Create the prompt for paper analysis."""
        return f"""
        Analyze this medical research paper:
        
        Title: {paper.title}
        Abstract: {paper.abstract[:500]}
        Conclusion: {paper.conclusion}
        Authors: {', '.join(paper.authors[:5])}
        arXiv Categories: {', '.join(paper.categories)}
        
        Provide:
        1. Summary of the paper in one paragraph. A couple of sentences about the abstract and 2-3 sentences about the conclusion.
        2. Medical specialty (ONE of: {', '.join(sorted(self.VALID_SPECIALTIES))})
        3. 5 key medical concepts/terms from this research
        
        Format your response as a JSON object with the following structure:
        {{
            "summary": "summary of the paper",
            "specialty": "medical specialty",
            "keywords": ["keyword1", "keyword2", "keyword3", "keyword4", "keyword5"]
        }}
        """
    
    def _parse_analysis_response(self, response: str) -> Optional[PaperAnalysis]:
        """Parse the AI response into a PaperAnalysis object."""
        try:
            # Find JSON object in the response
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if not json_match:
                logger.error(f"Could not find JSON in response: {response}")
                return None
                
            json_str = json_match.group(0)
            data = json.loads(json_str)
            
            # Validate required fields
            if not all(key in data for key in ['summary', 'specialty', 'keywords']):
                logger.error(f"Missing required fields in response: {data}")
                return None
                
            # Validate specialty
            if data['specialty'] not in self.VALID_SPECIALTIES:
                logger.error(f"Invalid specialty: {data['specialty']}")
                return None
                
            return PaperAnalysis(
                specialty=data['specialty'],
                keywords=data['keywords'][:5],  # Ensure we only take up to 5 keywords
                focus=data['summary']  # Use the summary as the focus
            )
            
        except Exception as e:
            logger.error(f"Error parsing analysis response: {str(e)}")
            return None

class ResearchDigest:
    """Main class for generating medical research digests."""
    
    def __init__(self, api_key: str):
        self.arxiv_client = ArxivClient()
        self.analyzer = PaperAnalyzer(api_key)
        self.llm = self.analyzer.llm  # Get LLM instance from analyzer
        self.specialty_data: Dict[str, Dict] = {}
    
    def generate_digest(self, search_query: str = "all:medical", max_results: int = 20) -> None:
        """
        Generate a research digest for medical papers.
        
        Args:
            search_query: The search query to use
            max_results: Maximum number of papers to analyze
        """
        logger.info("Fetching papers from arXiv...")
        papers = self.arxiv_client.fetch_papers(search_query, max_results)
        logger.info(f"Found {len(papers)} papers")
        
        self._analyze_papers(papers)
        self._display_summary()
        self._digest_summary()
    
    def _analyze_papers(self, papers: List[Paper]) -> None:
        """Analyze the fetched papers."""
        logger.info("Analyzing papers with AI...")
        
        for i, paper in enumerate(papers, 1):
            logger.info(f"Analyzing paper {i}/{len(papers)}: {paper.title[:80]}...")
            
            analysis = self.analyzer.analyze_paper(paper)
            if not analysis:
                continue
                
            self._update_specialty_data(paper, analysis)
    
    def _update_specialty_data(self, paper: Paper, analysis: PaperAnalysis) -> None:
        """Update the specialty data with the paper analysis."""
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
        """Display the research summary by specialty."""
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

    def _digest_summary(self) -> None:
        """Generate a concise AI-powered summary of key findings across all papers."""
        logger.info("\n" + "="*60)
        logger.info("MEDICAL RESEARCH DIGEST SUMMARY")
        logger.info("="*60)
        
        # Prepare data for summary
        summary_data = []
        for specialty, data in self.specialty_data.items():
            for paper in data["papers"]:
                summary_data.append({
                    "specialty": specialty,
                    "title": paper["title"],
                    "focus": paper["focus"],
                    "keywords": paper["keywords"]
                })
        
        if not summary_data:
            logger.info("\nNo papers were analyzed. Please ensure papers were successfully fetched and analyzed.")
            return

        # Create prompt for AI summary using the structured data
        prompt = f"""
        Based on the following medical research papers, provide a 2-3 paragraph summary highlighting the most significant findings and trends. Focus on:
        1. Major breakthroughs or novel approaches
        2. Common themes across different specialties
        3. Potential impact on medical practice

        Papers to analyze:
        {[f"- {p['specialty']}: {p['title']} (Focus: {p['focus']})" for p in summary_data]}

        Provide a concise, engaging summary that would be valuable for medical professionals.
        """
        
        try:
            # Generate AI summary
            response = self.llm.invoke(prompt)
            summary = response.content.strip()
            
            # Display the summary
            logger.info("\nKEY FINDINGS AND TRENDS:")
            logger.info("-"*50)
            logger.info(f"\n{summary}\n")
            
            # Add some basic statistics
            total_papers = sum(len(data["papers"]) for data in self.specialty_data.values())
            specialties = len(self.specialty_data)
            logger.info(f"\nTotal Papers Analyzed: {total_papers}")
            logger.info(f"Number of Specialties: {specialties}")
            
            # Display top keywords across all specialties
            all_keywords = {}
            for specialty, data in self.specialty_data.items():
                for kw in data["all_keywords"]:
                    all_keywords[kw.lower()] = all_keywords.get(kw.lower(), 0) + 1
            
            logger.info("\nTop Research Terms Across All Specialties:")
            top_keywords = sorted(all_keywords.items(), key=lambda x: x[1], reverse=True)[:10]
            for keyword, count in top_keywords:
                logger.info(f"  • {keyword} ({count} papers)")
            
        except Exception as e:
            logger.error(f"Failed to generate AI summary: {str(e)}")
            # Fallback to basic statistics if AI summary fails
            logger.info("\nBasic Research Overview:")
            logger.info("-"*50)
            for specialty, data in sorted(
                self.specialty_data.items(),
                key=lambda x: len(x[1]["papers"]),
                reverse=True
            ):
                logger.info(f"\n{specialty}: {len(data['papers'])} papers")
                logger.info(f"Top keywords: {', '.join(sorted(set(data['all_keywords']))[:5])}")
        
        logger.info("\n" + "="*60)

class Newsletter:
    """Generates a newsletter from the research digest."""
    
    def __init__(self, digest: ResearchDigest):
        self.digest = digest
    
    def generate_newsletter(self) -> None:
        """Generate a newsletter from the research digest."""

def main():
    """Main entry point for the script."""
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY environment variable not set. Please set it in your .env file.")
        return

    digest = ResearchDigest(api_key)
    digest.generate_digest()

if __name__ == "__main__":
    main()
