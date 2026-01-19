"""Web search tool using DuckDuckGo."""

from typing import Any

from duckduckgo_search import DDGS

from .base import Tool, ToolResult, ToolSchema, tool_registry
from .schemas import WEB_SEARCH_SCHEMA


class WebSearchTool(Tool):
    """Tool for performing web searches."""

    name = "web_search"
    description = "Search the web using DuckDuckGo. Returns relevant search results with titles, URLs, and snippets."

    def get_schema(self) -> ToolSchema:
        return ToolSchema(
            name=self.name,
            description=self.description,
            parameters=WEB_SEARCH_SCHEMA,
        )

    async def execute(self, **kwargs: Any) -> ToolResult:
        query = kwargs.get("query", "")
        max_results = kwargs.get("max_results", 5)

        if not query:
            return ToolResult(success=False, error="No search query provided")

        try:
            # DuckDuckGo search is synchronous, but we wrap it for consistency
            results = self._search(query, max_results)

            if not results:
                return ToolResult(
                    success=True,
                    data=f"No results found for: {query}",
                )

            return ToolResult(success=True, data=self._format_results(query, results))

        except Exception as e:
            return ToolResult(success=False, error=f"Search failed: {e}")

    def _search(self, query: str, max_results: int) -> list[dict]:
        """Perform the actual search with retries."""
        import time

        for attempt in range(3):
            try:
                with DDGS() as ddgs:
                    results = list(ddgs.text(query, max_results=max_results))
                if results:
                    return results
                time.sleep(0.5)  # Brief delay before retry
            except Exception as e:
                if attempt == 2:
                    raise
                time.sleep(1)
        return []

    def _format_results(self, query: str, results: list[dict]) -> str:
        """Format search results into a readable string."""
        lines = [f"Search results for: {query}\n"]

        for i, result in enumerate(results, 1):
            title = result.get("title", "No title")
            url = result.get("href", result.get("link", "No URL"))
            snippet = result.get("body", result.get("snippet", "No description"))

            lines.extend([
                f"{i}. {title}",
                f"   URL: {url}",
                f"   {snippet}",
                "",
            ])

        return "\n".join(lines)


# Register the tool
tool_registry.register(WebSearchTool())
