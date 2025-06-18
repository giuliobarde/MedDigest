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
        Outputs JSON that can be used by the Newsletter class.
        """
        papers_with_summaries = []

        for specialty, data in self.specialty_data.items():
            for paper in data["papers"]:
                paper_info = {
                    "title": paper["title"],
                    "specialty": specialty,
                    "focus": paper["focus"],
                    "date": paper["date"],
                    "authors": paper["authors"],
                    "summary": "",
                    "main_discovery": "",
                    "implications": "",
                    "challenges": "",
                    "looking_forward": ""
                }

                # Generate analysis for each paper
                try:
                    prompt = f"""
                    Analyze this medical research paper and provide the following information:
                    
                    Title: {paper['title']}
                    Specialty: {specialty}
                    Focus: {paper['focus']}
                    Keywords: {', '.join(paper['keywords'])}
                    
                    Please provide:
                    1. Summary: A comprehensive 5-6 sentence overview of the research
                    2. Main Discovery: The key breakthrough or finding in one sentence
                    3. Implications: The potential impact on medical practice in 1-2 sentences
                    4. Challenges: Main obstacles or limitations identified in one sentence
                    5. Looking Forward: Future directions or next steps in one sentence
                    
                    Format your response exactly as:
                    Summary: [your 5-6 sentence summary]
                    Main Discovery: [key finding]
                    Implications: [medical impact]
                    Challenges: [obstacles]
                    Looking Forward: [future directions]
                    """

                    response = self.llm.invoke(input=prompt)
                    content = response.content.strip()

                    # Parse the response
                    lines = content.split('\n')
                    for line in lines:
                        if line.startswith('Summary:'):
                            paper_info["summary"] = line.replace('Summary:', '').strip()
                        elif line.startswith('Main Discovery:'):
                            paper_info["main_discovery"] = line.replace('Main Discovery:', '').strip()
                        elif line.startswith('Implications:'):
                            paper_info["implications"] = line.replace('Implications:', '').strip()
                        elif line.startswith('Challenges:'):
                            paper_info["challenges"] = line.replace('Challenges:', '').strip()
                        elif line.startswith('Looking Forward:'):
                            paper_info["looking_forward"] = line.replace('Looking Forward:', '').strip()

                    time.sleep(1)

                except Exception as e:
                    logger.warning(f"Failed to generate analysis for paper: {str(e)}")
                    # Fallback content
                    paper_info["summary"] = (f"This research focuses on {paper['focus']}. "
                                        f"The study investigates key aspects of {specialty} "
                                        f"with emphasis on {paper['keywords'][0] if paper['keywords'] else 'innovative approaches'}. "
                                        f"The research aims to advance our understanding in this field. "
                                        f"It contributes to the growing body of knowledge in {specialty}. "
                                        f"The findings have potential applications in clinical practice.")
                    paper_info["main_discovery"] = f"Advances in {paper['keywords'][0] if paper['keywords'] else 'medical research'}."
                    paper_info["implications"] = f"Potential to improve {specialty} practices."
                    paper_info["challenges"] = "Further validation and implementation required."
                    paper_info["looking_forward"] = "Future studies needed to expand on these findings."

                papers_with_summaries.append(paper_info)

        if not papers_with_summaries:
            logger.info("\nNo papers were analyzed. Please ensure papers were successfully fetched and analyzed.")
            return

        # Create simplified output structure for newsletter
        output_json = {
            "date_generated": datetime.datetime.now().strftime("%B %d, %Y"),
            "papers": papers_with_summaries,
            "total_papers": len(papers_with_summaries)
        }

        logger.info("\n" + "="*60)
        logger.info("JSON DIGEST SUMMARY:")
        logger.info("="*60)

        print(json.dumps(output_json, indent=2, ensure_ascii=False))

        self.digest_json = output_json