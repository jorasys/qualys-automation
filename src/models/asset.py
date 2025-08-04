"""
Asset model
"""
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship
from .base import BaseModel


class Asset(BaseModel):
    """Asset model representing scanned hosts"""
    __tablename__ = 'assets'
    
    # Network identification
    ip_address = Column(String(45), nullable=False, unique=True, index=True)  # IPv4 or IPv6
    hostname = Column(String(255))
    
    # System information
    os_type = Column(String(100))
    asset_group = Column(String(100))
    owner = Column(String(100))
    
    # Status
    active = Column(Boolean, default=True)
    
    # Relations
    vulnerability_instances = relationship("VulnerabilityInstance", back_populates="asset", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Asset(ip={self.ip_address}, hostname='{self.hostname}')>"
    
    @property
    def display_name(self) -> str:
        """Get display name (hostname or IP)"""
        return self.hostname if self.hostname else self.ip_address
    
    def get_vulnerability_count(self) -> int:
        """Get count of vulnerabilities for this asset"""
        return len(self.vulnerability_instances)
    
    def get_critical_vulnerability_count(self) -> int:
        """Get count of critical vulnerabilities for this asset"""
        from .vulnerability import SeverityLevel
        return len([
            instance for instance in self.vulnerability_instances
            if instance.vulnerability.severity == SeverityLevel.CRITICAL
        ])