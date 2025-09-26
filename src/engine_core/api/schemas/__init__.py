"""
API Schemas Package - Engine Framework REST API Schemas.

This package contains all Pydantic schemas and models for the Engine Framework API,
organized by functional domain. These schemas provide request/response validation,
serialization, and OpenAPI documentation generation.

Available Schemas:
- base_schemas: Common base models and utilities
- agent_schemas: Agent-related request/response models
- team_schemas: Team coordination models
- workflow_schemas: Process orchestration models
- protocol_schemas: Command protocol models
- tool_schemas: External tool integration models
- book_schemas: Knowledge management models
- enums: Shared enumeration types
- validators: Custom field validators

Each schema follows consistent patterns:
- Pydantic BaseModel inheritance
- Proper field validation and constraints
- Optional fields with defaults
- Nested model relationships
- OpenAPI documentation strings
"""

__version__ = "1.0.0"
