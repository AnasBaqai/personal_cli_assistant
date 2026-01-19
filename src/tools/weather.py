"""Weather tool using OpenWeatherMap API."""

from typing import Any

import httpx

from ..utils.config import config
from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import WEATHER_SCHEMA


class WeatherTool(Tool):
    """Tool for fetching weather information."""

    name = "weather"
    description = "Get current weather information for a city. Returns temperature, conditions, humidity, and wind speed."

    BASE_URL = "https://api.openweathermap.org/data/2.5/weather"

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=WEATHER_SCHEMA,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        city = kwargs.get("city", "")
        units = kwargs.get("units", "metric")

        if not city:
            return ToolResult(success=False, error="No city specified")

        api_key = config.openweathermap_api_key
        if not api_key:
            return ToolResult(
                success=False,
                error="Weather API key not configured. Set OPENWEATHERMAP_API_KEY in .env file.",
            )

        try:
            async with httpx.AsyncClient(timeout=config.request_timeout) as client:
                response = await client.get(
                    self.BASE_URL,
                    params={
                        "q": city,
                        "appid": api_key,
                        "units": units,
                    },
                )

                if response.status_code == 401:
                    return ToolResult(success=False, error="Invalid API key")
                if response.status_code == 404:
                    return ToolResult(success=False, error=f"City not found: {city}")

                response.raise_for_status()
                data = response.json()

            return ToolResult(success=True, data=self._format_weather(data, units))

        except httpx.TimeoutException:
            return ToolResult(success=False, error="Weather API request timed out")
        except httpx.HTTPStatusError as e:
            return ToolResult(success=False, error=f"Weather API error: {e.response.status_code}")
        except Exception as e:
            return ToolResult(success=False, error=f"Failed to fetch weather: {e}")

    def _format_weather(self, data: dict, units: str) -> str:
        """Format weather data into a readable string."""
        temp_unit = "°C" if units == "metric" else "°F"
        speed_unit = "m/s" if units == "metric" else "mph"

        main = data.get("main", {})
        weather = data.get("weather", [{}])[0]
        wind = data.get("wind", {})
        sys = data.get("sys", {})

        lines = [
            f"Weather for {data.get('name', 'Unknown')}, {sys.get('country', '')}:",
            f"  Conditions: {weather.get('main', 'Unknown')} - {weather.get('description', '')}",
            f"  Temperature: {main.get('temp', 'N/A')}{temp_unit}",
            f"  Feels like: {main.get('feels_like', 'N/A')}{temp_unit}",
            f"  Humidity: {main.get('humidity', 'N/A')}%",
            f"  Wind: {wind.get('speed', 'N/A')} {speed_unit}",
        ]

        return "\n".join(lines)


# Register the tool
tool_registry.register(WeatherTool())
