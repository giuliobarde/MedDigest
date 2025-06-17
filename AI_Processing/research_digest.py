from Data_Classes.classes import Paper, PaperAnalysis
from Data_Retrieval.data_retrieval import ArxivClient
from AI_Processing.paper_analyzer import PaperAnalyzer
from typing import List, Dict
import logging

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
    
    def generate_digest(self, search_query: str = "all:medical", max_results: int = 100) -> None:
        """
        Generate a research digest for medical papers.
        
        Args:
            search_query (str): The search query to use for finding papers
            max_results (int): Maximum number of papers to analyze
            
        Note:
            The digest includes paper analysis, specialty categorization,
            and AI-generated summaries of key findings.
        """
        logger.info("Fetching papers from arXiv...")
        papers = self.arxiv_client.fetch_papers(search_query, max_results)
        logger.info(f"Found {len(papers)} papers")
        
        self._analyze_papers(papers)
        self._display_summary()
        self._digest_summary()
    
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

    def _digest_summary(self) -> None:
        """
        Generate a concise AI-powered summary of key findings across all papers.
        
        Note:
            This method:
            1. Prepares structured data for AI analysis
            2. Generates a comprehensive summary using AI
            3. Provides fallback statistics if AI summary fails
            4. Includes cross-specialty insights and trends
        """
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
            response = self.llm.invoke(input=prompt)
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