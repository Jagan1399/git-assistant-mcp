"""
LLM Provider Factory for Git Assistant MCP

This module provides a factory pattern for automatically selecting and
initializing the appropriate LLM provider based on available configuration.
"""

import logging
from typing import Optional, Type
from .providers.base_provider import BaseLLMProvider
from .providers.gemini_provider import GeminiProvider
from .providers.openai_provider import OpenAIProvider
from ..config.settings import Settings

logger = logging.getLogger(__name__)


class LLMProviderFactory:
    """
    Factory for creating and managing LLM providers.
    
    Automatically detects which provider is available based on API keys
    and configuration, with fallback logic for multiple providers.
    """
    
    # Priority order for providers (first available will be used)
    PROVIDER_PRIORITY = [
        ("gemini", GeminiProvider),
        ("openai", OpenAIProvider),
    ]
    
    def __init__(self, settings: Settings):
        """
        Initialize the provider factory.
        
        Args:
            settings: Application settings containing API configuration
        """
        self.settings = settings
        self._current_provider: Optional[BaseLLMProvider] = None
        self._provider_name: Optional[str] = None
    
    def get_available_providers(self) -> list[tuple[str, Type[BaseLLMProvider]]]:
        """
        Get a list of available providers based on configuration.
        
        Returns:
            List of tuples containing (provider_name, provider_class) for available providers
        """
        available_providers = []
        
        for provider_name, provider_class in self.PROVIDER_PRIORITY:
            try:
                # Try to create a temporary instance to check availability
                temp_provider = provider_class(self.settings)
                if temp_provider.is_available():
                    available_providers.append((provider_name, provider_class))
                    logger.debug(f"Provider {provider_name} is available")
                else:
                    logger.debug(f"Provider {provider_name} is not available")
            except Exception as e:
                logger.debug(f"Provider {provider_name} failed to initialize: {str(e)}")
                continue
        
        return available_providers
    
    def get_provider(self, force_provider: Optional[str] = None) -> BaseLLMProvider:
        """
        Get the current LLM provider, initializing it if necessary.
        
        Args:
            force_provider: Optional provider name to force selection
            
        Returns:
            Initialized LLM provider instance
            
        Raises:
            RuntimeError: If no provider is available
        """
        # If a specific provider is requested, try to use it
        if force_provider:
            return self._create_provider(force_provider)
        
        # If we already have a provider and it's still available, use it
        if self._current_provider and self._current_provider.is_available():
            return self._current_provider
        
        # Find the best available provider
        available_providers = self.get_available_providers()
        
        if not available_providers:
            raise RuntimeError(
                "No LLM providers are available. Please check your API keys and configuration."
            )
        
        # Use the first available provider (highest priority)
        provider_name, provider_class = available_providers[0]
        
        # Create and store the new provider
        self._current_provider = self._create_provider(provider_name)
        self._provider_name = provider_name
        
        logger.info(f"Selected LLM provider: {provider_name}")
        return self._current_provider
    
    def _create_provider(self, provider_name: str) -> BaseLLMProvider:
        """
        Create a specific provider instance.
        
        Args:
            provider_name: Name of the provider to create
            
        Returns:
            Initialized provider instance
            
        Raises:
            ValueError: If the provider name is not supported
        """
        provider_map = {
            "gemini": GeminiProvider,
            "openai": OpenAIProvider,
        }
        
        if provider_name not in provider_map:
            raise ValueError(f"Unsupported provider: {provider_name}")
        
        provider_class = provider_map[provider_name]
        
        try:
            provider = provider_class(self.settings)
            logger.info(f"Successfully created {provider_name} provider")
            return provider
        except Exception as e:
            logger.error(f"Failed to create {provider_name} provider: {str(e)}")
            raise RuntimeError(f"Failed to initialize {provider_name} provider: {str(e)}")
    
    def get_current_provider_info(self) -> Optional[dict]:
        """
        Get information about the current provider.
        
        Returns:
            Dictionary with provider information, or None if no provider is active
        """
        if not self._current_provider:
            return None
        
        info = self._current_provider.get_model_info()
        info["provider_name"] = self._provider_name
        return info
    
    def refresh_provider(self) -> BaseLLMProvider:
        """
        Force refresh of the current provider.
        
        Returns:
            New provider instance
        """
        logger.info("Refreshing LLM provider")
        self._current_provider = None
        self._provider_name = None
        return self.get_provider()
    
    def list_providers(self) -> dict:
        """
        List all available and unavailable providers with their status.
        
        Returns:
            Dictionary containing provider status information
        """
        provider_status = {}
        
        for provider_name, provider_class in self.PROVIDER_PRIORITY:
            try:
                temp_provider = provider_class(self.settings)
                is_available = temp_provider.is_available()
                provider_status[provider_name] = {
                    "available": is_available,
                    "status": "Available" if is_available else "Not configured",
                    "model_info": temp_provider.get_model_info() if is_available else None
                }
            except Exception as e:
                provider_status[provider_name] = {
                    "available": False,
                    "status": f"Error: {str(e)}",
                    "model_info": None
                }
        
        return provider_status


# Global factory instance
_provider_factory: Optional[LLMProviderFactory] = None


def get_provider_factory(settings: Settings) -> LLMProviderFactory:
    """
    Get the global provider factory instance.
    
    Args:
        settings: Application settings
        
    Returns:
        Global provider factory instance
    """
    global _provider_factory
    if _provider_factory is None:
        _provider_factory = LLMProviderFactory(settings)
    return _provider_factory


def get_llm_provider(settings: Settings, force_provider: Optional[str] = None) -> BaseLLMProvider:
    """
    Get an LLM provider instance.
    
    Args:
        settings: Application settings
        force_provider: Optional provider name to force selection
        
    Returns:
        Initialized LLM provider instance
    """
    factory = get_provider_factory(settings)
    return factory.get_provider(force_provider)
