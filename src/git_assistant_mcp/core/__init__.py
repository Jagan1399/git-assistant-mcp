"""
Core components for Git Assistant MCP.

This package contains the main business logic components including
state scraping, MCP wrapper, and core utilities.
"""

from .state_scraper import StateScraper, GitCommandError
from .mcp_wrapper import GitAssistantMCP, create_git_assistant

__all__ = [
    "StateScraper",
    "GitCommandError", 
    "GitAssistantMCP",
    "create_git_assistant",
]
