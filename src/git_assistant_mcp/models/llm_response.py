"""
LLM Response Model for Git Assistant MCP.

This module defines the data models for responses from Large Language Models,
ensuring consistent structure and validation across different LLM providers.
"""

from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, validator
from datetime import datetime


class LLMResponse(BaseModel):
    """
    Structured response from an LLM for Git operations.
    
    This model ensures that all LLM responses follow a consistent format
    and contain the necessary information for safe Git command execution.
    """
    
    # Core response fields
    reply: str = Field(
        description="Natural language confirmation of what the assistant is doing"
    )
    command: str = Field(
        description="The exact Git command to execute"
    )
    explanation: str = Field(
        description="Brief explanation of what the command does"
    )
    
    # Context and prediction fields
    updated_context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Predicted Git context after command execution"
    )
    
    # Safety and validation fields
    is_destructive: bool = Field(
        default=False,
        description="Whether the command could result in data loss"
    )
    confidence: float = Field(
        default=0.8,
        ge=0.0,
        le=1.0,
        description="Confidence level in the generated command (0.0 to 1.0)"
    )
    
    # Alternative approaches
    alternatives: Optional[List[str]] = Field(
        default=None,
        description="Alternative Git commands or approaches"
    )
    
    # Metadata fields
    model_used: Optional[str] = Field(
        default=None,
        description="Name of the LLM model that generated this response"
    )
    generation_time: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="When this response was generated"
    )
    
    # Validation fields
    validation_passed: bool = Field(
        default=False,
        description="Whether the response passed safety validation"
    )
    validation_errors: Optional[List[str]] = Field(
        default=None,
        description="Any validation errors found during safety checks"
    )
    
    @validator('command')
    def validate_command(cls, v):
        """Validate that the command is a valid Git command."""
        if not v or not v.strip():
            raise ValueError('Command cannot be empty')
        
        # Ensure command starts with 'git'
        if not v.strip().startswith('git '):
            raise ValueError('Command must start with "git "')
        
        return v.strip()
    
    @validator('reply')
    def validate_reply(cls, v):
        """Validate that the reply is not empty."""
        if not v or not v.strip():
            raise ValueError('Reply cannot be empty')
        return v.strip()
    
    @validator('explanation')
    def validate_explanation(cls, v):
        """Validate that the explanation is not empty."""
        if not v or not v.strip():
            raise ValueError('Explanation cannot be empty')
        return v.strip()
    
    @validator('confidence')
    def validate_confidence(cls, v):
        """Validate confidence is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Confidence must be between 0.0 and 1.0')
        return v
    
    def is_safe_to_execute(self) -> bool:
        """
        Check if the command is safe to execute.
        
        Returns:
            True if the command is safe, False otherwise
        """
        # Check if validation passed
        if not self.validation_passed:
            return False
        
        # Check confidence level
        if self.confidence < 0.7:
            return False
        
        # Check if destructive operations are properly marked
        if self.is_destructive and not self.validation_passed:
            return False
        
        return True
    
    def get_safety_level(self) -> str:
        """
        Get the safety level of the command.
        
        Returns:
            Safety level: 'safe', 'caution', or 'dangerous'
        """
        if self.is_destructive:
            return 'dangerous'
        elif self.confidence < 0.9:
            return 'caution'
        else:
            return 'safe'
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the response to a dictionary.
        
        Returns:
            Dictionary representation of the response
        """
        return {
            'reply': self.reply,
            'command': self.command,
            'explanation': self.explanation,
            'is_destructive': self.is_destructive,
            'confidence': self.confidence,
            'alternatives': self.alternatives,
            'safety_level': self.get_safety_level(),
            'validation_passed': self.validation_passed,
            'model_used': self.model_used,
            'generation_time': self.generation_time.isoformat() if self.generation_time else None
        }
    
    def get_formatted_output(self, include_metadata: bool = False) -> str:
        """
        Get a formatted string representation of the response.
        
        Args:
            include_metadata: Whether to include metadata fields
            
        Returns:
            Formatted string representation
        """
        output = f"Reply: {self.reply}\n"
        output += f"Command: {self.command}\n"
        output += f"Explanation: {self.explanation}\n"
        
        if self.is_destructive:
            output += "⚠️  WARNING: This is a destructive operation!\n"
        
        if self.alternatives:
            output += f"Alternatives: {', '.join(self.alternatives)}\n"
        
        if include_metadata:
            output += f"Confidence: {self.confidence:.2f}\n"
            output += f"Safety Level: {self.get_safety_level()}\n"
            output += f"Validation: {'Passed' if self.validation_passed else 'Failed'}\n"
            if self.model_used:
                output += f"Model: {self.model_used}\n"
        
        return output
    
    class Config:
        """Pydantic configuration."""
        validate_assignment = True
        extra = "forbid"  # Don't allow extra fields


class LLMRequest(BaseModel):
    """
    Request structure for LLM API calls.
    
    This model defines the format for sending requests to LLM providers.
    """
    
    prompt: str = Field(
        description="The formatted prompt to send to the LLM"
    )
    context: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional context information for the LLM"
    )
    max_tokens: Optional[int] = Field(
        default=None,
        description="Maximum tokens for response generation"
    )
    temperature: Optional[float] = Field(
        default=None,
        description="Temperature setting for response generation"
    )
    
    @validator('prompt')
    def validate_prompt(cls, v):
        """Validate that the prompt is not empty."""
        if not v or not v.strip():
            raise ValueError('Prompt cannot be empty')
        return v.strip()
    
    @validator('temperature')
    def validate_temperature(cls, v):
        """Validate temperature if provided."""
        if v is not None and (v < 0.0 or v > 1.0):
            raise ValueError('Temperature must be between 0.0 and 1.0')
        return v


class LLMError(BaseModel):
    """
    Error response from LLM API calls.
    
    This model provides structured error information when LLM calls fail.
    """
    
    error_type: str = Field(
        description="Type of error that occurred"
    )
    error_message: str = Field(
        description="Human-readable error message"
    )
    error_code: Optional[str] = Field(
        default=None,
        description="Error code if available"
    )
    provider: str = Field(
        description="Name of the LLM provider that generated the error"
    )
    timestamp: datetime = Field(
        default_factory=datetime.now,
        description="When the error occurred"
    )
    context: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Additional context about the error"
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert the error to a dictionary.
        
        Returns:
            Dictionary representation of the error
        """
        return {
            'error_type': self.error_type,
            'error_message': self.error_message,
            'error_code': self.error_code,
            'provider': self.provider,
            'timestamp': self.timestamp.isoformat(),
            'context': self.context
        }
