"""System information tool."""

import os
import platform
import shutil
from datetime import datetime
from typing import Any

from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import SYSTEM_INFO_SCHEMA


class SystemInfoTool(Tool):
    """Tool for retrieving system information."""

    name = "system_info"
    description = "Get system information including CPU, memory, disk space, current date/time, and platform details."

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=SYSTEM_INFO_SCHEMA,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        info_type = kwargs.get("info_type", "all")

        try:
            match info_type:
                case "all":
                    return ToolResult(success=True, data=self._get_all_info())
                case "cpu":
                    return ToolResult(success=True, data=self._get_cpu_info())
                case "memory":
                    return ToolResult(success=True, data=self._get_memory_info())
                case "disk":
                    return ToolResult(success=True, data=self._get_disk_info())
                case "datetime":
                    return ToolResult(success=True, data=self._get_datetime_info())
                case "platform":
                    return ToolResult(success=True, data=self._get_platform_info())
                case _:
                    return ToolResult(
                        success=False,
                        error=f"Unknown info type: {info_type}. Supported: all, cpu, memory, disk, datetime, platform",
                    )
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to get system info: {e}")

    def _get_all_info(self) -> str:
        """Get all system information."""
        sections = [
            self._get_platform_info(),
            self._get_datetime_info(),
            self._get_cpu_info(),
            self._get_memory_info(),
            self._get_disk_info(),
        ]
        return "\n\n".join(sections)

    def _get_cpu_info(self) -> str:
        """Get CPU information."""
        cpu_count = os.cpu_count() or "Unknown"

        # Try to get load average (Unix only)
        try:
            load = os.getloadavg()
            load_str = f"  Load average: {load[0]:.2f}, {load[1]:.2f}, {load[2]:.2f}"
        except (AttributeError, OSError):
            load_str = "  Load average: Not available on this platform"

        return f"CPU Information:\n  Cores: {cpu_count}\n{load_str}"

    def _get_memory_info(self) -> str:
        """Get memory information (basic, without psutil)."""
        # Without psutil, we can only get basic info
        lines = ["Memory Information:"]

        # Try to read from /proc/meminfo on Linux
        try:
            with open("/proc/meminfo") as f:
                meminfo = {}
                for line in f:
                    parts = line.split(":")
                    if len(parts) == 2:
                        key = parts[0].strip()
                        value = parts[1].strip()
                        meminfo[key] = value

                if "MemTotal" in meminfo:
                    lines.append(f"  Total: {meminfo['MemTotal']}")
                if "MemAvailable" in meminfo:
                    lines.append(f"  Available: {meminfo['MemAvailable']}")
                if "MemFree" in meminfo:
                    lines.append(f"  Free: {meminfo['MemFree']}")
        except FileNotFoundError:
            lines.append("  Detailed memory info not available on this platform")

        return "\n".join(lines)

    def _get_disk_info(self) -> str:
        """Get disk usage information."""
        lines = ["Disk Information:"]

        # Get disk usage for current directory's drive
        try:
            usage = shutil.disk_usage("/")
            total_gb = usage.total / (1024**3)
            used_gb = usage.used / (1024**3)
            free_gb = usage.free / (1024**3)
            percent = (usage.used / usage.total) * 100

            lines.extend([
                f"  Total: {total_gb:.1f} GB",
                f"  Used: {used_gb:.1f} GB ({percent:.1f}%)",
                f"  Free: {free_gb:.1f} GB",
            ])
        except Exception as e:
            lines.append(f"  Unable to get disk info: {e}")

        return "\n".join(lines)

    def _get_datetime_info(self) -> str:
        """Get current date and time information."""
        now = datetime.now()
        utc_now = datetime.utcnow()

        return (
            f"Date/Time Information:\n"
            f"  Local: {now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S')}\n"
            f"  Timezone: {datetime.now().astimezone().tzname()}"
        )

    def _get_platform_info(self) -> str:
        """Get platform and OS information."""
        return (
            f"Platform Information:\n"
            f"  System: {platform.system()}\n"
            f"  Release: {platform.release()}\n"
            f"  Version: {platform.version()}\n"
            f"  Machine: {platform.machine()}\n"
            f"  Processor: {platform.processor() or 'Unknown'}\n"
            f"  Python: {platform.python_version()}"
        )


# Register the tool
tool_registry.register(SystemInfoTool())
