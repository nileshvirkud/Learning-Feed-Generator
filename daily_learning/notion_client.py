"""Notion database integration for storing learning materials"""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from notion_client import Client
from notion_client.errors import APIResponseError

from .quiz_generator import Flashcard, LearningMaterials, QuizQuestion

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
            logger.info(
                f"Successfully connected to Notion database: {response.get('title', [{}])[0].get('text', {}).get('content', 'Unknown')}"
            )

            # Log current schema for debugging
            properties = response.get("properties", {})
            logger.info(f"Current database properties: {list(properties.keys())}")
            for prop_name, prop_data in properties.items():
                prop_type = list(prop_data.keys())[0] if prop_data else "unknown"
                logger.debug(f"Property '{prop_name}': type={prop_type}")

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
                            {"name": "General", "color": "gray"},
                        ]
                    }
                },
                "Summary": {"rich_text": {}},
                "Source URL": {"url": {}},
                "Date Added": {"date": {}},
                "Quiz Questions": {"rich_text": {}},
                "Flashcards": {"rich_text": {}},
                "Status": {
                    "select": {
                        "options": [
                            {"name": "New", "color": "blue"},
                            {"name": "Reviewed", "color": "green"},
                            {"name": "Archived", "color": "gray"},
                        ]
                    }
                },
                "Priority": {
                    "select": {
                        "options": [
                            {"name": "High", "color": "red"},
                            {"name": "Medium", "color": "yellow"},
                            {"name": "Low", "color": "gray"},
                        ]
                    }
                },
                "Tags": {"multi_select": {}},
                "Key Points": {"rich_text": {}},
                "Learning Objectives": {"rich_text": {}},
            }

            self._rate_limit()
            self.client.databases.update(
                database_id=self.database_id, properties=schema_properties
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

    def get_database_schema(self) -> Dict[str, str]:
        """Get the current database schema"""
        try:
            self._rate_limit()
            response = self.client.databases.retrieve(database_id=self.database_id)
            properties = response.get("properties", {})

            schema = {}
            for prop_name, prop_data in properties.items():
                # Use the 'type' field from the property data
                prop_type = prop_data.get("type", "unknown")
                logger.debug(f"Property '{prop_name}': type={prop_type}")
                schema[prop_name] = prop_type

            return schema
        except Exception as e:
            logger.error(f"Error getting database schema: {str(e)}")
            return {}

    def create_learning_entry(
        self, materials: LearningMaterials
    ) -> Optional[Dict[str, Any]]:
        """Create a new entry in the Notion database, adapting to existing schema"""
        self._rate_limit()

        try:
            article = materials.summary.original_article
            summary = materials.summary

            # Get current database schema
            schema = self.get_database_schema()
            logger.debug(f"Database schema: {schema}")

            # Build properties based on available schema
            properties = {}

            # Title (required, usually exists)
            if "Title" in schema or "Name" in schema:
                title_prop = "Title" if "Title" in schema else "Name"
                properties[title_prop] = {
                    "title": [
                        {"text": {"content": article.title[:100]}}  # Notion title limit
                    ]
                }

            # Topic - adapt to schema type
            topic_mapping = {
                "artificial intelligence": "Artificial Intelligence",
                "machine learning": "Machine Learning",
                "software development": "Software Development",
                "data science": "Data Science",
            }
            topic_name = topic_mapping.get(article.topic.lower(), "General")

            if "Topic" in schema:
                topic_type = schema["Topic"]
                logger.debug(
                    f"Setting Topic field (type: {topic_type}) to: {topic_name}"
                )
                if topic_type == "select":
                    properties["Topic"] = {"select": {"name": topic_name}}
                elif topic_type == "multi_select":
                    properties["Topic"] = {"multi_select": [{"name": topic_name}]}
                elif topic_type == "rich_text":
                    properties["Topic"] = {
                        "rich_text": [{"text": {"content": topic_name}}]
                    }

            # Summary and Notes - try both
            summary_fields = ["Summary", "Notes", "Content"]
            for field in summary_fields:
                if field in schema and schema[field] == "rich_text":
                    logger.debug(f"Setting {field} field with summary content")
                    properties[field] = {
                        "rich_text": [{"text": {"content": summary.summary}}]
                    }
                    break

            # URL - try different common names
            url_fields = ["Source Link", "Source URL", "URL", "Link", "Source"]
            for field in url_fields:
                if field in schema and schema[field] == "url":
                    logger.debug(f"Setting {field} field to: {article.url}")
                    properties[field] = {"url": article.url}
                    break

            # Date - try different common names
            date_fields = ["Date", "Date Added", "Created", "Added"]
            for field in date_fields:
                if field in schema and schema[field] == "date":
                    date_value = datetime.now().isoformat()
                    logger.debug(f"Setting {field} field to: {date_value}")
                    properties[field] = {"date": {"start": date_value}}
                    break

            # Status - adapt to schema type
            if "Status" in schema:
                status_type = schema["Status"]
                logger.debug(f"Setting Status field (type: {status_type}) to: New")
                if status_type == "select":
                    properties["Status"] = {"select": {"name": "New"}}
                elif status_type == "status":
                    properties["Status"] = {"status": {"name": "New"}}
                elif status_type == "rich_text":
                    properties["Status"] = {"rich_text": [{"text": {"content": "New"}}]}

            # Priority and Difficulty
            priority_fields = ["Priority", "Difficulty"]
            for field in priority_fields:
                if field in schema and schema[field] == "select":
                    logger.debug(f"Setting {field} field to: Medium")
                    properties[field] = {"select": {"name": "Medium"}}
                    break

            # Quiz Questions
            quiz_content = self.format_quiz_questions(materials.quiz_questions)
            quiz_fields = ["Quiz Questions", "Quiz", "Questions"]
            for field in quiz_fields:
                if field in schema and schema[field] == "rich_text":
                    logger.debug(
                        f"Setting {field} field with {len(materials.quiz_questions)} questions"
                    )
                    properties[field] = {
                        "rich_text": [{"text": {"content": quiz_content}}]
                    }
                    break

            # Flashcards
            flashcard_content = self.format_flashcards(materials.flashcards)
            flashcard_fields = ["Flashcards", "Cards", "Flash Cards"]
            for field in flashcard_fields:
                if field in schema and schema[field] == "rich_text":
                    logger.debug(
                        f"Setting {field} field with {len(materials.flashcards)} flashcards"
                    )
                    properties[field] = {
                        "rich_text": [{"text": {"content": flashcard_content}}]
                    }
                    break

            # Answers - if it exists as a separate field
            if "Answers" in schema and schema["Answers"] == "rich_text":
                # Combine quiz answers and flashcard answers
                answers_content = (
                    "Quiz Answers:\n"
                    + quiz_content
                    + "\n\nFlashcard Answers:\n"
                    + flashcard_content
                )
                logger.debug(f"Setting Answers field with combined content")
                properties["Answers"] = {
                    "rich_text": [{"text": {"content": answers_content}}]
                }

            # Key Points
            key_points_content = "\n".join(
                [f"• {point}" for point in summary.key_points]
            )
            key_fields = ["Key Points", "Key Insights", "Points"]
            for field in key_fields:
                if field in schema and schema[field] == "rich_text":
                    properties[field] = {
                        "rich_text": [{"text": {"content": key_points_content}}]
                    }
                    break

            # Learning Objectives
            objectives_content = "\n".join(
                [f"• {obj}" for obj in summary.learning_objectives]
            )
            objective_fields = ["Learning Objectives", "Objectives", "Goals"]
            for field in objective_fields:
                if field in schema and schema[field] == "rich_text":
                    properties[field] = {
                        "rich_text": [{"text": {"content": objectives_content}}]
                    }
                    break

            # Debug logging for property values
            logger.debug(f"Creating entry with properties: {list(properties.keys())}")
            for prop_name, prop_value in properties.items():
                logger.debug(f"Property '{prop_name}': {prop_value}")

            # Debug the original data
            logger.debug(f"Original article title: '{article.title}'")
            logger.debug(f"Original article topic: '{article.topic}'")
            logger.debug(
                f"Summary content length: {len(summary.summary) if summary.summary else 0}"
            )
            logger.debug(
                f"Key points count: {len(summary.key_points) if summary.key_points else 0}"
            )
            logger.debug(
                f"Learning objectives count: {len(summary.learning_objectives) if summary.learning_objectives else 0}"
            )
            logger.debug(
                f"Quiz questions count: {len(materials.quiz_questions) if materials.quiz_questions else 0}"
            )
            logger.debug(
                f"Flashcards count: {len(materials.flashcards) if materials.flashcards else 0}"
            )

            response = self.client.pages.create(
                parent={"database_id": self.database_id}, properties=properties
            )

            logger.info(f"Created Notion entry for: {article.title[:50]}...")
            return response

        except APIResponseError as e:
            logger.error(f"Notion API error creating entry: {e.body}")
            return None
        except Exception as e:
            logger.error(f"Error creating Notion entry: {str(e)}")
            return None

    def batch_create_entries(
        self, materials_list: List[LearningMaterials]
    ) -> List[Dict[str, Any]]:
        """Create multiple entries with rate limiting"""
        created_entries = []

        for i, materials in enumerate(materials_list):
            logger.info(f"Creating Notion entry {i+1}/{len(materials_list)}")

            entry = self.create_learning_entry(materials)
            if entry:
                created_entries.append(entry)
            else:
                logger.warning(
                    f"Failed to create entry for: {materials.summary.original_article.title}"
                )

            # Rate limiting between requests
            if i < len(materials_list) - 1:
                time.sleep(0.5)

        logger.info(
            f"Successfully created {len(created_entries)}/{len(materials_list)} Notion entries"
        )
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
                filter={"property": "Date Added", "date": {"after": cutoff_date}},
                sorts=[{"property": "Date Added", "direction": "descending"}],
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
                page_id=page_id, properties={"Status": {"select": {"name": status}}}
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
                "recent_entries": 0,
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
                status_name = (
                    status_prop.get("name", "Unknown") if status_prop else "Unknown"
                )
                stats["statuses"][status_name] = (
                    stats["statuses"].get(status_name, 0) + 1
                )

                # Count recent entries
                date_prop = properties.get("Date Added", {}).get("date", {})
                if date_prop and date_prop.get("start"):
                    entry_date = datetime.fromisoformat(
                        date_prop["start"].replace("Z", "+00:00")
                    )
                    if entry_date.replace(tzinfo=None) >= cutoff_date:
                        stats["recent_entries"] += 1

            logger.info(f"Database stats: {stats}")
            return stats

        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return {}
