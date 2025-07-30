"""Configuration management for Daily Learning Feed Generator"""

import os
from dataclasses import dataclass
from typing import List, Optional
from dotenv import load_dotenv

load_dotenv()

@dataclass
class Config:
    """Application configuration"""
    
    # API Keys
    openai_api_key: str
    notion_token: str
    notion_database_id: str
    perplexity_api_key: Optional[str] = None
    
    # Content Settings
    max_articles_per_topic: int = 5
    content_max_age_hours: int = 48
    summary_sentence_count: int = 4
    quiz_questions_per_article: int = 2
    flashcards_per_article: int = 3
    
    # Default Topics
    default_topics: List[str] = None
    
    # Rate Limiting
    api_rate_limit_per_minute: int = 60
    batch_size: int = 5
    
    # Logging
    log_level: str = "INFO"
    log_file: str = "daily_learning.log"
    
    def __post_init__(self):
        if self.default_topics is None:
            self.default_topics = [
                "artificial intelligence",
                "machine learning",
                "software development",
                "data science"
            ]
    
    @classmethod
    def from_env(cls) -> "Config":
        """Create config from environment variables"""
        return cls(
            openai_api_key=os.getenv("OPENAI_API_KEY", ""),
            notion_token=os.getenv("NOTION_TOKEN", ""),
            notion_database_id=os.getenv("NOTION_DATABASE_ID", ""),
            perplexity_api_key=os.getenv("PERPLEXITY_API_KEY"),
            max_articles_per_topic=int(os.getenv("MAX_ARTICLES_PER_TOPIC", "5")),
            content_max_age_hours=int(os.getenv("CONTENT_MAX_AGE_HOURS", "48")),
            summary_sentence_count=int(os.getenv("SUMMARY_SENTENCE_COUNT", "4")),
            quiz_questions_per_article=int(os.getenv("QUIZ_QUESTIONS_PER_ARTICLE", "2")),
            flashcards_per_article=int(os.getenv("FLASHCARDS_PER_ARTICLE", "3")),
            api_rate_limit_per_minute=int(os.getenv("API_RATE_LIMIT_PER_MINUTE", "60")),
            batch_size=int(os.getenv("BATCH_SIZE", "5")),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_file=os.getenv("LOG_FILE", "daily_learning.log")
        )
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        if not self.openai_api_key:
            errors.append("OPENAI_API_KEY is required")
        
        if not self.notion_token:
            errors.append("NOTION_TOKEN is required")
            
        if not self.notion_database_id:
            errors.append("NOTION_DATABASE_ID is required")
            
        if self.max_articles_per_topic <= 0:
            errors.append("max_articles_per_topic must be positive")
            
        if self.content_max_age_hours <= 0:
            errors.append("content_max_age_hours must be positive")
            
        return errors