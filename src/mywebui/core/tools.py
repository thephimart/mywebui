"""Tool system for executing user-requested actions."""

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

from mywebui.config import get_config


@dataclass
class ToolResult:
    """Result of a tool execution."""
    success: bool
    output: str
    logs: dict[str, Any]
    error: str | None = None


class BaseTool(ABC):
    """Base class for all tools."""

    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description

    @abstractmethod
    async def execute(self, **kwargs) -> ToolResult:
        """Execute the tool with given arguments."""
        pass

    def validate_args(self, **kwargs) -> bool:
        """Validate tool arguments."""
        return True


class FilesystemTool(BaseTool):
    """Tool for reading files from allowed directories."""

    def __init__(self):
        super().__init__("filesystem", "Read files from allowed directories")

    def validate_args(self, **kwargs) -> bool:
        return "path" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        config = get_config()
        allowed_paths = config.tools.filesystem.get("allowed_paths", [])
        
        if not allowed_paths:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="No allowed paths configured",
            )
        
        file_path = Path(kwargs["path"]).resolve()
        
        is_allowed = False
        for allowed in allowed_paths:
            allowed_path = Path(allowed).resolve()
            try:
                file_path.relative_to(allowed_path)
                is_allowed = True
                break
            except ValueError:
                continue
        
        if not is_allowed:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=f"Path not in allowed directories: {kwargs['path']}",
            )
        
        operation = kwargs.get("operation", "read")
        
        try:
            if operation == "read":
                if file_path.is_file():
                    content = file_path.read_text()
                    return ToolResult(
                        success=True,
                        output=content,
                        logs={"path": str(file_path), "operation": "read"},
                    )
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        logs={},
                        error=f"Not a file: {kwargs['path']}",
                    )
            
            elif operation == "list":
                if file_path.is_dir():
                    items = list(file_path.iterdir())
                    return ToolResult(
                        success=True,
                        output="\n".join([i.name for i in items]),
                        logs={"path": str(file_path), "operation": "list", "count": len(items)},
                    )
                else:
                    return ToolResult(
                        success=False,
                        output="",
                        logs={},
                        error=f"Not a directory: {kwargs['path']}",
                    )
            
            elif operation == "glob":
                pattern = kwargs.get("pattern", "*")
                items = list(file_path.glob(pattern))
                return ToolResult(
                    success=True,
                    output="\n".join([str(i) for i in items]),
                    logs={"path": str(file_path), "pattern": pattern, "count": len(items)},
                )
            
            else:
                return ToolResult(
                    success=False,
                    output="",
                    logs={},
                    error=f"Unknown operation: {operation}",
                )
        
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


class WebSearchTool(BaseTool):
    """Tool for web search."""

    def __init__(self):
        super().__init__("web_search", "Search the web using DuckDuckGo")

    def validate_args(self, **kwargs) -> bool:
        return "query" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        config = get_config()

        if not config.tools.web.get("enabled", False):
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Web search is disabled",
            )

        try:
            from ddgs import DDGS
            query = kwargs["query"]

            ddgs = DDGS()
            results = ddgs.text(query, max_results=5)

            output = "\n\n".join([
                f"{r.get('title', '')}: {r.get('href', '')}"
                for r in results
            ])

            return ToolResult(
                success=True,
                output=output,
                logs={"query": query, "count": len(results)},
            )

        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


class WebFetchTool(BaseTool):
    """Tool for fetching a single URL and extracting content."""

    MAX_SIZE_BYTES = 10 * 1024 * 1024  # 10MB
    TIMEOUT_SECONDS = 30

    def __init__(self):
        super().__init__("web_fetch", "Fetch a URL and extract clean text content")

    def validate_args(self, **kwargs) -> bool:
        return "url" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        config = get_config()

        if not config.tools.web.get("enabled", False):
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Web fetch is disabled",
            )

        url = kwargs["url"]

        try:
            import httpx
            from bs4 import BeautifulSoup

            async with httpx.AsyncClient(
                timeout=httpx.Timeout(self.TIMEOUT_SECONDS),
                follow_redirects=True,
            ) as client:
                response = await client.get(url)

                if response.status_code != 200:
                    return ToolResult(
                        success=False,
                        output="",
                        logs={},
                        error=f"HTTP {response.status_code}",
                    )

                content_type = response.headers.get("content-type", "")
                if "text/html" not in content_type and "text/plain" not in content_type:
                    return ToolResult(
                        success=False,
                        output="",
                        logs={},
                        error=f"Unsupported content type: {content_type}",
                    )

                content = response.text
                if len(content) > self.MAX_SIZE_BYTES:
                    content = content[:self.MAX_SIZE_BYTES]

                soup = BeautifulSoup(content, "html.parser")

                title = soup.title.string if soup.title else ""

                for tag in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    tag.decompose()

                main_content = soup.get_text(separator="\n", strip=True)

                lines = [line for line in main_content.split("\n") if line.strip()]
                clean_text = "\n".join(lines[:500])

                return ToolResult(
                    success=True,
                    output=clean_text,
                    logs={
                        "url": url,
                        "title": title,
                        "size_bytes": len(content),
                    },
                )

        except httpx.TimeoutException:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Request timed out",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


