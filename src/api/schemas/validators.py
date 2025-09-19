# Custom Validators for API Schemas
# This module contains custom validation functions used in Pydantic schemas

import re
from typing import List, Dict, Any, Tuple, Union
from urllib.parse import urlparse
from pydantic import ValidationError


def validate_agent_model(model: str) -> bool:
    """Validate agent model format."""
    if not model or not isinstance(model, str):
        raise ValidationError("Model must be a non-empty string")

    # Valid model patterns
    valid_patterns = [
        r"^claude-3\..*$",  # Claude models
        r"^gpt-4.*$",      # GPT-4 models
        r"^gpt-3\.5.*$",   # GPT-3.5 models
        r"^llama-.*$",     # Llama models
        r"^mistral-.*$",   # Mistral models
    ]

    if not any(re.match(pattern, model, re.IGNORECASE) for pattern in valid_patterns):
        raise ValidationError(f"Invalid model format: {model}")

    return True


def validate_workflow_dag(vertices: List[str], edges: List[Tuple[str, str]]) -> bool:
    """Validate workflow DAG structure (no cycles)."""
    if not vertices:
        raise ValidationError("Workflow must have at least one vertex")

    # Build adjacency list
    adj_list = {v: [] for v in vertices}
    for source, target in edges:
        if source not in adj_list or target not in adj_list:
            raise ValidationError(f"Edge references unknown vertex: {source} -> {target}")
        adj_list[source].append(target)

    # Detect cycles using DFS
    visited = set()
    rec_stack = set()

    def has_cycle(vertex: str) -> bool:
        visited.add(vertex)
        rec_stack.add(vertex)

        for neighbor in adj_list[vertex]:
            if neighbor not in visited:
                if has_cycle(neighbor):
                    return True
            elif neighbor in rec_stack:
                return True

        rec_stack.remove(vertex)
        return False

    for vertex in vertices:
        if vertex not in visited:
            if has_cycle(vertex):
                raise ValidationError("Workflow contains cycles")

    return True


def validate_tool_configuration(tool_type: str, config: Dict[str, Any]) -> bool:
    """Validate tool configuration based on tool type."""
    if tool_type == "api":
        required_fields = ["base_url"]
        if not all(field in config for field in required_fields):
            raise ValidationError("API tools require base_url configuration")

        # Validate URL format
        validate_url_format(config["base_url"])

    elif tool_type == "cli":
        required_fields = ["executable_path"]
        if not all(field in config for field in required_fields):
            raise ValidationError("CLI tools require executable_path configuration")

    elif tool_type == "mcp":
        required_fields = ["server_url"]
        if not all(field in config for field in required_fields):
            raise ValidationError("MCP tools require server_url configuration")

        # Validate URL format
        validate_url_format(config["server_url"])

    return True


def validate_protocol_commands(commands: List[Dict[str, Any]]) -> bool:
    """Validate protocol commands structure."""
    if not commands:
        raise ValidationError("Protocol must have at least one command")

    command_names = set()
    execution_orders = set()

    for cmd in commands:
        # Check required fields
        if "command_name" not in cmd:
            raise ValidationError("Command must have command_name")
        if "execution_order" not in cmd:
            raise ValidationError("Command must have execution_order")

        # Check for duplicates
        cmd_name = cmd["command_name"]
        exec_order = cmd["execution_order"]

        if cmd_name in command_names:
            raise ValidationError(f"Duplicate command name: {cmd_name}")
        if exec_order in execution_orders:
            raise ValidationError(f"Duplicate execution order: {exec_order}")

        command_names.add(cmd_name)
        execution_orders.add(exec_order)

        # Validate command name format
        if not re.match(r"^[a-z][a-z0-9_]*$", cmd_name):
            raise ValidationError(f"Invalid command name format: {cmd_name}")

    return True


def validate_book_hierarchy(hierarchy: Dict[str, Any]) -> bool:
    """Validate book hierarchy structure."""
    if "chapters" not in hierarchy:
        raise ValidationError("Book hierarchy must have chapters")

    chapters = hierarchy["chapters"]
    pages = hierarchy.get("pages", {})

    # Check for orphaned pages
    for chapter_id, page_list in pages.items():
        if chapter_id not in chapters:
            raise ValidationError(f"Orphaned page chapter: {chapter_id}")

    return True


def validate_url_format(url: str) -> bool:
    """Validate URL format."""
    if not url or not isinstance(url, str):
        raise ValidationError("URL must be a non-empty string")

    try:
        parsed = urlparse(url)
        if not parsed.scheme or not parsed.netloc:
            raise ValidationError(f"Invalid URL format: {url}")
    except Exception:
        raise ValidationError(f"Invalid URL format: {url}")

    # Valid schemes
    valid_schemes = ["http", "https", "tcp", "udp", "ftp", "ftps"]
    if parsed.scheme not in valid_schemes:
        raise ValidationError(f"Unsupported URL scheme: {parsed.scheme}")

    return True


def validate_version_format(version: str) -> bool:
    """Validate semantic version format."""
    if not version or not isinstance(version, str):
        raise ValidationError("Version must be a non-empty string")

    # Semantic version pattern (with optional pre-release)
    pattern = r"^(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)(?:-((?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*)(?:\.(?:0|[1-9]\d*|\d*[a-zA-Z-][0-9a-zA-Z-]*))*))?(?:\+([0-9a-zA-Z-]+(?:\.[0-9a-zA-Z-]+)*))?$"

    if not re.match(pattern, version):
        raise ValidationError(f"Invalid version format: {version}")

    return True


def validate_email_format(email: str) -> bool:
    """Validate email format."""
    if not email or not isinstance(email, str):
        raise ValidationError("Email must be a non-empty string")

    pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(pattern, email):
        raise ValidationError(f"Invalid email format: {email}")

    return True


def validate_uuid_format(uuid_str: str) -> bool:
    """Validate UUID format."""
    if not uuid_str or not isinstance(uuid_str, str):
        raise ValidationError("UUID must be a non-empty string")

    pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
    if not re.match(pattern, uuid_str, re.IGNORECASE):
        raise ValidationError(f"Invalid UUID format: {uuid_str}")

    return True


def validate_json_schema(schema: Dict[str, Any]) -> bool:
    """Validate JSON schema structure."""
    if not isinstance(schema, dict):
        raise ValidationError("Schema must be a dictionary")

    if "type" not in schema:
        raise ValidationError("Schema must have a type field")

    return True


def validate_cron_expression(cron: str) -> bool:
    """Validate cron expression format."""
    if not cron or not isinstance(cron, str):
        raise ValidationError("Cron expression must be a non-empty string")

    # Basic cron pattern validation (simplified)
    parts = cron.split()
    if len(parts) != 5:
        raise ValidationError("Cron expression must have 5 parts")

    return True


def validate_file_path(path: str) -> bool:
    """Validate file path format."""
    if not path or not isinstance(path, str):
        raise ValidationError("File path must be a non-empty string")

    # Check for dangerous characters
    dangerous_chars = ["..", "<", ">", "|", "&", ";"]
    if any(char in path for char in dangerous_chars):
        raise ValidationError(f"File path contains dangerous characters: {path}")

    return True