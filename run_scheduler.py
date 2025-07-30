#!/usr/bin/env python3
"""Standalone script to run the learning feed scheduler as a daemon"""

import sys
import signal
import time
from daily_learning.scheduler import create_scheduler_from_env, HealthChecker
from daily_learning.config import Config

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\nReceived signal {signum}. Shutting down gracefully...")
    global scheduler, running
    if scheduler:
        scheduler.stop_scheduler()
    running = False

def main():
    """Main function to run the scheduler"""
    global scheduler, running
    
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)  # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    try:
        # Create scheduler
        scheduler = create_scheduler_from_env()
        
        # Validate configuration
        if not scheduler.generator.validate_setup():
            print("Setup validation failed. Please check your configuration.")
            sys.exit(1)
        
        # Start scheduler
        scheduler.start_scheduler()
        
        # Print status
        schedule_info = scheduler.get_schedule_info()
        print("Daily Learning Feed Scheduler")
        print("=" * 40)
        print(f"Enabled: {schedule_info['enabled']}")
        print(f"Run Time: {schedule_info['run_time']}")
        print(f"Weekdays Only: {schedule_info['weekdays_only']}")
        print(f"Topics: {schedule_info['topics'] or 'Default topics'}")
        print(f"Next Run: {schedule_info['next_run'] or 'Not scheduled'}")
        print(f"Jobs: {schedule_info['jobs_count']}")
        print("\nScheduler is running. Press Ctrl+C to stop.")
        
        # Keep the main thread alive
        running = True
        while running:
            time.sleep(1)
    
    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        sys.exit(1)
    finally:
        if 'scheduler' in locals():
            scheduler.stop_scheduler()
        print("Scheduler stopped")

if __name__ == "__main__":
    scheduler = None
    running = False
    main()