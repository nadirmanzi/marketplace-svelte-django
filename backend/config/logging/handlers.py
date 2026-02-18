"""
Custom file handlers for the logging system.

Provides MonthlyRotatingFileHandler which combines:
- Size-based rotation (10MB limit)
- Monthly file naming (e.g., default-Dec-2024.log)
- Automatic overflow handling (.1, .2 suffixes)
"""
import logging.handlers
from datetime import datetime
from pathlib import Path


# Default configuration
MAX_BYTES = 10 * 1024 * 1024  # 10MB
BACKUP_COUNT = 5


class MonthlyRotatingFileHandler(logging.handlers.RotatingFileHandler):
    """
    File handler with monthly naming and size-based rotation.
    
    Creates files like: default-Dec-2024.log, error-Dec-2024.log
    When file exceeds MAX_BYTES, rotates to .1, .2, etc.
    On month change, starts fresh file with new month name.
    
    Args:
        prefix: File prefix (e.g., "default", "error")
        logs_dir: Directory for log files
        max_bytes: Size limit before rotation (default: 10MB)
        backup_count: Number of backup files to keep (default: 5)
    """
    
    def __init__(
        self,
        prefix: str,
        logs_dir: Path = None,
        max_bytes: int = MAX_BYTES,
        backup_count: int = BACKUP_COUNT
    ):
        from .config import LOGS_DIR
        
        self.prefix = prefix
        self.logs_dir = Path(logs_dir) if logs_dir else LOGS_DIR
        self.logs_dir.mkdir(exist_ok=True)
        self.current_month = self._get_month_str()
        
        super().__init__(
            filename=self._get_filename(),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8"
        )
    
    def _get_month_str(self) -> str:
        """Get current month string (e.g., '12-2024')."""
        return datetime.now().strftime("%m-%Y")
    
    def _get_filename(self) -> str:
        """Generate filename for current month."""
        return str(self.logs_dir / f"{self.prefix}-{self.current_month}.log")
    
    def shouldRollover(self, record) -> bool:
        """Check for month change or size limit."""
        new_month = self._get_month_str()
        
        if new_month != self.current_month:
            self.current_month = new_month
            self.baseFilename = self._get_filename()
            if self.stream:
                self.stream.close()
                self.stream = None
            return False
        
        return super().shouldRollover(record)
