"""
Git Assistant MCP - AI-powered Git operations through natural language.

A Model Context Protocol (MCP) implementation that transforms how developers
interact with Git by providing intelligent command generation through LLM integration.
"""

__version__ = "0.1.0"
__author__ = "Git Assistant MCP Team"
__description__ = "AI-powered Git assistant with natural language processing"

# Main imports
from .config.settings import get_settings, Settings
from .models.llm_response import LLMResponse, LLMRequest, LLMError

__all__ = [
    "__version__",
    "__author__",
    "__description__",
    "get_settings",
    "Settings",
    "LLMResponse",
    "LLMRequest",
    "LLMError",
]
