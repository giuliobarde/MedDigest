#!/usr/bin/env python3
"""
Simplified test script for the interest score functionality.

This script tests the interest score calculation logic directly without
requiring the full PaperAnalyzer import and external dependencies.
"""

import sys
import os
import hashlib
from datetime import datetime
from typing import List

# Add the parent directory to the path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Data_Classes.classes import Paper, PaperAnalysis


class InterestScoreCalculator:
    """
    Simplified version of the interest score calculation logic for testing.
    """
    
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
    
    @staticmethod
    def calculate_interest_score(paper: Paper, analysis: PaperAnalysis) -> float:
        """
        Calculate a deterministic interest score based on paper content and analysis.
        
        Args:
            paper (Paper): The original paper
            analysis (PaperAnalysis): The AI analysis results
            
        Returns:
            float: Interest score between 0.0 and 10.0
        """
        # Combine all text for analysis
        full_text = f"{paper.title} {paper.abstract} {paper.conclusion} {' '.join(analysis.keywords)}".lower()
        
        # Base score starts at 5.0
        score = 5.0
        
        # Factor 1: Study type and methodology (±2.0 points)
        if any(keyword in full_text for keyword in ['randomized controlled trial', 'rct', 'clinical trial']):
            score += 2.0
        elif any(keyword in full_text for keyword in ['meta-analysis', 'systematic review']):
            score += 1.8
        elif any(keyword in full_text for keyword in ['multi-center', 'multicenter', 'phase iii', 'phase 3']):
            score += 1.5
        elif any(keyword in full_text for keyword in ['prospective', 'cohort']):
            score += 1.0
        elif any(keyword in full_text for keyword in ['retrospective', 'case-control']):
            score += 0.5
        elif any(keyword in full_text for keyword in ['case report', 'case series', 'single case']):
            score -= 1.5
        elif any(keyword in full_text for keyword in ['in vitro', 'cell culture', 'animal model']):
            score -= 1.0
        
        # Factor 2: Clinical impact keywords (±1.5 points)
        high_impact_count = sum(1 for keyword in InterestScoreCalculator.HIGH_IMPACT_KEYWORDS if keyword in full_text)
        moderate_impact_count = sum(1 for keyword in InterestScoreCalculator.MODERATE_IMPACT_KEYWORDS if keyword in full_text)
        low_impact_count = sum(1 for keyword in InterestScoreCalculator.LOW_IMPACT_KEYWORDS if keyword in full_text)
        
        score += min(high_impact_count * 0.3, 1.5)
        score += min(moderate_impact_count * 0.1, 0.5)
        score -= min(low_impact_count * 0.2, 1.0)
        
        # Factor 3: Sample size indicators (±1.0 point)
        if any(keyword in full_text for keyword in ['large cohort', 'large sample', 'n >']) or \
           any(f'n = {i}' in full_text for i in range(1000, 10000)):
            score += 1.0
        elif any(keyword in full_text for keyword in ['small sample', 'limited sample', 'pilot']) or \
             any(f'n = {i}' in full_text for i in range(1, 50)):
            score -= 0.5
        
        # Factor 4: Regulatory/Clinical relevance (±1.0 point)
        if any(keyword in full_text for keyword in ['fda approved', 'fda approval', 'regulatory approval']):
            score += 1.0
        elif any(keyword in full_text for keyword in ['clinical guidelines', 'treatment guidelines']):
            score += 0.8
        elif any(keyword in full_text for keyword in ['mortality reduction', 'survival benefit']):
            score += 0.6
        
        # Factor 5: Innovation indicators (±0.5 points)
        if any(keyword in full_text for keyword in ['novel', 'innovative', 'first', 'breakthrough']):
            score += 0.5
        elif any(keyword in full_text for keyword in ['artificial intelligence', 'machine learning', 'deep learning']):
            score += 0.3
        
        # Factor 6: Add deterministic variance based on content hash
        # This ensures consistent scoring for identical content while adding slight variation
        content_hash = hashlib.md5(full_text.encode()).hexdigest()
        hash_factor = (int(content_hash[:8], 16) % 100) / 1000.0  # 0.000 to 0.099
        score += hash_factor
        
        # Ensure score is within bounds
        score = max(0.0, min(10.0, score))
        
        # Round to 1 decimal place for consistency
        return round(score, 1)


