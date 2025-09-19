"""
Infrastructure models for Engine Framework.

Infrastructure models provide core system functionality:
- User management and authentication
- Session management and tracking
- Audit logging and system monitoring
- System-level configuration and health

Based on Engine Framework data model specification.
"""

from typing import Dict, Any, List, Optional, Union, TYPE_CHECKING
from sqlalchemy import (
    Column, String, Text, Boolean, Integer, Float,
    ForeignKey, Index, CheckConstraint, DateTime
)
from sqlalchemy.dialects.postgresql import JSONB, ARRAY, UUID
from sqlalchemy.orm import relationship, validates
from datetime import datetime
import re
import hashlib

from .base import BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin


class UserRole:
    """User role constants."""
    ADMIN = "admin"
    USER = "user"
    VIEWER = "viewer"
    SYSTEM = "system"


class UserStatus:
    """User status constants."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    PENDING = "pending"


class SessionStatus:
    """Session status constants."""
    ACTIVE = "active"
    EXPIRED = "expired"
    TERMINATED = "terminated"
    INVALIDATED = "invalidated"


class LogLevel:
    """Log level constants."""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class User(BaseModel, StringIdentifierMixin, ConfigurationMixin, ValidationMixin):
    """
    User entity for authentication and authorization.
    
    Users represent individuals or systems that interact with the Engine Framework.
    They have roles, permissions, and can own projects, agents, teams, etc.
    
    Key features:
    - Role-based access control
    - Profile management
    - Authentication tracking
    - Resource ownership
    - Activity monitoring
    """
    
    __tablename__ = "users"

    # Basic user information
    username = Column(
        String(100),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique username for authentication"
    )
    
    email = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="User email address"
    )
    
    full_name = Column(
        String(255),
        nullable=True,
        comment="User's full name"
    )
    
    # Authentication
    password_hash = Column(
        String(255),
        nullable=True,
        comment="Hashed password for local authentication"
    )
    
    salt = Column(
        String(100),
        nullable=True,
        comment="Salt used for password hashing"
    )
    
    # User role and status
    role = Column(
        String(50),
        nullable=False,
        default=UserRole.USER,
        index=True,
        comment="User role for authorization"
    )
    
    status = Column(
        String(50),
        nullable=False,
        default=UserStatus.PENDING,
        index=True,
        comment="User account status"
    )
    
    # Profile information
    avatar_url = Column(
        String(500),
        nullable=True,
        comment="URL to user avatar image"
    )
    
    timezone = Column(
        String(50),
        nullable=True,
        default="UTC",
        comment="User's preferred timezone"
    )
    
    language = Column(
        String(10),
        nullable=True,
        default="en",
        comment="User's preferred language"
    )
    
    # Authentication tracking
    last_login_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp of last login"
    )
    
    login_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of successful logins"
    )
    
    failed_login_attempts = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of consecutive failed login attempts"
    )
    
    last_failed_login_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp of last failed login attempt"
    )
    
    # Account verification
    email_verified = Column(
        Boolean,
        default=False,
        nullable=False,
        comment="Whether email address has been verified"
    )
    
    email_verification_token = Column(
        String(255),
        nullable=True,
        comment="Token for email verification"
    )
    
    # Password reset
    password_reset_token = Column(
        String(255),
        nullable=True,
        comment="Token for password reset"
    )
    
    password_reset_expires_at = Column(
        String(50),
        nullable=True,
        comment="Expiration timestamp for password reset token"
    )
    
    # Preferences and settings
    preferences = Column(
        JSONB,
        nullable=True,
        comment="User preferences and settings"
    )
    
    # API access
    api_key = Column(
        String(255),
        nullable=True,
        unique=True,
        comment="API key for programmatic access"
    )
    
    api_key_created_at = Column(
        String(50),
        nullable=True,
        comment="Timestamp when API key was created"
    )

    # User-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    user_metadata = Column(
        JSONB,
        nullable=True,
        comment="User-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None
    
    # === RELATIONSHIPS ===
    
    # One-to-many relationship with sessions
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")

    def __init__(self, **kwargs):
        """Initialize user with validation."""
        # Set defaults
        if 'role' not in kwargs:
            kwargs['role'] = UserRole.USER
        if 'status' not in kwargs:
            kwargs['status'] = UserStatus.PENDING
        if 'timezone' not in kwargs:
            kwargs['timezone'] = 'UTC'
        if 'language' not in kwargs:
            kwargs['language'] = 'en'
        if 'login_count' not in kwargs:
            kwargs['login_count'] = 0
        if 'failed_login_attempts' not in kwargs:
            kwargs['failed_login_attempts'] = 0
        if 'email_verified' not in kwargs:
            kwargs['email_verified'] = False
            
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<User(id='{self.id}', username='{self.username}', role='{self.role}')>"

    # === VALIDATION METHODS ===

    @validates('username')
    def validate_username(self, key: str, value: str) -> str:
        """Validate username format."""
        if not value or not value.strip():
            raise ValueError("Username is required")
        
        # Must be alphanumeric with underscores/hyphens, 3-100 characters
        if not re.match(r'^[a-zA-Z0-9_-]{3,100}$', value):
            raise ValueError(
                "Username must be 3-100 characters, containing only "
                "letters, numbers, underscores, and hyphens"
            )
        
        return value.lower()

    @validates('email')
    def validate_email(self, key: str, value: str) -> str:
        """Validate email format."""
        if not value or not value.strip():
            raise ValueError("Email is required")
        
        # Basic email validation
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, value):
            raise ValueError("Invalid email format")
        
        return value.lower()

    @validates('role')
    def validate_role(self, key: str, value: str) -> str:
        """Validate user role."""
        valid_roles = [UserRole.ADMIN, UserRole.USER, UserRole.VIEWER, UserRole.SYSTEM]
        
        if value not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        
        return value

    @validates('status')
    def validate_status(self, key: str, value: str) -> str:
        """Validate user status."""
        valid_statuses = [UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED, UserStatus.PENDING]
        
        if value not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")
        
        return value

    # === PASSWORD MANAGEMENT ===

    def set_password(self, password: str) -> None:
        """Set user password with hashing."""
        if not password or len(password) < 8:
            raise ValueError("Password must be at least 8 characters long")
        
        # Generate salt
        import secrets
        self.salt = secrets.token_hex(32)
        
        # Hash password with salt
        self.password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            self.salt.encode('utf-8'),
            100000
        ).hex()

    def verify_password(self, password: str) -> bool:
        """Verify password against hash."""
        password_hash_value = getattr(self, 'password_hash', None)
        salt_value = getattr(self, 'salt', None)
        if not password_hash_value or not salt_value:
            return False
        
        # Hash provided password with stored salt
        password_hash = hashlib.pbkdf2_hmac(
            'sha256',
            password.encode('utf-8'),
            salt_value.encode('utf-8'),
            100000
        ).hex()
        
        return password_hash == password_hash_value

    # === AUTHENTICATION TRACKING ===

    def record_successful_login(self) -> None:
        """Record successful login attempt."""
        self.last_login_at = datetime.utcnow().isoformat()
        self.login_count += 1
        self.failed_login_attempts = 0  # Reset failed attempts

    def record_failed_login(self) -> None:
        """Record failed login attempt."""
        self.failed_login_attempts += 1
        self.last_failed_login_at = datetime.utcnow().isoformat()

    def is_locked_out(self, max_attempts: int = 5) -> bool:
        """Check if user is locked out due to failed login attempts."""
        failed_attempts = getattr(self, 'failed_login_attempts', 0)
        return failed_attempts >= max_attempts

    # === API KEY MANAGEMENT ===

    def generate_api_key(self) -> str:
        """Generate new API key for user."""
        import secrets
        self.api_key = f"ek_{secrets.token_urlsafe(32)}"
        self.api_key_created_at = datetime.utcnow().isoformat()
        return self.api_key

    def revoke_api_key(self) -> None:
        """Revoke current API key."""
        self.api_key = None
        self.api_key_created_at = None

    # === USER PROFILE ===

    def get_profile(self) -> Dict[str, Any]:
        """Get user profile information."""
        created_at_value = getattr(self, 'created_at', None)
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'full_name': self.full_name,
            'role': self.role,
            'status': self.status,
            'avatar_url': self.avatar_url,
            'timezone': self.timezone,
            'language': self.language,
            'email_verified': self.email_verified,
            'last_login_at': self.last_login_at,
            'login_count': getattr(self, 'login_count', 0),
            'has_api_key': self.api_key is not None,
            'preferences': self.preferences,
            'created_at': created_at_value.isoformat() if created_at_value else None
        }


class Session(BaseModel, ValidationMixin):
    """
    User session for authentication and activity tracking.
    
    Sessions represent active user connections and provide:
    - Authentication state management
    - Activity tracking
    - Security monitoring
    - Resource usage tracking
    """
    
    __tablename__ = "sessions"

    # Session identification
    session_token = Column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
        comment="Unique session token"
    )
    
    # User association
    user_id = Column(
        String(255),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="User this session belongs to"
    )
    
    # Session metadata
    status = Column(
        String(50),
        nullable=False,
        default=SessionStatus.ACTIVE,
        index=True,
        comment="Session status"
    )
    
    # Session timing
    started_at = Column(
        String(50),
        nullable=False,
        comment="Session start timestamp"
    )
    
    expires_at = Column(
        String(50),
        nullable=False,
        comment="Session expiration timestamp"
    )
    
    last_activity_at = Column(
        String(50),
        nullable=True,
        comment="Last activity timestamp"
    )
    
    ended_at = Column(
        String(50),
        nullable=True,
        comment="Session end timestamp"
    )
    
    # Client information
    ip_address = Column(
        String(45),
        nullable=True,
        comment="Client IP address (IPv4/IPv6)"
    )
    
    user_agent = Column(
        String(1000),
        nullable=True,
        comment="Client user agent string"
    )
    
    device_fingerprint = Column(
        String(255),
        nullable=True,
        comment="Device fingerprint for security"
    )
    
    # Activity tracking
    request_count = Column(
        Integer,
        default=0,
        nullable=False,
        comment="Number of requests in this session"
    )
    
    # Session data
    session_data = Column(
        JSONB,
        nullable=True,
        comment="Session-specific data and state"
    )

    # Session-specific metadata (avoiding conflict with SQLAlchemy's reserved 'metadata' attribute)
    session_metadata = Column(
        JSONB,
        nullable=True,
        comment="Session-specific metadata and configuration"
    )

    # Override the inherited metadata attribute to avoid SQLAlchemy conflict
    metadata = None
    
    # === RELATIONSHIPS ===
    
    user = relationship("User", back_populates="sessions")

    def __init__(self, **kwargs):
        """Initialize session with validation."""
        # Set defaults
        if 'status' not in kwargs:
            kwargs['status'] = SessionStatus.ACTIVE
        if 'request_count' not in kwargs:
            kwargs['request_count'] = 0
        if 'started_at' not in kwargs:
            kwargs['started_at'] = datetime.utcnow().isoformat()
            
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Session(id='{self.id}', user_id='{self.user_id}', status='{self.status}')>"

    # === SESSION MANAGEMENT ===

    def is_active(self) -> bool:
        """Check if session is active and not expired."""
        status_value = getattr(self, 'status', SessionStatus.ACTIVE)
        if status_value != SessionStatus.ACTIVE:
            return False
        
        # Check expiration
        expires_at_value = getattr(self, 'expires_at', None)
        if expires_at_value:
            try:
                expires = datetime.fromisoformat(expires_at_value)
                return datetime.utcnow() < expires
            except ValueError:
                return False
        
        return True

    def extend_session(self, hours: int = 24) -> None:
        """Extend session expiration time."""
        from datetime import timedelta
        new_expiry = datetime.utcnow() + timedelta(hours=hours)
        self.expires_at = new_expiry.isoformat()

    def record_activity(self) -> None:
        """Record session activity."""
        self.last_activity_at = datetime.utcnow().isoformat()
        self.request_count += 1

    def terminate_session(self, reason: str = "user_logout") -> None:
        """Terminate session."""
        setattr(self, 'status', SessionStatus.TERMINATED)
        setattr(self, 'ended_at', datetime.utcnow().isoformat())
        
        session_data_value = getattr(self, 'session_data', None)
        if session_data_value is None:
            session_data_value = {}
        session_data_value['termination_reason'] = reason
        setattr(self, 'session_data', session_data_value)

    def invalidate_session(self) -> None:
        """Invalidate session (security reasons)."""
        self.status = SessionStatus.INVALIDATED
        self.ended_at = datetime.utcnow().isoformat()


class Log(BaseModel, ValidationMixin):
    """
    System audit log for tracking operations and events.
    
    Logs provide comprehensive audit trail for:
    - User actions and operations
    - System events and changes
    - Error tracking and debugging
    - Security monitoring
    - Performance analysis
    """
    
    __tablename__ = "logs"

    # Log identification and categorization
    level = Column(
        String(20),
        nullable=False,
        index=True,
        comment="Log level (debug, info, warning, error, critical)"
    )
    
    category = Column(
        String(100),
        nullable=False,
        index=True,
        comment="Log category (auth, system, user, api, workflow, etc.)"
    )
    
    operation = Column(
        String(100),
        nullable=False,
        comment="Specific operation or action being logged"
    )
    
    # Message and context
    message = Column(
        Text,
        nullable=False,
        comment="Log message description"
    )
    
    details = Column(
        JSONB,
        nullable=True,
        comment="Additional log details and context"
    )
    
    # Source information
    source = Column(
        String(100),
        nullable=True,
        comment="Source of the log entry (service, component, module)"
    )
    
    # User and session context
    user_id = Column(
        String(255),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="User associated with this log entry"
    )
    
    session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("sessions.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        comment="Session associated with this log entry"
    )
    
    # Request context
    request_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Request ID for correlation"
    )
    
    correlation_id = Column(
        String(255),
        nullable=True,
        index=True,
        comment="Correlation ID for distributed tracing"
    )
    
    # Resource context
    resource_type = Column(
        String(100),
        nullable=True,
        comment="Type of resource involved (project, agent, team, etc.)"
    )
    
    resource_id = Column(
        String(255),
        nullable=True,
        comment="ID of the resource involved"
    )
    
    # Client information
    ip_address = Column(
        String(45),
        nullable=True,
        comment="Client IP address"
    )
    
    user_agent = Column(
        String(1000),
        nullable=True,
        comment="Client user agent"
    )
    
    # Performance metrics
    duration_ms = Column(
        Integer,
        nullable=True,
        comment="Operation duration in milliseconds"
    )
    
    # Error information
    error_code = Column(
        String(100),
        nullable=True,
        comment="Error code if applicable"
    )
    
    stack_trace = Column(
        Text,
        nullable=True,
        comment="Stack trace for errors"
    )
    
    # Tags for filtering and searching
    tags = Column(
        ARRAY(String(100)),
        nullable=True,
        comment="Tags for log organization and filtering"
    )
    
    # Log-specific metadata (avoiding SQLAlchemy reserved 'metadata' attribute)
    log_metadata = Column(
        JSONB,
        nullable=True,
        comment="Additional log metadata and context"
    )
    
    # Override SQLAlchemy reserved 'metadata' attribute
    metadata = None

    def __init__(self, **kwargs):
        """Initialize log entry with validation."""
        super().__init__(**kwargs)

    def __repr__(self) -> str:
        return f"<Log(level='{self.level}', category='{self.category}', operation='{self.operation}')>"

    # === VALIDATION METHODS ===

    @validates('level')
    def validate_level(self, key: str, value: str) -> str:
        """Validate log level."""
        valid_levels = [LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]
        
        if value not in valid_levels:
            raise ValueError(f"Log level must be one of: {', '.join(valid_levels)}")
        
        return value

    # === LOG ANALYSIS ===

    def is_error(self) -> bool:
        """Check if log entry represents an error."""
        return self.level in [LogLevel.ERROR, LogLevel.CRITICAL]

    def add_tag(self, tag: str) -> None:
        """Add tag to log entry."""
        if self.tags is None:
            self.tags = []
        
        if tag not in self.tags:
            self.tags.append(tag)

    def has_tag(self, tag: str) -> bool:
        """Check if log entry has specific tag."""
        return self.tags is not None and tag in self.tags

    @classmethod
    def create_user_action_log(
        cls,
        user_id: str,
        action: str,
        message: str,
        session_id: Optional[str] = None,
        resource_type: Optional[str] = None,
        resource_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "Log":
        """Create log entry for user action."""
        return cls(
            level=LogLevel.INFO,
            category="user_action",
            operation=action,
            message=message,
            user_id=user_id,
            session_id=session_id,
            resource_type=resource_type,
            resource_id=resource_id,
            details=details,
            tags=["user_action", action]
        )

    @classmethod
    def create_system_log(
        cls,
        level: str,
        operation: str,
        message: str,
        source: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None
    ) -> "Log":
        """Create system log entry."""
        return cls(
            level=level,
            category="system",
            operation=operation,
            message=message,
            source=source,
            details=details,
            error_code=error_code,
            tags=["system", operation]
        )

    @classmethod
    def create_error_log(
        cls,
        operation: str,
        message: str,
        error_code: Optional[str] = None,
        stack_trace: Optional[str] = None,
        user_id: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None
    ) -> "Log":
        """Create error log entry."""
        return cls(
            level=LogLevel.ERROR,
            category="error",
            operation=operation,
            message=message,
            error_code=error_code,
            stack_trace=stack_trace,
            user_id=user_id,
            details=details,
            tags=["error", operation]
        )


# Database indexes for performance
Index('idx_user_username', User.username)
Index('idx_user_email', User.email)
Index('idx_user_role_status', User.role, User.status)
Index('idx_user_last_login', User.last_login_at)

Index('idx_session_token', Session.session_token)
Index('idx_session_user_status', Session.user_id, Session.status)
Index('idx_session_expires', Session.expires_at)
Index('idx_session_activity', Session.last_activity_at)

Index('idx_log_level_category', Log.level, Log.category)
Index('idx_log_operation', Log.operation)
Index('idx_log_user_time', Log.user_id, Log.created_at)
Index('idx_log_request_id', Log.request_id)
Index('idx_log_correlation_id', Log.correlation_id)
Index('idx_log_resource', Log.resource_type, Log.resource_id)
Index('idx_log_created_at', Log.created_at.desc())

# Database constraints
CheckConstraint(
    User.role.in_([UserRole.ADMIN, UserRole.USER, UserRole.VIEWER, UserRole.SYSTEM]),
    name='ck_user_role_valid'
)

CheckConstraint(
    User.status.in_([UserStatus.ACTIVE, UserStatus.INACTIVE, UserStatus.SUSPENDED, UserStatus.PENDING]),
    name='ck_user_status_valid'
)

CheckConstraint(
    User.login_count >= 0,
    name='ck_user_login_count_non_negative'
)

CheckConstraint(
    User.failed_login_attempts >= 0,
    name='ck_user_failed_login_attempts_non_negative'
)

CheckConstraint(
    Session.status.in_([SessionStatus.ACTIVE, SessionStatus.EXPIRED, SessionStatus.TERMINATED, SessionStatus.INVALIDATED]),
    name='ck_session_status_valid'
)

CheckConstraint(
    Session.request_count >= 0,
    name='ck_session_request_count_non_negative'
)

CheckConstraint(
    Log.level.in_([LogLevel.DEBUG, LogLevel.INFO, LogLevel.WARNING, LogLevel.ERROR, LogLevel.CRITICAL]),
    name='ck_log_level_valid'
)

CheckConstraint(
    Log.duration_ms >= 0,
    name='ck_log_duration_non_negative'
)
