"""Quiz and flashcard generation module using OpenAI GPT-4"""

import logging
import openai
import json
import time
from typing import List, Dict, Optional
from dataclasses import dataclass
from .summarizer import Summary

logger = logging.getLogger(__name__)

@dataclass
class QuizQuestion:
    """Represents a quiz question"""
    question: str
    question_type: str  # 'multiple_choice' or 'short_answer'
    options: List[str]  # Empty for short_answer
    correct_answer: str
    explanation: str
    difficulty: str  # 'easy', 'medium', 'hard'

@dataclass
class Flashcard:
    """Represents a flashcard"""
    question: str
    answer: str
    category: str
    difficulty: str
    hint: Optional[str] = None

@dataclass
class LearningMaterials:
    """Combined quiz questions and flashcards for a summary"""
    summary: Summary
    quiz_questions: List[QuizQuestion]
    flashcards: List[Flashcard]
    
class QuizGenerator:
    """Generates quiz questions and flashcards from summaries"""
    
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
    
    def create_quiz_prompt(self, summary: Summary, num_questions: int = 2) -> str:
        """Create prompt for quiz question generation"""
        return f"""Based on this summary about {summary.original_article.topic}, create {num_questions} quiz questions that test understanding of the key concepts. 

Summary: {summary.summary}
Key Points: {', '.join(summary.key_points)}
Learning Objectives: {', '.join(summary.learning_objectives)}

Create a mix of question types:
- At least 1 multiple-choice question with 4 options
- At least 1 short-answer question

Each question should:
- Test understanding of core concepts
- Be clear and unambiguous
- Have appropriate difficulty level
- Include an explanation of the correct answer

Format as JSON:
{{
    "questions": [
        {{
            "question": "Question text here",
            "type": "multiple_choice",
            "options": ["A) Option 1", "B) Option 2", "C) Option 3", "D) Option 4"],
            "correct_answer": "A) Option 1",
            "explanation": "Explanation of why this is correct",
            "difficulty": "medium"
        }},
        {{
            "question": "Question text here", 
            "type": "short_answer",
            "options": [],
            "correct_answer": "Expected answer",
            "explanation": "What makes a good answer",
            "difficulty": "medium"
        }}
    ]
}}"""
    
    def create_flashcard_prompt(self, summary: Summary, num_flashcards: int = 3) -> str:
        """Create prompt for flashcard generation"""
        return f"""Based on this summary about {summary.original_article.topic}, create {num_flashcards} flashcards for spaced repetition learning.

Summary: {summary.summary}
Key Points: {', '.join(summary.key_points)}

Each flashcard should:
- Have a clear, specific question
- Have a concise but complete answer
- Focus on key definitions, concepts, or actionable insights
- Be suitable for quick review
- Include a helpful hint if the concept is complex

Format as JSON:
{{
    "flashcards": [
        {{
            "question": "What is...", 
            "answer": "Concise answer here",
            "category": "{summary.original_article.topic}",
            "difficulty": "easy|medium|hard",
            "hint": "Optional hint for complex concepts"
        }}
    ]
}}"""
    
    def generate_quiz_questions(self, summary: Summary, num_questions: int = 2) -> List[QuizQuestion]:
        """Generate quiz questions for a summary"""
        self._rate_limit()
        
        try:
            prompt = self.create_quiz_prompt(summary, num_questions)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert educator who creates effective quiz questions to test comprehension and retention."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=800
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            questions = []
            for q_data in result.get("questions", []):
                question = QuizQuestion(
                    question=q_data.get("question", ""),
                    question_type=q_data.get("type", "short_answer"),
                    options=q_data.get("options", []),
                    correct_answer=q_data.get("correct_answer", ""),
                    explanation=q_data.get("explanation", ""),
                    difficulty=q_data.get("difficulty", "medium")
                )
                questions.append(question)
            
            logger.info(f"Generated {len(questions)} quiz questions for: {summary.original_article.title[:50]}...")
            return questions
            
        except Exception as e:
            logger.error(f"Error generating quiz questions: {str(e)}")
            return []
    
    def generate_flashcards(self, summary: Summary, num_flashcards: int = 3) -> List[Flashcard]:
        """Generate flashcards for a summary"""
        self._rate_limit()
        
        try:
            prompt = self.create_flashcard_prompt(summary, num_flashcards)
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are an expert in spaced repetition learning who creates effective flashcards for knowledge retention."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=600
            )
            
            content = response.choices[0].message.content
            result = json.loads(content)
            
            flashcards = []
            for f_data in result.get("flashcards", []):
                flashcard = Flashcard(
                    question=f_data.get("question", ""),
                    answer=f_data.get("answer", ""),
                    category=f_data.get("category", summary.original_article.topic),
                    difficulty=f_data.get("difficulty", "medium"),
                    hint=f_data.get("hint")
                )
                flashcards.append(flashcard)
            
            logger.info(f"Generated {len(flashcards)} flashcards for: {summary.original_article.title[:50]}...")
            return flashcards
            
        except Exception as e:
            logger.error(f"Error generating flashcards: {str(e)}")
            return []
    
    def generate_learning_materials(self, summary: Summary, num_questions: int = 2, num_flashcards: int = 3) -> LearningMaterials:
        """Generate both quiz questions and flashcards for a summary"""
        logger.info(f"Generating learning materials for: {summary.original_article.title[:50]}...")
        
        quiz_questions = self.generate_quiz_questions(summary, num_questions)
        time.sleep(0.5)  # Brief pause between API calls
        flashcards = self.generate_flashcards(summary, num_flashcards)
        
        return LearningMaterials(
            summary=summary,
            quiz_questions=quiz_questions,
            flashcards=flashcards
        )
    
    def generate_batch_materials(self, summaries: List[Summary], num_questions: int = 2, num_flashcards: int = 3) -> List[LearningMaterials]:
        """Generate learning materials for multiple summaries"""
        materials = []
        
        for i, summary in enumerate(summaries):
            logger.info(f"Processing summary {i+1}/{len(summaries)}")
            
            learning_material = self.generate_learning_materials(summary, num_questions, num_flashcards)
            materials.append(learning_material)
            
            # Add delay between summaries to respect rate limits
            if i < len(summaries) - 1:
                time.sleep(1)
        
        logger.info(f"Generated learning materials for {len(materials)} summaries")
        return materials
    
    def assess_question_quality(self, question: QuizQuestion) -> float:
        """Assess the quality of a quiz question"""
        score = 0.0
        
        # Check question length (should be clear but not too long)
        if 10 <= len(question.question) <= 200:
            score += 0.3
        
        # Check if explanation is provided
        if question.explanation and len(question.explanation) > 10:
            score += 0.3
        
        # Check multiple choice options
        if question.question_type == "multiple_choice":
            if len(question.options) == 4:
                score += 0.2
            if question.correct_answer in question.options:
                score += 0.2
        
        return min(score, 1.0)
    
    def assess_flashcard_quality(self, flashcard: Flashcard) -> float:
        """Assess the quality of a flashcard"""
        score = 0.0
        
        # Check question clarity (should be concise)
        if 5 <= len(flashcard.question) <= 100:
            score += 0.4
        
        # Check answer completeness
        if 5 <= len(flashcard.answer) <= 200:
            score += 0.4
        
        # Check if category is set
        if flashcard.category:
            score += 0.2
        
        return min(score, 1.0)