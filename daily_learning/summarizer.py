"""Content summarization module using OpenAI GPT-4"""

import logging
import time
from dataclasses import dataclass
from typing import List, Optional
from urllib import response

import openai

from .content_fetcher import Article

logger = logging.getLogger(__name__)


@dataclass
class Summary:
    """Represents a summarized article"""

    original_article: Article
    summary: str
    key_points: List[str]
    learning_objectives: List[str]


class Summarizer:
    """Handles content summarization using GPT-4"""

    def __init__(self, api_key: str, model: str = "gpt-4-turbo-preview"):
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
        self.last_request_time = 0

    def _rate_limit(self, min_interval: float = 1.0):
        """Basic rate limiting for OpenAI API"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time

        if time_since_last < min_interval:
            sleep_time = min_interval - time_since_last
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f} seconds")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def create_summary_prompt(self, article: Article, sentence_count: int = 4) -> str:
        """Create a prompt for article summarization"""
        return f"""You are an educational content curator. Summarize the latest development in last 7 days about {article.topic} in exactly {sentence_count} sentences that capture the most important learning points. Focus on actionable insights and key concepts that would be valuable for someone learning about {article.topic}. Make it concise but comprehensive.

Title: {article.title}
Source: {article.source}
Content: {article.content}

Please provide:
1. A {sentence_count}-sentence summary
2. 3-5 key points as bullet points
3. 2-3 clear learning objectives

Format your response as JSON with the following structure:
{{
    "summary": "Your {sentence_count}-sentence summary here",
    "key_points": ["Key point 1", "Key point 2", "Key point 3"],
    "learning_objectives": ["Learning objective 1", "Learning objective 2"]
}}"""

    def summarize_article(
        self, article: Article, sentence_count: int = 4
    ) -> Optional[Summary]:
        """Summarize a single article using GPT-4"""
        self._rate_limit()

        try:
            prompt = self.create_summary_prompt(article, sentence_count)

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an expert educational content curator who creates concise, valuable summaries for learners.",
                    },
                    {"role": "user", "content": prompt},
                ],
                temperature=0.3,
                max_tokens=500,
            )

            logger.debug(f"Received response: {response}")
            content = response.choices[0].message.content
            # Log first 200 chars

            # Parse JSON response
            import json

            # Try to extract JSON from markdown code blocks first
            if "```json" in content:
                start = content.find("```json") + 7
                end = content.find("```", start)
                if end > start:
                    json_content = content[start:end].strip()
                    logger.debug(f"Extracted JSON from markdown: {json_content}")
                    try:
                        result = json.loads(json_content)
                    except json.JSONDecodeError as e:
                        logger.error(f"Failed to parse extracted JSON for summary: {e}")
                        # Fallback: treat the entire response as summary
                        return Summary(
                            original_article=article,
                            summary=content[:500],
                            key_points=[],
                            learning_objectives=[],
                        )
                else:
                    logger.error(
                        "Found json markdown but couldn't extract summary content"
                    )
                    return Summary(
                        original_article=article,
                        summary=content[:500],
                        key_points=[],
                        learning_objectives=[],
                    )
            else:
                # Try direct JSON parsing
                try:
                    logger.debug(f"Parsing JSON content: {content[:500]}...")
                    result = json.loads(content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse JSON response for summary: {e}")
                    logger.error(f"Raw response content: {repr(content[:500])}")
                    # Fallback: treat the entire response as summary
                    return Summary(
                        original_article=article,
                        summary=content[:500],
                        key_points=[],
                        learning_objectives=[],
                    )

            logger.debug(f"Received summary response: {result}")

            summary = Summary(
                original_article=article,
                summary=result.get("summary", ""),
                key_points=result.get("key_points", []),
                learning_objectives=result.get("learning_objectives", []),
            )

            logger.info(f"Successfully summarized article: {article.title[:50]}...")
            return summary

        except Exception as e:
            logger.error(f"Error summarizing article '{article.title}': {str(e)}")
            return None

    def summarize_batch(
        self, articles: List[Article], sentence_count: int = 4
    ) -> List[Summary]:
        """Summarize multiple articles with error handling"""
        summaries = []

        for i, article in enumerate(articles):
            logger.info(
                f"Summarizing article {i+1}/{len(articles)}: {article.title[:50]}..."
            )

            summary = self.summarize_article(article, sentence_count)
            if summary:
                summaries.append(summary)
            else:
                logger.warning(f"Failed to summarize article: {article.title}")

            # Add delay between requests
            if i < len(articles) - 1:
                time.sleep(0.5)

        logger.info(
            f"Successfully summarized {len(summaries)}/{len(articles)} articles"
        )
        return summaries

    def enhance_summary_for_learning(self, summary: Summary) -> Summary:
        """Enhance summary with additional learning-focused content"""
        self._rate_limit()

        try:
            enhancement_prompt = f"""Based on this summary about {summary.original_article.topic}, enhance it for better learning outcomes:

Original Summary: {summary.summary}
Key Points: {', '.join(summary.key_points)}

Please provide enhanced content in JSON format:
{{
    "enhanced_summary": "Improved summary with clearer learning focus",
    "difficulty_level": "beginner|intermediate|advanced",
    "estimated_read_time": "X minutes", 
    "prerequisites": ["Prerequisite 1", "Prerequisite 2"],
    "related_topics": ["Related topic 1", "Related topic 2"]
}}"""

            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": "You are an educational expert who enhances content for optimal learning.",
                    },
                    {"role": "user", "content": enhancement_prompt},
                ],
                temperature=0.2,
                max_tokens=300,
            )

            import json

            enhancement = json.loads(response.choices[0].message.content)

            # Update summary with enhanced content
            summary.summary = enhancement.get("enhanced_summary", summary.summary)

            logger.info(
                f"Enhanced summary for: {summary.original_article.title[:50]}..."
            )
            return summary

        except Exception as e:
            logger.error(f"Error enhancing summary: {str(e)}")
            return summary  # Return original if enhancement fails

    def get_content_quality_score(self, summary: Summary) -> float:
        """Assess the quality of summarized content"""
        score = 0.0

        # Check summary length (should be substantive but not too long)
        if 100 <= len(summary.summary) <= 800:
            score += 0.3

        # Check if key points are present
        if len(summary.key_points) >= 3:
            score += 0.3

        # Check if learning objectives are present
        if len(summary.learning_objectives) >= 2:
            score += 0.2

        # Check for educational keywords
        educational_keywords = [
            "learn",
            "understand",
            "concept",
            "method",
            "technique",
            "principle",
            "skill",
        ]
        summary_lower = summary.summary.lower()
        keyword_count = sum(
            1 for keyword in educational_keywords if keyword in summary_lower
        )
        score += min(keyword_count * 0.05, 0.2)

        return min(score, 1.0)  # Cap at 1.0
