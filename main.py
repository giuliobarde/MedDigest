# Standard library imports for core functionality
import datetime
import logging


# Third-party imports for AI and environment management
from dotenv import load_dotenv
import os

# Local application imports
from AI_Processing.research_digest import ResearchDigest

# Load environment variables from .env file
load_dotenv()

# Configure logging with timestamp, level, and message format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


def main():
    """
    Main entry point for the script.
    
    Initializes the ResearchDigest with API credentials and generates
    a research digest of academic papers.
    
    Returns:
        None
    """
    # Retrieve and validate API key from environment variables
    api_key = os.getenv('GROQ_API_KEY')
    if not api_key:
        logger.error("GROQ_API_KEY environment variable not set. Please set it in your .env file.")
        return

    # Initialize and run the research digest generation
    digest = ResearchDigest(api_key)
    digest_json = digest.generate_digest()
    digest.digest_json = digest_json  # Store the digest JSON for Newsletter

    # Print token usage summary
    digest.token_monitor.print_usage_summary()

    # Generate the newsletter
    from Output_Generation.newsletter import Newsletter
    newsletter = Newsletter(digest)
    current_newsletter = newsletter.generate_newsletter()

    # Try to send the newsletter, but don't fail if email sending doesn't work
    try:
        from Email_System.send_email import send_newsletter_email
        result = send_newsletter_email("giuliobarde@gmail.com", "MedDigest Newsletter", current_newsletter)
        if result:
            logger.info("✅ Newsletter email sent successfully!")
        else:
            logger.warning("⚠️ Email sending failed, but newsletter was generated and saved locally.")
    except Exception as e:
        logger.warning(f"⚠️ Email sending failed with error: {e}")
        logger.info("📧 Newsletter was generated and saved locally. You can find it in the Newsletters directory.")

# Entry point guard to ensure script runs only when executed directly
if __name__ == "__main__":
    main()
