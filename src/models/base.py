"""
Base model configuration and database setup for Engine Framework.

This module provides:
1. SQLAlchemy Base class with common fields
2. Database connection and async session management  
3. Alembic migration configuration
4. Common model utilities and validators

Based on Engine Framework data model specification.
"""

import uuid
from datetime import datetime
from typing import Any, Dict, Optional, List, Union, AsyncGenerator
from sqlalchemy import (
    Column, 
    String, 
    DateTime, 
    Boolean, 
    Text, 
    Integer,
    MetaData,
    event
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func, text
from sqlalchemy.types import TypeDecorator, String as SQLString
import json
import os
from pathlib import Path

# Database Configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://engine:engine@localhost:5432/engine_db"
)

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL", 
    "postgresql+asyncpg://engine:engine@localhost:5432/engine_test_db"
)

# SQLAlchemy async engine configuration
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    pool_size=20,
    max_overflow=30,
    pool_pre_ping=True,
    pool_recycle=3600  # 1 hour
)

test_engine = create_async_engine(
    TEST_DATABASE_URL,
    echo=False,  # Reduce noise in tests
    pool_size=5,
    max_overflow=10
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

TestAsyncSessionLocal = async_sessionmaker(
    bind=test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False
)

# Naming convention for constraints (required for Alembic)
convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

metadata = MetaData(naming_convention=convention)


class JSONType(TypeDecorator):
    """Custom JSON type that handles serialization properly."""
    
    impl = Text
    cache_ok = True

    def process_bind_param(self, value: Any, dialect) -> Optional[str]:
        if value is not None:
            return json.dumps(value, default=str, ensure_ascii=False)
        return value

    def process_result_value(self, value: Optional[str], dialect) -> Any:
        if value is not None:
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value


# Base class with common fields and functionality
Base = declarative_base(metadata=metadata)


class BaseModel(Base):
    """
    Abstract base model with common fields and functionality.
    
    All Engine Framework entities inherit from this base class.
    Provides:
    - id: Primary key (UUID)
    - created_at: Creation timestamp
    - updated_at: Last update timestamp  
    - is_active: Soft deletion flag
    - metadata: Additional metadata storage
    """
    
    __abstract__ = True

    # Primary key as UUID
    id = Column(
        UUID(as_uuid=True), 
        primary_key=True, 
        default=uuid.uuid4,
        index=True,
        comment="Unique identifier for the entity"
    )
    
    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        comment="Entity creation timestamp"
    )
    
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        index=True,
        comment="Entity last update timestamp"
    )
    
    # Soft deletion
    is_active = Column(
        Boolean,
        default=True,
        nullable=False,
        index=True,
        comment="Flag for soft deletion (True = active, False = deleted)"
    )
    
    # Flexible metadata storage
    metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional metadata and configuration"
    )

    def __repr__(self) -> str:
        """String representation of the model."""
        return f"<{self.__class__.__name__}(id={self.id})>"

    def to_dict(self, exclude: Optional[List[str]] = None) -> Dict[str, Any]:
        """Convert model instance to dictionary."""
        exclude = exclude or []
        result = {}
        
        for column in self.__table__.columns:
            if column.name not in exclude:
                value = getattr(self, column.name)
                # Handle UUID and datetime serialization
                if isinstance(value, uuid.UUID):
                    value = str(value)
                elif isinstance(value, datetime):
                    value = value.isoformat()
                result[column.name] = value
        
        return result

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "BaseModel":
        """Create model instance from dictionary."""
        # Remove None values
        filtered_data = {k: v for k, v in data.items() if v is not None}
        
        # Handle UUID fields
        if "id" in filtered_data and isinstance(filtered_data["id"], str):
            try:
                filtered_data["id"] = uuid.UUID(filtered_data["id"])
            except ValueError:
                pass  # Keep as string if invalid UUID
        
        return cls(**filtered_data)

    def update_from_dict(self, data: Dict[str, Any], exclude: Optional[List[str]] = None) -> None:
        """Update model instance from dictionary."""
        exclude = exclude or ["id", "created_at"]  # Don't update immutable fields
        
        for key, value in data.items():
            if key not in exclude and hasattr(self, key):
                setattr(self, key, value)


