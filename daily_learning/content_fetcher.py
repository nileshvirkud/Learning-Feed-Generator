"""Content fetching module using Perplexity API and fallback sources"""

import logging
import requests
import time
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class Article:
    """Represents a fetched article"""
    title: str
    url: str
    content: str
    source: str
    published_date: Optional[datetime]
    topic: str
    
class ContentFetcher:
    """Fetches content from various sources with rate limiting"""
    
    def __init__(self, perplexity_api_key: Optional[str] = None, rate_limit: int = 60):
        self.perplexity_api_key = perplexity_api_key
        self.rate_limit = rate_limit
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        min_interval = 60 / self.rate_limit
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def fetch_with_perplexity(self, topic: str, max_articles: int = 5) -> List[Article]:
        """Fetch articles using Perplexity API"""
        if not self.perplexity_api_key:
            logger.warning("Perplexity API key not provided, skipping Perplexity search")
            return []
        
        self._rate_limit()
        
        try:
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            # Construct search query for recent educational content
            query = f"recent articles about {topic} educational content learning resources 2024"
            
            payload = {
                "model": "llama-3.1-sonar-large-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a content curator. Find recent, high-quality educational articles and return them in a structured format."
                    },
                    {
                        "role": "user", 
                        "content": f"Find {max_articles} recent educational articles about {topic}. For each article, provide: title, URL, brief summary, source, and publication date if available. Focus on content from the last 48 hours."
                    }
                ]
            }
            
            response = requests.post(
                "https://api.perplexity.ai/chat/completions",
                headers=headers,
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                
                # Parse the response to extract articles
                articles = self._parse_perplexity_response(content, topic)
                logger.info(f"Fetched {len(articles)} articles from Perplexity for topic: {topic}")
                return articles
            else:
                logger.error(f"Perplexity API error: {response.status_code} - {response.text}")
                return []
                
        except Exception as e:
            logger.error(f"Error fetching from Perplexity: {str(e)}")
            return []
    
    def _parse_perplexity_response(self, content: str, topic: str) -> List[Article]:
        """Parse Perplexity API response to extract articles"""
        articles = []
        
        # This is a simplified parser - in practice, you'd want more robust parsing
        # based on the actual format returned by Perplexity
        lines = content.split('\n')
        current_article = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Title:') or line.startswith('**Title'):
                current_article['title'] = line.split(':', 1)[-1].strip().strip('*')
            elif line.startswith('URL:') or line.startswith('**URL'):
                current_article['url'] = line.split(':', 1)[-1].strip().strip('*')
            elif line.startswith('Summary:') or line.startswith('**Summary'):
                current_article['content'] = line.split(':', 1)[-1].strip().strip('*')
            elif line.startswith('Source:') or line.startswith('**Source'):
                current_article['source'] = line.split(':', 1)[-1].strip().strip('*')
                
                # When we have all fields, create article
                if all(key in current_article for key in ['title', 'url', 'content', 'source']):
                    articles.append(Article(
                        title=current_article['title'],
                        url=current_article['url'],
                        content=current_article['content'],
                        source=current_article['source'],
                        published_date=datetime.now(),  # Default to now if not specified
                        topic=topic
                    ))
                    current_article = {}
        
        return articles
    
    def fetch_with_rss(self, topic: str, max_articles: int = 5) -> List[Article]:
        """Fallback method using RSS feeds"""
        logger.info(f"Using RSS fallback for topic: {topic}")
        
        # Common RSS feeds for tech/learning content
        rss_feeds = {
            "artificial intelligence": [
                "https://feeds.feedburner.com/oreilly/radar",
                "https://machinelearningmastery.com/feed/"
            ],
            "machine learning": [
                "https://machinelearningmastery.com/feed/",
                "https://distill.pub/rss.xml"
            ],
            "software development": [
                "https://feeds.feedburner.com/oreilly/radar",
                "https://dev.to/feed"
            ],
            "data science": [
                "https://towardsdatascience.com/feed",
                "https://www.kaggle.com/learn-posts.atom"
            ]
        }
        
        # This is a placeholder - you'd implement actual RSS parsing here
        # For now, return mock data
        mock_articles = [
            Article(
                title=f"Sample Article About {topic.title()}",
                url=f"https://example.com/{topic.replace(' ', '-')}-article",
                content=f"This is a sample article about {topic} that would normally be fetched from RSS feeds.",
                source="Example Source",
                published_date=datetime.now() - timedelta(hours=2),
                topic=topic
            )
        ]
        
        return mock_articles[:max_articles]
    
    def fetch_content(self, topics: List[str], max_articles_per_topic: int = 5) -> List[Article]:
        """Main method to fetch content for given topics"""
        all_articles = []
        
        for topic in topics:
            logger.info(f"Fetching content for topic: {topic}")
            
            # Try Perplexity first
            articles = self.fetch_with_perplexity(topic, max_articles_per_topic)
            
            # If Perplexity fails or returns no results, use RSS fallback
            if not articles:
                logger.info(f"Perplexity returned no results for {topic}, trying RSS fallback")
                articles = self.fetch_with_rss(topic, max_articles_per_topic)
            
            all_articles.extend(articles)
            
            # Add delay between topics to be respectful to APIs
            time.sleep(1)
        
        logger.info(f"Total articles fetched: {len(all_articles)}")
        return all_articles
    
    def filter_recent_content(self, articles: List[Article], max_age_hours: int = 48) -> List[Article]:
        """Filter articles to only include recent content"""
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        recent_articles = []
        
        for article in articles:
            if article.published_date and article.published_date >= cutoff_time:
                recent_articles.append(article)
            elif not article.published_date:
                # If no date available, assume it's recent
                recent_articles.append(article)
        
        logger.info(f"Filtered to {len(recent_articles)} recent articles (within {max_age_hours} hours)")
        return recent_articles