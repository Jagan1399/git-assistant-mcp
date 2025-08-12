"""
OpenAI LLM Provider for Git Assistant MCP

This module provides integration with OpenAI's API for natural language
processing of Git operations.
"""

import json
import logging
from typing import Dict, Any, Optional
from openai import AsyncOpenAI

from .base_provider import BaseLLMProvider
from ...models.llm_response import LLMResponse
from ...config.settings import Settings

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseLLMProvider):
    """
    OpenAI API provider for Git Assistant MCP.
    
    Handles communication with OpenAI models for understanding user intent
    and generating appropriate Git commands.
    """
    
    def _validate_configuration(self) -> None:
        """
        Validate that OpenAI configuration is complete.
        
        Raises:
            ValueError: If required configuration is missing
        """
        if not self.settings.openai_api_key:
            raise ValueError("OpenAI API key is required")
        if not self.settings.openai_model_name:
            raise ValueError("OpenAI model name is required")
        
        logger.info("OpenAI configuration validated successfully")
    
    def __init__(self, settings: Settings):
        """
        Initialize the OpenAI provider.
        
        Args:
            settings: Application settings containing API configuration
        """
        super().__init__(settings)
        
        self.api_key = settings.openai_api_key
        self.model_name = settings.openai_model_name
        self.max_tokens = settings.openai_max_tokens
        self.temperature = settings.openai_temperature
        self.base_url = settings.openai_base_url

        # Initialize the OpenAI client
        self.client = AsyncOpenAI(api_key=self.api_key, base_url=self.base_url)

        logger.info(f"Initialized OpenAI provider with model: {self.model_name}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Generate a response from OpenAI based on the prompt and context.
        
        Args:
            prompt: The formatted prompt to send to OpenAI
            context: Additional context information
            
        Returns:
            LLMResponse object containing the parsed response
            
        Raises:
            Exception: If there's an error communicating with OpenAI API
        """
        try:
            logger.debug(f"Sending prompt to OpenAI: {prompt[:100]}...")
            
            # Generate content using OpenAI
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {
                        "role": "system",
                        "content": "You are a Git assistant that helps users with Git operations. Always respond with valid JSON containing the required fields."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                max_tokens=self.max_tokens,
                temperature=self.temperature,
                response_format={"type": "json_object"}
            )
            
            # Extract the response text
            response_text = response.choices[0].message.content.strip()
            logger.debug(f"Received response from OpenAI: {response_text[:100]}...")
            
            # Parse the JSON response
            parsed_response = self._parse_response(response_text)
            
            # Create and return the LLMResponse object
            return LLMResponse(
                reply=parsed_response.get("reply", ""),
                command=parsed_response.get("command", ""),
                updated_context=parsed_response.get("updatedContext"),
                is_destructive=parsed_response.get("is_destructive", False),
                explanation=parsed_response.get("explanation", ""),
                alternatives=parsed_response.get("alternatives"),
                confidence=parsed_response.get("confidence", 0.8)
            )
            
        except Exception as e:
            logger.error(f"Error generating response from OpenAI: {str(e)}")
            raise Exception(f"Failed to generate response from OpenAI: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response text from OpenAI into a structured format.
        
        Args:
            response_text: Raw response text from OpenAI
            
        Returns:
            Parsed response as a dictionary
            
        Raises:
            ValueError: If the response cannot be parsed as valid JSON
        """
        try:
            # Parse the JSON response
            parsed = json.loads(response_text)
            
            # Validate required fields
            required_fields = ["reply", "command", "explanation"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from OpenAI: {str(e)}")
    
    def validate_response(self, response: LLMResponse) -> bool:
        """
        Validate the generated response for safety and correctness.
        
        Args:
            response: The LLMResponse object to validate
            
        Returns:
            True if the response is valid, False otherwise
        """
        # Check if command is empty
        if not response.command or not response.command.strip():
            logger.warning("Generated command is empty")
            return False
        
        # Check if command starts with 'git'
        if not response.command.strip().startswith('git '):
            logger.warning(f"Generated command doesn't start with 'git': {response.command}")
            return False
        
        # Check for potentially dangerous commands
        dangerous_patterns = [
            'git reset --hard',
            'git push --force',
            'git clean -fd',
            'git branch -D',
            'git remote remove'
        ]
        
        for pattern in dangerous_patterns:
            if pattern in response.command:
                if not response.is_destructive:
                    logger.warning(f"Dangerous command detected but not marked as destructive: {response.command}")
                    return False
                break
        
        return True
    
    def get_model_info(self) -> Dict[str, Any]:
        """
        Get information about the current OpenAI model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "openai",
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "api_type": "chat_completion"
        }
    
    def update_settings(self, new_settings: Settings) -> None:
        """
        Update the provider settings.
        
        Args:
            new_settings: New settings to apply
        """
        self.temperature = new_settings.openai_temperature
        self.max_tokens = new_settings.openai_max_tokens
        
        # Reconfigure the client if the API key changed
        if new_settings.openai_api_key != self.api_key:
            self.api_key = new_settings.openai_api_key
            self.client = AsyncOpenAI(api_key=self.api_key)
            logger.info("Updated OpenAI API key")
        
        # Reconfigure the model if the model name changed
        if new_settings.openai_model_name != self.model_name:
            self.model_name = new_settings.openai_model_name
            logger.info(f"Updated OpenAI model to: {self.model_name}")
        
        logger.info("Updated OpenAI provider settings")
    
    def is_available(self) -> bool:
        """
        Check if the OpenAI provider is available and properly configured.
        
        Returns:
            True if the provider can be used, False otherwise
        """
        return bool(self.api_key and self.model_name)
