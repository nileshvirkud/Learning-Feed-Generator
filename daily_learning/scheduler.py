"""Scheduling and automation features for daily learning feed generation"""

import logging
import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import List, Optional, Callable
from dataclasses import dataclass

from .main import DailyLearningGenerator
from .config import Config

logger = logging.getLogger(__name__)

@dataclass
class ScheduleConfig:
    """Configuration for scheduled runs"""
    enabled: bool = False
    run_time: str = "08:00"  # 24-hour format
    timezone: str = "UTC"
    topics: Optional[List[str]] = None
    weekdays_only: bool = True
    retry_attempts: int = 3
    retry_delay_minutes: int = 30

class LearningFeedScheduler:
    """Handles scheduling and automated execution of learning feed generation"""
    
    def __init__(self, config: Config, schedule_config: ScheduleConfig):
        self.config = config
        self.schedule_config = schedule_config
        self.logger = logging.getLogger(__name__)
        self.is_running = False
        self.scheduler_thread = None
        
        # Initialize the learning generator
        self.generator = DailyLearningGenerator(config)
    
    def setup_schedule(self):
        """Configure the schedule based on settings"""
        if not self.schedule_config.enabled:
            self.logger.info("Scheduler is disabled")
            return
        
        schedule.clear()  # Clear any existing jobs
        
        if self.schedule_config.weekdays_only:
            # Schedule for weekdays only
            schedule.every().monday.at(self.schedule_config.run_time).do(self._run_with_retry)
            schedule.every().tuesday.at(self.schedule_config.run_time).do(self._run_with_retry)
            schedule.every().wednesday.at(self.schedule_config.run_time).do(self._run_with_retry)
            schedule.every().thursday.at(self.schedule_config.run_time).do(self._run_with_retry)
            schedule.every().friday.at(self.schedule_config.run_time).do(self._run_with_retry)
            self.logger.info(f"Scheduled daily runs for weekdays at {self.schedule_config.run_time}")
        else:
            # Schedule for every day
            schedule.every().day.at(self.schedule_config.run_time).do(self._run_with_retry)
            self.logger.info(f"Scheduled daily runs for every day at {self.schedule_config.run_time}")
    
    def _run_with_retry(self):
        """Execute the learning feed generation with retry logic"""
        self.logger.info("Starting scheduled learning feed generation")
        
        for attempt in range(1, self.schedule_config.retry_attempts + 1):
            try:
                self.logger.info(f"Attempt {attempt}/{self.schedule_config.retry_attempts}")
                
                success = self.generator.run_daily_generation(
                    topics=self.schedule_config.topics
                )
                
                if success:
                    self.logger.info("Scheduled generation completed successfully")
                    return
                else:
                    self.logger.warning(f"Attempt {attempt} failed")
                    
            except Exception as e:
                self.logger.error(f"Attempt {attempt} failed with error: {str(e)}", exc_info=True)
            
            # Wait before retry (except for last attempt)
            if attempt < self.schedule_config.retry_attempts:
                self.logger.info(f"Waiting {self.schedule_config.retry_delay_minutes} minutes before retry")
                time.sleep(self.schedule_config.retry_delay_minutes * 60)
        
        self.logger.error(f"All {self.schedule_config.retry_attempts} attempts failed")
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        if self.is_running:
            self.logger.warning("Scheduler is already running")
            return
        
        if not self.schedule_config.enabled:
            self.logger.info("Scheduler is disabled, not starting")
            return
        
        self.setup_schedule()
        self.is_running = True
        
        def run_scheduler():
            self.logger.info("Scheduler started")
            while self.is_running:
                try:
                    schedule.run_pending()
                    time.sleep(60)  # Check every minute
                except Exception as e:
                    self.logger.error(f"Scheduler error: {str(e)}", exc_info=True)
            
            self.logger.info("Scheduler stopped")
        
        self.scheduler_thread = threading.Thread(target=run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("Scheduler thread started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        if not self.is_running:
            self.logger.info("Scheduler is not running")
            return
        
        self.logger.info("Stopping scheduler...")
        self.is_running = False
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        schedule.clear()
        self.logger.info("Scheduler stopped")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """Get the next scheduled run time"""
        if not self.schedule_config.enabled:
            return None
        
        next_job = schedule.next_run()
        return next_job if next_job else None
    
    def get_schedule_info(self) -> dict:
        """Get information about the current schedule"""
        info = {
            "enabled": self.schedule_config.enabled,
            "is_running": self.is_running,
            "run_time": self.schedule_config.run_time,
            "weekdays_only": self.schedule_config.weekdays_only,
            "topics": self.schedule_config.topics,
            "retry_attempts": self.schedule_config.retry_attempts,
            "next_run": None,
            "jobs_count": len(schedule.jobs)
        }
        
        next_run = self.get_next_run_time()
        if next_run:
            info["next_run"] = next_run.isoformat()
        
        return info

class HealthChecker:
    """Monitor the health of scheduled runs and alert on failures"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = logging.getLogger(__name__)
        self.last_successful_run = None
        self.consecutive_failures = 0
        self.max_consecutive_failures = 3
    
    def record_success(self):
        """Record a successful run"""
        self.last_successful_run = datetime.now()
        self.consecutive_failures = 0
        self.logger.info("Health check: Successful run recorded")
    
    def record_failure(self):
        """Record a failed run"""
        self.consecutive_failures += 1
        self.logger.warning(f"Health check: Failure recorded. Consecutive failures: {self.consecutive_failures}")
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            self._alert_on_repeated_failures()
    
    def _alert_on_repeated_failures(self):
        """Handle repeated failures (could send notifications, etc.)"""
        self.logger.error(f"ALERT: {self.consecutive_failures} consecutive failures detected!")
        # Here you could add email notifications, Slack alerts, etc.
    
    def check_health(self) -> dict:
        """Check the overall health of the system"""
        health_status = {
            "status": "healthy",
            "last_successful_run": None,
            "consecutive_failures": self.consecutive_failures,
            "issues": []
        }
        
        if self.last_successful_run:
            health_status["last_successful_run"] = self.last_successful_run.isoformat()
            
            # Check if it's been too long since last success
            hours_since_success = (datetime.now() - self.last_successful_run).total_seconds() / 3600
            if hours_since_success > 48:  # 2 days
                health_status["status"] = "warning"
                health_status["issues"].append(f"No successful run in {hours_since_success:.1f} hours")
        
        if self.consecutive_failures >= self.max_consecutive_failures:
            health_status["status"] = "critical"
            health_status["issues"].append(f"{self.consecutive_failures} consecutive failures")
        
        return health_status

def create_scheduler_from_env() -> LearningFeedScheduler:
    """Create scheduler from environment variables"""
    import os
    
    config = Config.from_env()
    
    schedule_config = ScheduleConfig(
        enabled=os.getenv("SCHEDULER_ENABLED", "false").lower() == "true",
        run_time=os.getenv("SCHEDULER_RUN_TIME", "08:00"),
        timezone=os.getenv("SCHEDULER_TIMEZONE", "UTC"),
        weekdays_only=os.getenv("SCHEDULER_WEEKDAYS_ONLY", "true").lower() == "true",
        retry_attempts=int(os.getenv("SCHEDULER_RETRY_ATTEMPTS", "3")),
        retry_delay_minutes=int(os.getenv("SCHEDULER_RETRY_DELAY_MINUTES", "30"))
    )
    
    # Parse topics if provided
    topics_env = os.getenv("SCHEDULER_TOPICS")
    if topics_env:
        schedule_config.topics = [topic.strip() for topic in topics_env.split(',')]
    
    return LearningFeedScheduler(config, schedule_config)