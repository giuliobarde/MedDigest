from AI_Processing.research_digest import ResearchDigest


class Newsletter:
    """Generates a newsletter from the research digest."""
    
    def __init__(self, digest: ResearchDigest):
        self.digest = digest
    
    def generate_newsletter(self) -> None:
        """Generate a newsletter from the research digest."""