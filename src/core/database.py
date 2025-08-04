"""
Database configuration and session management
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
from typing import Generator

from .config import config
from .exceptions import DatabaseError


class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self._engine = None
        self._session_factory = None
        self._initialize()
    
    def _initialize(self):
        """Initialize database engine and session factory"""
        try:
            database_url = config.get_database_url()
            db_config = config.database
            
            # Configure engine based on database type
            if db_config.type == "sqlite":
                self._engine = create_engine(
                    database_url,
                    echo=db_config.echo,
                    poolclass=StaticPool,
                    connect_args={"check_same_thread": False}
                )
            else:
                self._engine = create_engine(
                    database_url,
                    echo=db_config.echo,
                    pool_size=db_config.pool_size
                )
            
            self._session_factory = sessionmaker(bind=self._engine)
            
        except Exception as e:
            raise DatabaseError(f"Failed to initialize database: {e}")
    
    @property
    def engine(self):
        """Get database engine"""
        return self._engine
    
    def create_session(self) -> Session:
        """Create a new database session"""
        if not self._session_factory:
            raise DatabaseError("Database not initialized")
        
        return self._session_factory()
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """Context manager for database sessions"""
        session = self.create_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            raise DatabaseError(f"Database operation failed: {e}")
        finally:
            session.close()
    
    def create_tables(self):
        """Create all tables (for development/testing)"""
        try:
            from ..models.base import Base
            Base.metadata.create_all(self._engine)
        except Exception as e:
            raise DatabaseError(f"Failed to create tables: {e}")
    
    def drop_tables(self):
        """Drop all tables (for development/testing)"""
        try:
            from ..models.base import Base
            Base.metadata.drop_all(self._engine)
        except Exception as e:
            raise DatabaseError(f"Failed to drop tables: {e}")


# Global database manager instance
db_manager = DatabaseManager()