def create_sample_papers() -> List[Paper]:
    """
    Create sample papers with different characteristics to test interest scoring.
    
    Returns:
        List[Paper]: List of sample papers with varying content
    """
    papers = []
    
    # High-impact clinical trial paper
    papers.append(Paper(
        paper_id="sample_001",
        title="Randomized Controlled Trial of Novel Cardiovascular Treatment: A Breakthrough in Cardiology",
        published=datetime.now(),
        abstract="This landmark randomized controlled trial demonstrates a revolutionary approach to cardiovascular treatment. The study enrolled 2,500 patients across 15 centers and showed significant mortality reduction with the novel therapy. FDA approval is pending based on these groundbreaking results.",
        authors=["Dr. Smith", "Dr. Johnson", "Dr. Williams"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="The novel cardiovascular treatment represents a paradigm shift in patient care, with substantial clinical benefits and excellent safety profile."
    ))
    
    # Moderate-impact observational study
    papers.append(Paper(
        paper_id="sample_002",
        title="Observational Study of Treatment Outcomes in Oncology: A Retrospective Analysis",
        published=datetime.now(),
        abstract="This retrospective cohort study analyzed treatment outcomes in 500 cancer patients. The investigation focused on comparing different therapeutic approaches and their effectiveness. Preliminary findings suggest improvements in patient outcomes.",
        authors=["Dr. Brown", "Dr. Davis"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="The study provides valuable insights into treatment optimization and patient outcome assessment in oncology practice."
    ))
    
    # Low-impact case report
    papers.append(Paper(
        paper_id="sample_003",
        title="Single Case Report: Unusual Presentation in Dermatology",
        published=datetime.now(),
        abstract="We present a single case of an unusual dermatological condition. This case report describes the clinical presentation and management of a rare skin disorder. Limited sample size precludes general conclusions.",
        authors=["Dr. Wilson"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="This case report highlights the importance of careful clinical observation in rare conditions."
    ))
    
    # AI/ML research paper
    papers.append(Paper(
        paper_id="sample_004",
        title="Artificial Intelligence in Medical Imaging: Deep Learning for Diagnostic Accuracy",
        published=datetime.now(),
        abstract="This innovative study applies machine learning algorithms to improve diagnostic accuracy in radiology. The artificial intelligence system was trained on 10,000 medical images and demonstrates enhanced screening capabilities. The deep learning approach shows promising results.",
        authors=["Dr. Miller", "Dr. Garcia", "Dr. Rodriguez"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="Machine learning represents a transformative technology for medical imaging and diagnostic enhancement."
    ))
    
    # Meta-analysis paper
    papers.append(Paper(
        paper_id="sample_005",
        title="Systematic Review and Meta-Analysis of Treatment Efficacy in Neurology",
        published=datetime.now(),
        abstract="This comprehensive systematic review and meta-analysis examined treatment efficacy across 25 clinical trials involving 15,000 patients. The analysis reveals substantial evidence supporting current clinical guidelines. Multi-center data confirms the effectiveness of established protocols.",
        authors=["Dr. Martinez", "Dr. Anderson", "Dr. Taylor", "Dr. Thomas"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="The meta-analysis provides robust evidence for treatment guidelines and clinical decision-making in neurology."
    ))
    
    # In vitro research paper
    papers.append(Paper(
        paper_id="sample_006",
        title="In Vitro Study of Cellular Mechanisms: Cell Culture Analysis",
        published=datetime.now(),
        abstract="This in vitro study investigates cellular mechanisms using cell culture techniques. The research explores molecular pathways in controlled laboratory conditions. Animal model validation is planned for future studies.",
        authors=["Dr. Jackson", "Dr. White"],
        categories=["cs.AI", "q-bio.QM"],
        conclusion="The cell culture findings provide theoretical insights into molecular mechanisms requiring further validation."
    ))
    
    return papers


def test_interest_scores():
    """
    Test the interest score calculation for sample papers.
    """
    print("=" * 80)
    print("INTEREST SCORE TESTING")
    print("=" * 80)
    print()
    
    # Create sample papers
    papers = create_sample_papers()
    
    print("Testing Interest Score Calculation for Sample Papers:")
    print("-" * 60)
    
    for i, paper in enumerate(papers, 1):
        print(f"\nPaper {i}: {paper.title}")
        print(f"ID: {paper.paper_id}")
        print(f"Abstract: {paper.abstract[:100]}...")
        
        # Create a mock analysis with dummy data
        mock_analysis = PaperAnalysis(
            specialty="General Medicine",
            keywords=["test", "sample", "research", "medical", "study"],
            focus="Sample research paper for testing",
            interest_score=0.0
        )
        
        # Calculate interest score
        try:
            interest_score = InterestScoreCalculator.calculate_interest_score(paper, mock_analysis)
            print(f"Interest Score: {interest_score:.1f}/10.0")
            
            # Provide interpretation
            if interest_score >= 8.0:
                print("Category: HIGH IMPACT")
            elif interest_score >= 6.0:
                print("Category: MODERATE IMPACT")
            elif interest_score >= 4.0:
                print("Category: STANDARD RESEARCH")
            else:
                print("Category: LOW IMPACT")
                
        except Exception as e:
            print(f"Error calculating interest score: {e}")
        
        print("-" * 60)
    
    print("\n" + "=" * 80)
    print("INTEREST SCORE TESTING COMPLETE")
    print("=" * 80)


def test_scoring_factors():
    """
    Test individual scoring factors to understand how they contribute to the final score.
    """
    print("\n" + "=" * 80)
    print("SCORING FACTORS ANALYSIS")
    print("=" * 80)
    print()
    
    # Test papers with specific characteristics
    test_cases = [
        {
            "name": "Clinical Trial with High Impact Keywords",
            "title": "Randomized Controlled Trial of Breakthrough Treatment",
            "abstract": "This revolutionary clinical trial shows substantial improvement with FDA approval pending. The breakthrough treatment demonstrates significant mortality reduction.",
            "conclusion": "Landmark study with transformative clinical outcomes."
        },
        {
            "name": "Case Report with Low Impact Keywords",
            "title": "Single Case Report of Rare Condition",
            "abstract": "We present a case report of a single patient with limited sample size. This preliminary finding requires further investigation.",
            "conclusion": "Case report highlights unusual presentation."
        },
        {
            "name": "AI/ML Research Paper",
            "title": "Artificial Intelligence in Medical Diagnosis",
            "abstract": "This innovative study uses machine learning and deep learning for diagnostic enhancement. The artificial intelligence system shows promising results.",
            "conclusion": "AI represents transformative technology in medicine."
        }
    ]
    
    for test_case in test_cases:
        print(f"\nTest Case: {test_case['name']}")
        print(f"Title: {test_case['title']}")
        print(f"Abstract: {test_case['abstract']}")
        
        # Create a mock paper
        paper = Paper(
            paper_id="test_factor",
            title=test_case['title'],
            published=datetime.now(),
            abstract=test_case['abstract'],
            authors=["Test Author"],
            categories=["cs.AI"],
            conclusion=test_case['conclusion']
        )
        
        # Create mock analysis
        mock_analysis = PaperAnalysis(
            specialty="General Medicine",
            keywords=["test"],
            focus="Test case",
            interest_score=0.0
        )
        
        # Calculate score
        score = InterestScoreCalculator.calculate_interest_score(paper, mock_analysis)
        print(f"Calculated Interest Score: {score:.1f}/10.0")
        print("-" * 40)


if __name__ == "__main__":
    print("Starting Interest Score Testing...")
    print()
    
    # Test basic interest score calculation
    test_interest_scores()
    
    # Test scoring factors
    test_scoring_factors()
    
    print("\nAll tests completed!") 