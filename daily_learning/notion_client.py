"""Notion database integration for storing learning materials"""

import logging
import time
from datetime import datetime
from typing import List, Dict, Any, Optional
from notion_client import Client
from notion_client.errors import APIResponseError
from .quiz_generator import LearningMaterials, QuizQuestion, Flashcard

logger = logging.getLogger(__name__)

class NotionLearningDatabase:
    """Manages Notion database operations for learning materials"""
    
    def __init__(self, token: str, database_id: str):
        self.client = Client(auth=token)
        self.database_id = database_id
        self.last_request_time = 0
    
    def _rate_limit(self, min_interval: float = 0.3):
        """Rate limiting for Notion API (3 requests per second limit)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def verify_database_connection(self) -> bool:
        """Verify that the database exists and is accessible"""
        try:
            self._rate_limit()
            response = self.client.databases.retrieve(database_id=self.database_id)
            logger.info(f"Successfully connected to Notion database: {response.get('title', [{}])[0].get('text', {}).get('content', 'Unknown')}")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to Notion database: {str(e)}")
            return False
    
    def create_database_schema(self) -> bool:
        """Create or update the database schema with required properties"""
        try:
            schema_properties = {
                "Title": {"title": {}},
                "Topic": {
                    "multi_select": {
                        "options": [
                            {"name": "Artificial Intelligence", "color": "blue"},
                            {"name": "Machine Learning", "color": "green"},
                            {"name": "Software Development", "color": "purple"},
                            {"name": "Data Science", "color": "orange"},
                            {"name": "General", "color": "gray"}
                        ]
                    }
                },
                "Summary": {"rich_text": {}},
                "Source URL": {"url": {}},
                "Date Added": {
                    "date": {}
                },
                "Quiz Questions": {"rich_text": {}},
                "Flashcards": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "New", "color": "blue"},
                            {"name": "Reviewed", "color": "green"},
                            {"name": "Archived", "color": "gray"}
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"}
                        ]
                    }
                },
                "Tags": {"multi_select": {}},
                "Key Points": {"rich_text": {}},
                "Learning Objectives": {"rich_text": {}}
            }
            
            self._rate_limit()
            self.client.databases.update(
                database_id=self.database_id,
                properties=schema_properties
            )
            
            logger.info("Successfully updated database schema")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update database schema: {str(e)}")
            return False
    
    def format_quiz_questions(self, questions: List[QuizQuestion]) -> str:
        """Format quiz questions for Notion rich text"""
        formatted = []
        
        for i, q in enumerate(questions, 1):
            formatted.append(f"**Question {i}:** {q.question}")
            
            if q.question_type == "multiple_choice" and q.options:
                for option in q.options:
                    formatted.append(f"  {option}")
            
            formatted.append(f"**Answer:** {q.correct_answer}")
            formatted.append(f"**Explanation:** {q.explanation}")
            formatted.append(f"**Difficulty:** {q.difficulty}")
            formatted.append("")  # Empty line for spacing
        
        return "\n".join(formatted)
    
    def format_flashcards(self, flashcards: List[Flashcard]) -> str:
        """Format flashcards for Notion rich text"""
        formatted = []
        
        for i, card in enumerate(flashcards, 1):
            formatted.append(f"**Card {i}:**")
            formatted.append(f"Q: {card.question}")
            formatted.append(f"A: {card.answer}")
            if card.hint:
                formatted.append(f"Hint: {card.hint}")
            formatted.append(f"Difficulty: {card.difficulty}")
            formatted.append("")  # Empty line for spacing
        
        return "\n".join(formatted)
    
    def create_learning_entry(self, materials: LearningMaterials) -> Optional[Dict[str, Any]]:
        """Create a new entry in the Notion database"""
        self._rate_limit()
        
        try:
            article = materials.summary.original_article
            summary = materials.summary
            
            # Determine topic for multi-select
            topic_mapping = {
                "artificial intelligence": "Artificial Intelligence",
                "machine learning": "Machine Learning", 
                "software development": "Software Development",
                "data science": "Data Science"
            }
            topic_name = topic_mapping.get(article.topic.lower(), "General")
            
            properties = {
                "Title": {
                    "title": [
                        {
                            "text": {
                                "content": article.title[:100]  # Notion title limit
                            }
                        }
                    ]
                },
                "Topic": {
                    "multi_select": [
                        {"name": topic_name}
                    ]
                },
                "Summary": {
                    "rich_text": [
                        {
                            "text": {
                                "content": summary.summary
                            }
                        }
                    ]
                },
                "Source URL": {
                    "url": article.url
                },
                "Date Added": {
                    "date": {
                        "start": datetime.now().isoformat()
                    }
                },
                "Quiz Questions": {
                    "rich_text": [
                        {
                            "text": {
                                "content": self.format_quiz_questions(materials.quiz_questions)
                            }
                        }
                    ]
                },
                "Flashcards": {
                    "rich_text": [
                        {
                            "text": {
                                "content": self.format_flashcards(materials.flashcards)
                            }
                        }
                    ]
                },
                "Status": {
                    "select": {
                        "name": "New"
                    }
                },
                "Priority": {
                    "select": {
                        "name": "Medium"
                    }
                },
                "Key Points": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "\n".join([f"• {point}" for point in summary.key_points])
                            }
                        }
                    ]
                },
                "Learning Objectives": {
                    "rich_text": [
                        {
                            "text": {
                                "content": "\n".join([f"• {obj}" for obj in summary.learning_objectives])
                            }
                        }
                    ]
                }
            }
            
            response = self.client.pages.create(
                parent={"database_id": self.database_id},
                properties=properties
            )
            
            logger.info(f"Created Notion entry for: {article.title[:50]}...")
            return response
            
        except APIResponseError as e:
            logger.error(f"Notion API error creating entry: {e.body}")
            return None
        except Exception as e:
            logger.error(f"Error creating Notion entry: {str(e)}")
            return None
    
    def batch_create_entries(self, materials_list: List[LearningMaterials]) -> List[Dict[str, Any]]:
        """Create multiple entries with rate limiting"""
        created_entries = []
        
        for i, materials in enumerate(materials_list):
            logger.info(f"Creating Notion entry {i+1}/{len(materials_list)}")
            
            entry = self.create_learning_entry(materials)
            if entry:
                created_entries.append(entry)
            else:
                logger.warning(f"Failed to create entry for: {materials.summary.original_article.title}")
            
            # Rate limiting between requests
            if i < len(materials_list) - 1:
                time.sleep(0.5)
        
        logger.info(f"Successfully created {len(created_entries)}/{len(materials_list)} Notion entries")
        return created_entries
    
    def query_recent_entries(self, days: int = 7) -> List[Dict[str, Any]]:
        """Query recent entries from the database"""
        try:
            self._rate_limit()
            
            # Calculate date filter
            from datetime import timedelta
            cutoff_date = (datetime.now() - timedelta(days=days)).isoformat()
            
            response = self.client.databases.query(
                database_id=self.database_id,
                filter={
                    "property": "Date Added",
                    "date": {
                        "after": cutoff_date
                    }
                },
                sorts=[
                    {
                        "property": "Date Added",
                        "direction": "descending"
                    }
                ]
            )
            
            results = response.get("results", [])
            logger.info(f"Found {len(results)} entries from the last {days} days")
            return results
            
        except Exception as e:
            logger.error(f"Error querying recent entries: {str(e)}")
            return []
    
    def update_entry_status(self, page_id: str, status: str) -> bool:
        """Update the status of an existing entry"""
        try:
            self._rate_limit()
            
            self.client.pages.update(
                page_id=page_id,
                properties={
                    "Status": {
                        "select": {
                            "name": status
                        }
                    }
                }
            )
            
            logger.info(f"Updated entry status to: {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry status: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get statistics about the database contents"""
        try:
            self._rate_limit()
            
            response = self.client.databases.query(database_id=self.database_id)
            results = response.get("results", [])
            
            stats = {
                "total_entries": len(results),
                "topics": {},
                "statuses": {},
                "recent_entries": 0
            }
            
            # Count by topics and statuses
            cutoff_date = datetime.now() - timedelta(days=7)
            
            for result in results:
                properties = result.get("properties", {})
                
                # Count topics
                topic_prop = properties.get("Topic", {}).get("multi_select", [])
                for topic in topic_prop:
                    topic_name = topic.get("name", "Unknown")
                    stats["topics"][topic_name] = stats["topics"].get(topic_name, 0) + 1
                
                # Count statuses
                status_prop = properties.get("Status", {}).get("select", {})
                status_name = status_prop.get("name", "Unknown") if status_prop else "Unknown"
                stats["statuses"][status_name] = stats["statuses"].get(status_name, 0) + 1
                
                # Count recent entries
                date_prop = properties.get("Date Added", {}).get("date", {})
                if date_prop and date_prop.get("start"):
                    entry_date = datetime.fromisoformat(date_prop["start"].replace("Z", "+00:00"))
                    if entry_date.replace(tzinfo=None) >= cutoff_date:
                        stats["recent_entries"] += 1
            
            logger.info(f"Database stats: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}