class WebCrawlTool(BaseTool):
    """Tool for crawling multiple pages with depth limits."""

    DEFAULT_MAX_PAGES = 10
    DEFAULT_DEPTH = 2

    def __init__(self):
        super().__init__(
            "web_crawl",
            "Crawl a website following links with depth limits",
        )

    def validate_args(self, **kwargs) -> bool:
        return "url" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        config = get_config()

        if not config.tools.web.get("enabled", False):
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Web crawl is disabled",
            )

        url = kwargs["url"]
        max_pages = kwargs.get("max_pages", self.DEFAULT_MAX_PAGES)
        depth = kwargs.get("depth", self.DEFAULT_DEPTH)

        max_pages = min(max_pages, 50)
        depth = min(depth, 5)

        try:
            from crawl4ai import AsyncWebCrawler

            async with AsyncWebCrawler() as crawler:
                results = await crawler.arun(
                    url=url,
                    max_depth=depth,
                    max_pages=max_pages,
                    verbose=False,
                )

                output_parts = []
                for i, result in enumerate(results[:10]):
                    title = result.meta.get("title", f"Page {i+1}")
                    output_parts.append(f"## {title}\n{result.markdown[:2000]}")

                return ToolResult(
                    success=True,
                    output="\n\n---\n\n".join(output_parts),
                    logs={"url": url, "pages_crawled": len(results)},
                )

        except ImportError:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="crawl4ai not installed",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


class WebInteractTool(BaseTool):
    """Tool for interacting with JS-heavy sites (gated, requires playwright)."""

    def __init__(self):
        super().__init__(
            "web_interact",
            "Interact with JavaScript-heavy sites (requires playwright)",
        )

    def validate_args(self, **kwargs) -> bool:
        return "url" in kwargs and "instruction" in kwargs

    async def execute(self, **kwargs) -> ToolResult:
        config = get_config()

        if not config.tools.web.get("interact_enabled", False):
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Web interact is not enabled (requires admin to enable)",
            )

        url = kwargs["url"]
        instruction = kwargs["instruction"]

        try:
            from playwright.async_api import async_playwright

            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.goto(url, wait_until="networkidle")

                if instruction:
                    if instruction == "scroll":
                        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                    elif instruction == "click_agree":
                        await page.click("button:has-text('agree'), button:has-text('accept'), button:has-text('OK')", timeout=2000)

                content = await page.content()
                await browser.close()

                return ToolResult(
                    success=True,
                    output=content[:50000],
                    logs={"url": url, "instruction": instruction},
                )

        except ImportError:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="playwright not installed (pip install playwright)",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


class ToolRegistry:
    """Registry for all available tools."""

    def __init__(self):
        self._tools: dict[str, BaseTool] = {}
        self._register_default_tools()

    def _register_default_tools(self):
        """Register default tools."""
        self.register(FilesystemTool())
        self.register(WebSearchTool())
        self.register(WebFetchTool())
        self.register(WebCrawlTool())

    def register(self, tool: BaseTool):
        """Register a tool."""
        self._tools[tool.name] = tool

    def get(self, name: str) -> BaseTool | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[dict[str, str]]:
        """List all available tools."""
        return [
            {"name": tool.name, "description": tool.description}
            for tool in self._tools.values()
        ]

    async def execute(self, tool_name: str, **kwargs) -> ToolResult:
        """Execute a tool by name."""
        tool = self.get(tool_name)
        
        if tool is None:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=f"Unknown tool: {tool_name}",
            )
        
        if not tool.validate_args(**kwargs):
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=f"Invalid arguments for tool: {tool_name}",
            )
        
        try:
            return await asyncio.wait_for(
                tool.execute(**kwargs),
                timeout=30.0,
            )
        except asyncio.TimeoutError:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error="Tool execution timed out",
            )
        except Exception as e:
            return ToolResult(
                success=False,
                output="",
                logs={},
                error=str(e),
            )


_tool_registry: ToolRegistry | None = None


def get_tool_registry() -> ToolRegistry:
    """Get the global tool registry."""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry
