"""JSON schemas for all tools."""

from typing import Any

# Calculator tool schema
CALCULATOR_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "expression": {
            "type": "string",
            "description": "Mathematical expression to evaluate (e.g., '2 + 2', 'sqrt(16)', '10 * 5 / 2')",
        },
    },
    "required": ["expression"],
}

# File operations tool schema
FILE_OPS_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "operation": {
            "type": "string",
            "enum": ["list", "read", "info", "create_dir"],
            "description": "The file operation to perform",
        },
        "path": {
            "type": "string",
            "description": "File or directory path (relative or absolute)",
        },
    },
    "required": ["operation", "path"],
}

# Weather tool schema
WEATHER_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "city": {
            "type": "string",
            "description": "City name to get weather for (e.g., 'New York', 'London')",
        },
        "units": {
            "type": "string",
            "enum": ["metric", "imperial"],
            "default": "metric",
            "description": "Temperature units: metric (Celsius) or imperial (Fahrenheit)",
        },
    },
    "required": ["city"],
}

# Web search tool schema
WEB_SEARCH_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "query": {
            "type": "string",
            "description": "Search query string",
        },
        "max_results": {
            "type": "integer",
            "default": 5,
            "minimum": 1,
            "maximum": 10,
            "description": "Maximum number of results to return",
        },
    },
    "required": ["query"],
}

# System info tool schema
SYSTEM_INFO_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "info_type": {
            "type": "string",
            "enum": ["all", "cpu", "memory", "disk", "datetime", "platform"],
            "default": "all",
            "description": "Type of system information to retrieve",
        },
    },
    "required": [],
}


def get_all_tool_schemas() -> dict[str, dict[str, Any]]:
    """Return all tool schemas as a dictionary."""
    return {
        "calculator": CALCULATOR_SCHEMA,
        "file_ops": FILE_OPS_SCHEMA,
        "weather": WEATHER_SCHEMA,
        "web_search": WEB_SEARCH_SCHEMA,
        "system_info": SYSTEM_INFO_SCHEMA,
    }