class StringIdentifierMixin:
    """
    Mixin for models that use string identifiers instead of UUID.
    
    Used for entities like agents, projects, workflows where users
    provide meaningful string IDs.
    """
    
    id = Column(
        String(255),
        primary_key=True,
        index=True,
        comment="User-defined string identifier"
    )

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__}(id='{self.id}')>"


class TimestampMixin:
    """Mixin for additional timestamp fields."""
    
    last_accessed_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Last access timestamp"
    )
    
    last_executed_at = Column(
        DateTime(timezone=True), 
        nullable=True,
        comment="Last execution timestamp"
    )


class ConfigurationMixin:
    """Mixin for configuration storage."""
    
    config = Column(
        JSONB,
        nullable=True,
        default=dict,
        comment="Entity configuration settings"
    )

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value by key."""
        config_value = getattr(self, 'config', None)
        if config_value:
            return config_value.get(key, default)
        return default

    def set_config(self, key: str, value: Any) -> None:
        """Set configuration value by key."""
        config_value = getattr(self, 'config', None)
        if config_value is None:
            setattr(self, 'config', {})
        config_dict = getattr(self, 'config', {})
        config_dict[key] = value
        setattr(self, 'config', config_dict)

    def update_config(self, updates: Dict[str, Any]) -> None:
        """Update multiple configuration values."""
        config_value = getattr(self, 'config', None)
        if config_value is None:
            setattr(self, 'config', {})
        config_dict = getattr(self, 'config', {})
        config_dict.update(updates)
        setattr(self, 'config', config_dict)


class ValidationMixin:
    """Mixin for model validation."""
    
    @classmethod
    def validate_data(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate input data before creating/updating model."""
        # Subclasses should override this method
        return data

    def validate_instance(self) -> List[str]:
        """Validate model instance and return list of errors."""
        # Subclasses should override this method
        return []


# Database utility functions
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def get_test_async_session() -> AsyncGenerator[AsyncSession, None]:
    """Get async test database session."""
    async with TestAsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def create_tables():
    """Create all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_tables():
    """Drop all tables in the database."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


async def create_test_tables():
    """Create all tables in the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def drop_test_tables():
    """Drop all tables in the test database."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


# Alembic configuration helper
def get_alembic_config():
    """Get Alembic configuration for migrations."""
    from alembic.config import Config
    
    # Path to alembic.ini file
    alembic_cfg = Config(str(Path(__file__).parent.parent.parent.parent / "engine-infra" / "config" / "alembic.ini"))
    
    # Set script location
    alembic_cfg.set_main_option(
        "script_location", 
        str(Path(__file__).parent.parent.parent.parent / "engine-infra" / "alembic")
    )
    
    # Set database URL
    alembic_cfg.set_main_option("sqlalchemy.url", DATABASE_URL.replace("+asyncpg", ""))
    
    return alembic_cfg


# Event listeners for automatic timestamp updates
@event.listens_for(BaseModel, "before_update", propagate=True)
def receive_before_update(mapper, connection, target):
    """Automatically update updated_at timestamp."""
    target.updated_at = datetime.utcnow()


# Health check function
async def check_database_health() -> Dict[str, Any]:
    """Check database connection health."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            await session.commit()
            
        return {
            "status": "healthy",
            "database": "connected",
            "engine": str(engine.url),
            "pool_size": getattr(engine.pool, 'size', lambda: 0)(),
            "checked_in": getattr(engine.pool, 'checkedin', lambda: 0)(),
            "checked_out": getattr(engine.pool, 'checkedout', lambda: 0)(),
        }
    except Exception as e:
        return {
            "status": "unhealthy", 
            "error": str(e),
            "database": "disconnected"
        }


# Export commonly used items
__all__ = [
    "Base",
    "BaseModel", 
    "StringIdentifierMixin",
    "TimestampMixin",
    "ConfigurationMixin", 
    "ValidationMixin",
    "JSONType",
    "AsyncSessionLocal",
    "TestAsyncSessionLocal",
    "get_async_session",
    "get_test_async_session", 
    "create_tables",
    "drop_tables",
    "create_test_tables",
    "drop_test_tables",
    "get_alembic_config",
    "check_database_health",
    "engine",
    "test_engine",
    "DATABASE_URL",
    "TEST_DATABASE_URL"
]
