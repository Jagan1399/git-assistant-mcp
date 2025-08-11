"""
Base LLM Provider Interface for Git Assistant MCP

This module defines the abstract base class that all LLM providers must implement.
This ensures consistent behavior across different providers while allowing
provider-specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
from ...models.llm_response import LLMResponse
from ...config.settings import Settings


class BaseLLMProvider(ABC):
    """
    Abstract base class for LLM providers.
    
    All LLM providers must implement these methods to ensure
    consistent behavior across the application.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the provider with settings.
        
        Args:
            settings: Application settings containing API configuration
        """
        self.settings = settings
        self._validate_configuration()
    
    @abstractmethod
    def _validate_configuration(self) -> None:
        """
        Validate that the provider has all required configuration.
        
        Raises:
            ValueError: If required configuration is missing
        """
        pass
    
    @abstractmethod
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Generate a response from the LLM based on the prompt and context.
        
        Args:
            prompt: The formatted prompt to send to the LLM
            context: Additional context information
            
        Returns:
            LLMResponse object containing the parsed response
            
        Raises:
            Exception: If there's an error communicating with the LLM API
        """
        pass
    
    @abstractmethod
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate the generated response for safety and correctness.
        
        Args:
            response: The LLMResponse object to validate
            
        Returns:
            True if the response is valid, False otherwise
        """
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current LLM model.
        
        Returns:
            Dictionary containing model information
        """
        pass
    
    @abstractmethod
    def update_settings(self, new_settings: Settings) -> None:
        """
        Update the provider settings.
        
        Args:
            new_settings: New settings to apply
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """
        Check if the provider is available and properly configured.
        
        Returns:
            True if the provider can be used, False otherwise
        """
        pass
