"""
Google Gemini LLM Provider for Git Assistant MCP

This module provides integration with Google's Gemini API for natural language
processing of Git operations.
"""

import json
import logging
from typing import Dict, Any, Optional
from google.generativeai import GenerativeModel, configure
from google.generativeai.types import HarmCategory, HarmBlockThreshold

from ..models.llm_response import LLMResponse
from ...config.settings import Settings

logger = logging.getLogger(__name__)


class GeminiProvider:
    """
    Google Gemini API provider for Git Assistant MCP.
    
    Handles communication with Gemini models for understanding user intent
    and generating appropriate Git commands.
    """
    
    def __init__(self, settings: Settings):
        """
        Initialize the Gemini provider.
        
        Args:
            settings: Application settings containing API configuration
        """
        self.settings = settings
        self.api_key = settings.google_api_key
        self.model_name = settings.gemini_model_name
        self.max_tokens = settings.gemini_max_tokens
        self.temperature = settings.gemini_temperature
        
        # Configure the Gemini client
        configure(api_key=self.api_key)
        
        # Initialize the model
        self.model = GenerativeModel(self.model_name)
        
        # Configure safety settings
        self.safety_settings = {
            HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
            HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
        }
        
        logger.info(f"Initialized Gemini provider with model: {self.model_name}")
    
    async def generate_response(
        self, 
        prompt: str, 
        context: Dict[str, Any]
    ) -> LLMResponse:
        """
        Generate a response from Gemini based on the prompt and context.
        
        Args:
            prompt: The formatted prompt to send to Gemini
            context: Additional context information
            
        Returns:
            LLMResponse object containing the parsed response
            
        Raises:
            Exception: If there's an error communicating with Gemini API
        """
        try:
            logger.debug(f"Sending prompt to Gemini: {prompt[:100]}...")
            
            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config={
                    "temperature": self.temperature,
                    "max_output_tokens": self.max_tokens,
                    "top_p": 0.8,
                    "top_k": 40,
                },
                safety_settings=self.safety_settings
            )
            
            # Extract the response text
            response_text = response.text.strip()
            logger.debug(f"Received response from Gemini: {response_text[:100]}...")
            
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
            logger.error(f"Error generating response from Gemini: {str(e)}")
            raise Exception(f"Failed to generate response from Gemini: {str(e)}")
    
    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """
        Parse the response text from Gemini into a structured format.
        
        Args:
            response_text: Raw response text from Gemini
            
        Returns:
            Parsed response as a dictionary
            
        Raises:
            ValueError: If the response cannot be parsed as valid JSON
        """
        try:
            # Try to extract JSON from the response
            # Gemini sometimes wraps JSON in markdown or adds extra text
            json_start = response_text.find('{')
            json_end = response_text.rfind('}') + 1
            
            if json_start == -1 or json_end == 0:
                raise ValueError("No JSON object found in response")
            
            json_text = response_text[json_start:json_end]
            
            # Parse the JSON
            parsed = json.loads(json_text)
            
            # Validate required fields
            required_fields = ["reply", "command", "explanation"]
            for field in required_fields:
                if field not in parsed:
                    raise ValueError(f"Missing required field: {field}")
            
            return parsed
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            raise ValueError(f"Invalid JSON response from Gemini: {str(e)}")
    
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
        Get information about the current Gemini model.
        
        Returns:
            Dictionary containing model information
        """
        return {
            "provider": "gemini",
            "model_name": self.model_name,
            "max_tokens": self.max_tokens,
            "temperature": self.temperature,
            "safety_settings": str(self.safety_settings)
        }
    
    def update_settings(self, new_settings: Settings) -> None:
        """
        Update the provider settings.
        
        Args:
            new_settings: New settings to apply
        """
        self.temperature = new_settings.gemini_temperature
        self.max_tokens = new_settings.gemini_max_tokens
        
        # Reconfigure the model if the model name changed
        if new_settings.gemini_model_name != self.model_name:
            self.model_name = new_settings.gemini_model_name
            self.model = GenerativeModel(self.model_name)
            logger.info(f"Updated Gemini model to: {self.model_name}")
        
        logger.info("Updated Gemini provider settings")
