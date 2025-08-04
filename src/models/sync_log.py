"""
Sync Log model for tracking operations
"""
from sqlalchemy import Column, String, DateTime, Text, Integer
from .base import BaseModel


class SyncLog(BaseModel):
    """Sync log model for tracking operations"""
    __tablename__ = 'sync_log'
    
    # Operation details
    source = Column(String(20), nullable=False)  # qualys, rt, migration, etc.
    operation = Column(String(50), nullable=False)  # import, update, sync, etc.
    timestamp = Column(DateTime, nullable=False)
    
    # Status
    status = Column(String(20), nullable=False)  # success, error, warning
    
    # Details
    details = Column(Text)
    records_processed = Column(Integer, default=0)
    
    def __repr__(self):
        return f"<SyncLog(source={self.source}, operation={self.operation}, status={self.status})>"
    
    @property
    def is_successful(self) -> bool:
        """Check if operation was successful"""
        return self.status.lower() == "success"
    
    @property
    def summary(self) -> str:
        """Get operation summary"""
        return f"{self.source}.{self.operation}: {self.status} ({self.records_processed} records)"