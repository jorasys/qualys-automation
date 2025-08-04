"""
Scan Report model
"""
from sqlalchemy import Column, String, DateTime, Integer
from .base import BaseModel


class ScanReport(BaseModel):
    """Scan report model"""
    __tablename__ = 'scan_reports'
    
    # Qualys report identification
    qualys_report_id = Column(String(50), nullable=False, unique=True, index=True)
    report_type = Column(String(10), nullable=False)  # PDF, CSV, scan, host
    
    # File information
    file_path = Column(String(500))
    
    # Temporal information
    scan_date = Column(DateTime)
    imported_at = Column(DateTime)
    
    # Statistics
    vulnerabilities_count = Column(Integer, default=0)
    
    # Status
    status = Column(String(20), default="imported")  # imported, processing, error, historical
    
    def __repr__(self):
        return f"<ScanReport(id={self.qualys_report_id}, type={self.report_type}, status={self.status})>"
    
    @property
    def is_processed(self) -> bool:
        """Check if report has been processed"""
        return self.status in ["imported", "processed"]
    
    @property
    def filename(self) -> str:
        """Get filename from file path"""
        if self.file_path:
            from pathlib import Path
            return Path(self.file_path).name
        return f"report_{self.qualys_report_id}.{self.report_type.lower()}"