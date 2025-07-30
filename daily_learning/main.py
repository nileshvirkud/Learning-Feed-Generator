"""Main application entry point for Daily Learning Feed Generator"""

import argparse
import logging
import sys
import time
from datetime import datetime
from typing import List, Optional

from .config import Config
from .content_fetcher import ContentFetcher
from .summarizer import Summarizer
from .quiz_generator import QuizGenerator
from .notion_client import NotionLearningDatabase

def setup_logging(config: Config):
    """Configure logging for the application"""
    logging.basicConfig(
        level=getattr(logging, config.log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(config.log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Reduce noise from external libraries
    logging.getLogger("openai").setLevel(logging.WARNING)
    logging.getLogger("notion_client").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

class DailyLearningGenerator:
    """Main application class that orchestrates the learning feed generation"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Initialize components
        self.content_fetcher = ContentFetcher(
            perplexity_api_key=config.perplexity_api_key,
            rate_limit=config.api_rate_limit_per_minute
        )
        
        self.summarizer = Summarizer(
            api_key=config.openai_api_key
        )
        
        self.quiz_generator = QuizGenerator(
            api_key=config.openai_api_key
        )
        
        self.notion_db = NotionLearningDatabase(
            token=config.notion_token,
            database_id=config.notion_database_id
        )
    
    def validate_setup(self) -> bool:
        """Validate that all components are properly configured"""
        self.logger.info("Validating application setup...")
        
        # Validate configuration
        config_errors = self.config.validate()
        if config_errors:
            self.logger.error("Configuration errors:")
            for error in config_errors:
                self.logger.error(f"  - {error}")
            return False
        
        # Test Notion connection
        if not self.notion_db.verify_database_connection():
            self.logger.error("Failed to connect to Notion database")
            return False
        
        self.logger.info("Setup validation successful")
        return True
    
    def run_daily_generation(self, topics: Optional[List[str]] = None) -> bool:
        """Run the complete daily learning feed generation process"""
        start_time = time.time()
        self.logger.info("Starting daily learning feed generation")
        
        try:
            # Use provided topics or default from config
            topics_to_process = topics or self.config.default_topics
            self.logger.info(f"Processing topics: {', '.join(topics_to_process)}")
            
            # Step 1: Fetch content
            self.logger.info("Step 1: Fetching content...")
            articles = self.content_fetcher.fetch_content(
                topics=topics_to_process,
                max_articles_per_topic=self.config.max_articles_per_topic
            )
            
            if not articles:
                self.logger.error("No articles were fetched. Stopping process.")
                return False
            
            # Filter recent content
            recent_articles = self.content_fetcher.filter_recent_content(
                articles, self.config.content_max_age_hours
            )
            
            if not recent_articles:
                self.logger.warning("No recent articles found after filtering")
                return True  # Not an error, just no new content
            
            # Step 2: Generate summaries
            self.logger.info("Step 2: Generating summaries...")
            summaries = self.summarizer.summarize_batch(
                articles=recent_articles,
                sentence_count=self.config.summary_sentence_count
            )
            
            if not summaries:
                self.logger.error("No summaries were generated. Stopping process.")
                return False
            
            # Step 3: Generate learning materials
            self.logger.info("Step 3: Generating quiz questions and flashcards...")
            learning_materials = self.quiz_generator.generate_batch_materials(
                summaries=summaries,
                num_questions=self.config.quiz_questions_per_article,
                num_flashcards=self.config.flashcards_per_article
            )
            
            # Step 4: Save to Notion
            self.logger.info("Step 4: Saving to Notion database...")
            created_entries = self.notion_db.batch_create_entries(learning_materials)
            
            # Log summary
            elapsed_time = time.time() - start_time
            self.logger.info(f"""
Daily Learning Feed Generation Complete!
=====================================
Processing Time: {elapsed_time:.2f} seconds
Topics Processed: {len(topics_to_process)}
Articles Fetched: {len(articles)}
Recent Articles: {len(recent_articles)}
Summaries Generated: {len(summaries)}
Learning Materials Created: {len(learning_materials)}  
Notion Entries Created: {len(created_entries)}
            """)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error during daily generation: {str(e)}", exc_info=True)
            return False
    
    def show_database_stats(self):
        """Display current database statistics"""
        self.logger.info("Fetching database statistics...")
        stats = self.notion_db.get_database_stats()
        
        if stats:
            print("\nNotion Database Statistics:")
            print("=" * 30)
            print(f"Total Entries: {stats.get('total_entries', 0)}")
            print(f"Recent Entries (7 days): {stats.get('recent_entries', 0)}")
            
            print("\nBy Topic:")
            for topic, count in stats.get('topics', {}).items():
                print(f"  {topic}: {count}")
            
            print("\nBy Status:")
            for status, count in stats.get('statuses', {}).items():
                print(f"  {status}: {count}")
        else:
            print("Unable to fetch database statistics")
    
    def interactive_topic_selection(self) -> List[str]:
        """Allow user to interactively select topics"""
        print("\nInteractive Topic Selection")
        print("=" * 30)
        print("Default topics:")
        for i, topic in enumerate(self.config.default_topics, 1):
            print(f"  {i}. {topic}")
        
        print("\nOptions:")
        print("  - Press Enter to use all default topics")
        print("  - Enter topic numbers (comma-separated) to select specific topics")
        print("  - Enter custom topics (comma-separated)")
        
        user_input = input("\nYour choice: ").strip()
        
        if not user_input:
            return self.config.default_topics
        
        # Check if input contains only numbers and commas
        if all(c.isdigit() or c in [',', ' '] for c in user_input):
            try:
                indices = [int(x.strip()) - 1 for x in user_input.split(',')]
                selected_topics = []
                for idx in indices:
                    if 0 <= idx < len(self.config.default_topics):
                        selected_topics.append(self.config.default_topics[idx])
                return selected_topics if selected_topics else self.config.default_topics
            except ValueError:
                pass
        
        # Treat as custom topics
        custom_topics = [topic.strip() for topic in user_input.split(',')]
        return [topic for topic in custom_topics if topic]

def create_argument_parser() -> argparse.ArgumentParser:
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description="Daily Learning Feed Generator - Curate and organize educational content",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Run with default topics
  %(prog)s --topics "python,machine learning" # Run with custom topics  
  %(prog)s --interactive                      # Interactive topic selection
  %(prog)s --stats                           # Show database statistics
  %(prog)s --setup-db                        # Setup database schema
        """
    )
    
    parser.add_argument(
        '--topics', '-t',
        type=str,
        help='Comma-separated list of topics to process'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Use interactive topic selection'
    )
    
    parser.add_argument(
        '--stats', '-s',
        action='store_true',
        help='Show database statistics and exit'
    )
    
    parser.add_argument(
        '--setup-db',
        action='store_true',
        help='Setup or update database schema and exit'
    )
    
    parser.add_argument(
        '--config-file',
        type=str,
        help='Path to configuration file (default: use environment variables)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Run without saving to Notion (for testing)'
    )
    
    return parser

def main():
    """Main entry point"""
    parser = create_argument_parser()
    args = parser.parse_args()
    
    # Load configuration
    config = Config.from_env()
    setup_logging(config)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting Daily Learning Feed Generator")
    
    # Create main application
    app = DailyLearningGenerator(config)
    
    # Validate setup
    if not app.validate_setup():
        logger.error("Setup validation failed. Please check your configuration.")
        sys.exit(1)
    
    try:
        # Handle special commands
        if args.setup_db:
            logger.info("Setting up database schema...")
            if app.notion_db.create_database_schema():
                print("Database schema setup successful!")
            else:
                print("Database schema setup failed!")
            return
        
        if args.stats:
            app.show_database_stats()
            return
        
        # Determine topics to process
        topics = None
        if args.topics:
            topics = [topic.strip() for topic in args.topics.split(',')]
        elif args.interactive:
            topics = app.interactive_topic_selection()
        
        # Run the main process
        if args.dry_run:
            logger.info("DRY RUN MODE - No data will be saved to Notion")
            # You could modify the app to skip Notion saving in dry run mode
        
        success = app.run_daily_generation(topics)
        
        if success:
            logger.info("Daily learning feed generation completed successfully!")
            sys.exit(0)
        else:
            logger.error("Daily learning feed generation failed!")
            sys.exit(1)
            
    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()