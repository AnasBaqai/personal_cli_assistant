"""File operations tool for the CLI assistant."""

import os
from datetime import datetime
from pathlib import Path
from typing import Any

import aiofiles
import aiofiles.os

from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import FILE_OPS_SCHEMA


class FileOpsTool(Tool):
    """Tool for performing file system operations."""

    name = "file_ops"
    description = "Perform file system operations: list directory contents, read file contents, get file info, or create directories."

    # Safety: limit readable file size to prevent memory issues
    MAX_READ_SIZE = 100_000  # 100KB

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=FILE_OPS_SCHEMA,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        operation = kwargs.get("operation", "")
        path_str = kwargs.get("path", "")

        if not operation:
            return ToolResult(success=False, error="No operation specified")
        if not path_str:
            return ToolResult(success=False, error="No path specified")

        # Resolve path (handle ~ and relative paths)
        path = Path(path_str).expanduser().resolve()

        try:
            match operation:
                case "list":
                    return await self._list_directory(path)
                case "read":
                    return await self._read_file(path)
                case "info":
                    return await self._get_info(path)
                case "create_dir":
                    return await self._create_directory(path)
                case _:
                    return ToolResult(
                        success=False,
                        error=f"Unknown operation: {operation}. Supported: list, read, info, create_dir",
                    )
        except PermissionError:
            return ToolResult(success=False, error=f"Permission denied: {path}")
        except Exception as e:
            return ToolResult(success=False, error=f"File operation error: {e}")

    async def _list_directory(self, path: Path) -> ToolResult:
        """List contents of a directory."""
        if not path.exists():
            return ToolResult(success=False, error=f"Directory not found: {path}")
        if not path.is_dir():
            return ToolResult(success=False, error=f"Not a directory: {path}")

        entries = []
        for entry in sorted(path.iterdir()):
            entry_type = "DIR" if entry.is_dir() else "FILE"
            size = ""
            if entry.is_file():
                size = f" ({self._format_size(entry.stat().st_size)})"
            entries.append(f"  [{entry_type}] {entry.name}{size}")

        if not entries:
            return ToolResult(success=True, data=f"Directory is empty: {path}")

        result = f"Contents of {path}:\n" + "\n".join(entries)
        return ToolResult(success=True, data=result)

    async def _read_file(self, path: Path) -> ToolResult:
        """Read contents of a file."""
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {path}")
        if not path.is_file():
            return ToolResult(success=False, error=f"Not a file: {path}")

        # Check file size
        size = path.stat().st_size
        if size > self.MAX_READ_SIZE:
            return ToolResult(
                success=False,
                error=f"File too large ({self._format_size(size)}). Maximum: {self._format_size(self.MAX_READ_SIZE)}",
            )

        async with aiofiles.open(path, "r", encoding="utf-8", errors="replace") as f:
            content = await f.read()

        return ToolResult(
            success=True,
            data=f"Contents of {path.name}:\n\n{content}",
        )

    async def _get_info(self, path: Path) -> ToolResult:
        """Get information about a file or directory."""
        if not path.exists():
            return ToolResult(success=False, error=f"Path not found: {path}")

        stat = path.stat()
        is_dir = path.is_dir()

        info_lines = [
            f"Path: {path}",
            f"Type: {'Directory' if is_dir else 'File'}",
            f"Size: {self._format_size(stat.st_size)}",
            f"Created: {datetime.fromtimestamp(stat.st_ctime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Modified: {datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')}",
            f"Permissions: {oct(stat.st_mode)[-3:]}",
        ]

        if is_dir:
            try:
                count = len(list(path.iterdir()))
                info_lines.append(f"Items: {count}")
            except PermissionError:
                info_lines.append("Items: (permission denied)")

        return ToolResult(success=True, data="\n".join(info_lines))

    async def _create_directory(self, path: Path) -> ToolResult:
        """Create a directory (including parent directories)."""
        if path.exists():
            if path.is_dir():
                return ToolResult(success=True, data=f"Directory already exists: {path}")
            return ToolResult(success=False, error=f"Path exists but is not a directory: {path}")

        path.mkdir(parents=True, exist_ok=True)
        return ToolResult(success=True, data=f"Created directory: {path}")

    @staticmethod
    def _format_size(size: int) -> str:
        """Format file size in human-readable format."""
        for unit in ["B", "KB", "MB", "GB"]:
            if size < 1024:
                return f"{size:.1f} {unit}" if unit != "B" else f"{size} {unit}"
            size /= 1024
        return f"{size:.1f} TB"


# Register the tool
tool_registry.register(FileOpsTool())
