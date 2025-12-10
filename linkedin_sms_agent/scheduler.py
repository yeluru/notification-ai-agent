"""Scheduling logic with jitter for randomized run times."""

import random
from datetime import datetime, timedelta, timezone
from typing import Optional

from .config import SchedulerConfig


def _make_naive_utc(dt: datetime) -> datetime:
    """Convert timezone-aware datetime to naive UTC datetime."""
    if dt.tzinfo is not None:
        # Convert to UTC and remove timezone info
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def should_run_now(
    last_run: Optional[datetime],
    config: SchedulerConfig
) -> bool:
    """
    Determine if the agent should run now based on the last run time and jitter logic.
    
    Logic:
    - If last_run is None, return True (first run).
    - If gap < min_gap_minutes, return False (too soon).
    - If gap >= max_gap_minutes, return True (definitely time to run).
    - If min_gap_minutes <= gap < max_gap_minutes, return True with 50% probability.
    
    Args:
        last_run: Timestamp of the last run, or None if never run.
        config: Scheduler configuration.
        
    Returns:
        True if the agent should run now, False otherwise.
    """
    if last_run is None:
        return True
    
    # Ensure both are naive UTC datetimes for comparison
    now = datetime.utcnow()
    last_run_naive = _make_naive_utc(last_run)
    
    gap = now - last_run_naive
    min_gap = timedelta(minutes=config.min_gap_minutes)
    max_gap = timedelta(minutes=config.max_gap_minutes)
    
    if gap < min_gap:
        return False
    
    if gap >= max_gap:
        return True
    
    # Between min and max: random probability
    return random.random() < 0.5

