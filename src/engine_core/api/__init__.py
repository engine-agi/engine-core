"""
Engine Core API Package - REST API for Engine Framework Core Components.

This package provides REST API endpoints for all Engine Framework core components,
including agents, teams, workflows, tools, protocols, and books. The API is built
with FastAPI and provides comprehensive CRUD operations with proper validation,
error handling, and OpenAPI documentation.

Key Features:
- RESTful API endpoints for all core components
- Pydantic models for request/response validation
- Async/await support for performance
- Comprehensive error handling
- OpenAPI/Swagger documentation
- Modular router architecture
- Integration with core business logic

Architecture:
- Modular routers by component (agents, teams, workflows, etc.)
- Shared schemas and validation models
- Dependency injection for services
- Consistent error responses
- WebSocket integration for real-time updates

Components:
- agents: Agent management and execution
- teams: Team coordination and collaboration
- workflows: Process orchestration
- tools: External tool integrations
- protocols: Command protocols and behavior
- books: Knowledge management and memory
"""

__version__ = "1.0.0"