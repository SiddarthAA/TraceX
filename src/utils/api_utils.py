"""API call tracker and rate limiter."""

import time
from typing import Dict, Any, Callable
from datetime import datetime
import json
from pathlib import Path


class APICallTracker:
    """Track API calls and costs."""
    
    def __init__(self):
        self.calls = []
        self.total_calls = 0
        self.total_tokens_input = 0
        self.total_tokens_output = 0
        self.start_time = datetime.now()
        
    def log_call(self, model: str, purpose: str, tokens_input: int, tokens_output: int):
        """Log an API call."""
        call = {
            'timestamp': datetime.now().isoformat(),
            'model': model,
            'purpose': purpose,
            'tokens_input': tokens_input,
            'tokens_output': tokens_output,
            'tokens_total': tokens_input + tokens_output
        }
        self.calls.append(call)
        self.total_calls += 1
        self.total_tokens_input += tokens_input
        self.total_tokens_output += tokens_output
        
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics."""
        elapsed = (datetime.now() - self.start_time).total_seconds()
        
        return {
            'total_calls': self.total_calls,
            'total_tokens_input': self.total_tokens_input,
            'total_tokens_output': self.total_tokens_output,
            'total_tokens': self.total_tokens_input + self.total_tokens_output,
            'elapsed_seconds': elapsed,
            'calls_per_minute': (self.total_calls / elapsed * 60) if elapsed > 0 else 0,
            'calls': self.calls
        }
    
    def print_summary(self):
        """Print summary to console."""
        summary = self.get_summary()
        
        print("\n" + "="*80)
        print("📊 API CALL SUMMARY")
        print("="*80)
        print(f"Total API Calls:       {summary['total_calls']}")
        print(f"Input Tokens:          {summary['total_tokens_input']:,}")
        print(f"Output Tokens:         {summary['total_tokens_output']:,}")
        print(f"Total Tokens:          {summary['total_tokens']:,}")
        print(f"Elapsed Time:          {summary['elapsed_seconds']:.1f}s")
        print(f"Calls per Minute:      {summary['calls_per_minute']:.1f}")
        print("\nBreakdown by Purpose:")
        
        by_purpose = {}
        for call in self.calls:
            purpose = call['purpose']
            if purpose not in by_purpose:
                by_purpose[purpose] = {'count': 0, 'tokens': 0}
            by_purpose[purpose]['count'] += 1
            by_purpose[purpose]['tokens'] += call['tokens_total']
        
        for purpose, stats in sorted(by_purpose.items()):
            print(f"  {purpose:20s}: {stats['count']:3d} calls, {stats['tokens']:8,} tokens")
        print("="*80)
    
    def save(self, filepath: str):
        """Save tracker data to file."""
        Path(filepath).parent.mkdir(parents=True, exist_ok=True)
        with open(filepath, 'w') as f:
            json.dump(self.get_summary(), f, indent=2)


class RateLimiter:
    """Handle rate limiting with exponential backoff."""
    
    def __init__(self, max_retries: int = 5, base_delay: float = 1.0):
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.last_call_time = 0
        self.min_interval = 0.1  # Minimum time between calls
        
    def wait_if_needed(self):
        """Wait if needed to respect rate limits."""
        current_time = time.time()
        time_since_last = current_time - self.last_call_time
        
        if time_since_last < self.min_interval:
            wait_time = self.min_interval - time_since_last
            time.sleep(wait_time)
        
        self.last_call_time = time.time()
    
    def call_with_retry(self, func: Callable, *args, **kwargs) -> Any:
        """
        Call function with exponential backoff retry on rate limits.
        
        Args:
            func: Function to call
            *args, **kwargs: Arguments to pass to function
            
        Returns:
            Function result
            
        Raises:
            Exception if all retries exhausted
        """
        for attempt in range(self.max_retries):
            try:
                self.wait_if_needed()
                return func(*args, **kwargs)
                
            except Exception as e:
                error_str = str(e).lower()
                
                # Check if it's a rate limit error
                if 'rate' in error_str or 'limit' in error_str or '429' in error_str:
                    if attempt < self.max_retries - 1:
                        # Exponential backoff
                        delay = self.base_delay * (2 ** attempt)
                        print(f"⚠️  Rate limit hit. Waiting {delay:.1f}s before retry {attempt + 1}/{self.max_retries}...")
                        time.sleep(delay)
                        continue
                    else:
                        print(f"❌ Rate limit: All {self.max_retries} retries exhausted")
                        raise
                
                # Check if it's a timeout or connection error
                elif 'timeout' in error_str or 'connection' in error_str:
                    if attempt < self.max_retries - 1:
                        delay = self.base_delay * (2 ** attempt)
                        print(f"⚠️  Connection error. Retrying in {delay:.1f}s...")
                        time.sleep(delay)
                        continue
                    else:
                        raise
                
                # Other errors - don't retry
                else:
                    raise
        
        # Should never reach here
        raise Exception("Max retries exceeded")


# Global instances
api_tracker = APICallTracker()
rate_limiter = RateLimiter(max_retries=5, base_delay=2.0)


def api_tracker_decorator():
    """
    Decorator to track API calls.
    
    Usage:
        @api_tracker_decorator()
        def my_api_function(...):
            ...
    """
    from functools import wraps
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Just call the function - tracking happens inside
            return func(*args, **kwargs)
        return wrapper
    return decorator


def rate_limit_decorator(max_calls_per_minute: int = 30):
    """
    Decorator to rate limit function calls.
    
    Args:
        max_calls_per_minute: Maximum calls allowed per minute
    """
    import time
    from functools import wraps
    
    min_interval = 60.0 / max_calls_per_minute
    last_call = {'time': 0.0}
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Wait if needed
            current_time = time.time()
            time_since_last = current_time - last_call['time']
            
            if time_since_last < min_interval:
                wait_time = min_interval - time_since_last
                time.sleep(wait_time)
            
            # Update last call time
            last_call['time'] = time.time()
            
            # Call function
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator
