"""
API Router Package - Engine Framework REST API Routers.

This package contains all API routers for the Engine Framework, organized by
functional domain. Each router implements RESTful endpoints for their respective
system pillars with comprehensive CRUD operations, validation, and integration.

Available Routers:
- projects: Project management and organization
- agents: AI agent creation, configuration, and execution
- teams: Team coordination and collaboration
- workflows: Process orchestration and monitoring
- protocols: Command protocols and behavior management
- tools: External tool integrations and capabilities
- books: Knowledge management and hierarchical memory
- observability: Monitoring, logging, and system metrics

Each router follows consistent patterns:
- Pydantic models for request/response validation
- Async/await for performance
- Dependency injection for services
- Error handling and status codes
- OpenAPI documentation
- Authentication and authorization
- Real-time WebSocket integration
"""

# This file makes the routers directory a Python package
# Individual routers will be created in subsequent tasks

__version__ = "1.0.0"

# Note: __all__ will be populated as routers are created
# __all__ = [
#     "projects",
#     "agents", 
#     "teams",
#     "workflows",
#     "protocols",
#     "tools",
#     "books",
#     "observability"
# ]
