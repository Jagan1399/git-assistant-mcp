"""
LLM integration for Git Assistant MCP.

This package provides integration with various Large Language Model providers
for natural language processing of Git operations.
"""

from .providers.gemini_provider import GeminiProvider

__all__ = [
    "GeminiProvider",
]
