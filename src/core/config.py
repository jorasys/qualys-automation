"""
Configuration manager for Qualys Automation
Handles loading of settings, templates, and environment variables
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from dotenv import load_dotenv


@dataclass
class APIConfig:
    """Configuration for Qualys API"""
    base_url: str
    username: str
    password: str
    proxy_url: Optional[str] = None
    timeout: int = 30
    max_retries: int = 3


@dataclass
class DatabaseConfig:
    """Configuration for database connection"""
    type: str = "sqlite"
    path: str = "data/qualys_vuln.db"
    echo: bool = False
    pool_size: int = 5


@dataclass
class ReportsConfig:
    """Configuration for reports handling"""
    max_concurrent: int = 8
    max_running_reports: int = 8
    download_path: str = "Downloads"
    formats: List[str] = None
    cleanup_after_days: int = 30
    creation_controls: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.formats is None:
            self.formats = ["pdf", "csv"]
        if self.creation_controls is None:
            self.creation_controls = {
                "check_slots_before_creation": True,
                "max_wait_for_slots": 1800,
                "slot_check_interval": 30,
                "pause_between_reports": 2,
                "batch_size": 4
            }


@dataclass
class LoggingConfig:
    """Configuration for logging"""
    level: str = "INFO"
    format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    file: str = "logs/qualys_automation.log"
    max_bytes: int = 10485760
    backup_count: int = 5


class ConfigManager:
    """Central configuration manager"""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        
        # Load environment variables
        load_dotenv()
        
        # Load configuration files
        self._settings = self._load_settings()
        self._templates = self._load_templates()
        
        # Validate required environment variables
        self._validate_credentials()
    
    def _load_settings(self) -> Dict[str, Any]:
        """Load settings from JSON file"""
        settings_file = self.config_dir / "settings.json"
        
        if not settings_file.exists():
            raise FileNotFoundError(f"Settings file not found: {settings_file}")
        
        with open(settings_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _load_templates(self) -> Dict[str, Any]:
        """Load templates from JSON file"""
        templates_file = self.config_dir / "templates.json"
        
        if not templates_file.exists():
            raise FileNotFoundError(f"Templates file not found: {templates_file}")
        
        with open(templates_file, 'r', encoding='utf-8') as f:
            return json.load(f)
    
    def _validate_credentials(self):
        """Validate that required credentials are present"""
        username = os.getenv("QUALYS_USERNAME")
        password = os.getenv("QUALYS_PASSWORD")
        
        if not username or not password:
            raise ValueError(
                "Missing Qualys credentials. Please set QUALYS_USERNAME and QUALYS_PASSWORD "
                "environment variables or create a .env file from .env.example"
            )
    
    @property
    def api(self) -> APIConfig:
        """Get API configuration"""
        api_config = self._settings["api"]
        
        return APIConfig(
            base_url=api_config["base_url"],
            username=os.getenv("QUALYS_USERNAME"),
            password=os.getenv("QUALYS_PASSWORD"),
            proxy_url=api_config["proxy"]["url"] if api_config["proxy"]["enabled"] else None,
            timeout=api_config.get("timeout", 30),
            max_retries=api_config.get("max_retries", 3)
        )
    
    @property
    def database(self) -> DatabaseConfig:
        """Get database configuration"""
        db_config = self._settings["database"]
        return DatabaseConfig(**db_config)
    
    @property
    def reports(self) -> ReportsConfig:
        """Get reports configuration"""
        reports_config = self._settings["reports"]
        return ReportsConfig(**reports_config)
    
    @property
    def logging(self) -> LoggingConfig:
        """Get logging configuration"""
        logging_config = self._settings["logging"]
        return LoggingConfig(**logging_config)
    
    def get_scan_templates(self) -> List[Dict[str, Any]]:
        """Get scan-based report templates"""
        return self._templates["scan_based_reports"]
    
    def get_host_templates(self) -> List[Dict[str, Any]]:
        """Get host-based report templates"""
        return self._templates["host_based_reports"]
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific template by ID"""
        all_templates = self.get_scan_templates() + self.get_host_templates()
        
        for template in all_templates:
            if template["template_id"] == template_id:
                return template
        
        return None
    
    def get_database_url(self) -> str:
        """Get database URL for SQLAlchemy"""
        db_config = self.database
        
        if db_config.type == "sqlite":
            # Ensure data directory exists
            data_dir = Path(db_config.path).parent
            data_dir.mkdir(exist_ok=True)
            return f"sqlite:///{db_config.path}"
        elif db_config.type == "postgresql":
            database_url = os.getenv("DATABASE_URL")
            if not database_url:
                raise ValueError("DATABASE_URL environment variable required for PostgreSQL")
            return database_url
        else:
            raise ValueError(f"Unsupported database type: {db_config.type}")


# Global configuration instance
config = ConfigManager()