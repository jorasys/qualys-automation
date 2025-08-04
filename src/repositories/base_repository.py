"""
Base repository with common CRUD operations
"""
from typing import TypeVar, Generic, List, Optional, Type, Any, Dict
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_

from ..core.database import db_manager
from ..models.base import BaseModel

T = TypeVar('T', bound=BaseModel)


class BaseRepository(Generic[T]):
    """Base repository with common database operations"""
    
    def __init__(self, model_class: Type[T]):
        self.model_class = model_class
    
    def create(self, session: Session, **kwargs) -> T:
        """Create a new record"""
        instance = self.model_class(**kwargs)
        session.add(instance)
        session.flush()  # Get the ID without committing
        return instance
    
    def get_by_id(self, session: Session, record_id: int) -> Optional[T]:
        """Get record by ID"""
        return session.query(self.model_class).filter(self.model_class.id == record_id).first()
    
    def get_all(self, session: Session, limit: Optional[int] = None, offset: int = 0) -> List[T]:
        """Get all records with optional pagination"""
        query = session.query(self.model_class).offset(offset)
        if limit:
            query = query.limit(limit)
        return query.all()
    
    def update(self, session: Session, record_id: int, **kwargs) -> Optional[T]:
        """Update record by ID"""
        instance = self.get_by_id(session, record_id)
        if instance:
            for key, value in kwargs.items():
                if hasattr(instance, key):
                    setattr(instance, key, value)
            session.flush()
        return instance
    
    def delete(self, session: Session, record_id: int) -> bool:
        """Delete record by ID"""
        instance = self.get_by_id(session, record_id)
        if instance:
            session.delete(instance)
            session.flush()
            return True
        return False
    
    def count(self, session: Session) -> int:
        """Count total records"""
        return session.query(self.model_class).count()
    
    def exists(self, session: Session, **filters) -> bool:
        """Check if record exists with given filters"""
        query = session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.first() is not None
    
    def find_by(self, session: Session, **filters) -> List[T]:
        """Find records by filters"""
        query = session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.all()
    
    def find_one_by(self, session: Session, **filters) -> Optional[T]:
        """Find one record by filters"""
        query = session.query(self.model_class)
        for key, value in filters.items():
            if hasattr(self.model_class, key):
                query = query.filter(getattr(self.model_class, key) == value)
        return query.first()
    
    def bulk_create(self, session: Session, records: List[Dict[str, Any]]) -> List[T]:
        """Create multiple records"""
        instances = [self.model_class(**record) for record in records]
        session.add_all(instances)
        session.flush()
        return instances
    
    def get_or_create(self, session: Session, defaults: Optional[Dict[str, Any]] = None, **kwargs) -> tuple[T, bool]:
        """Get existing record or create new one"""
        instance = self.find_one_by(session, **kwargs)
        if instance:
            return instance, False
        
        # Create new instance
        create_kwargs = kwargs.copy()
        if defaults:
            create_kwargs.update(defaults)
        
        instance = self.create(session, **create_kwargs)
        return instance, True