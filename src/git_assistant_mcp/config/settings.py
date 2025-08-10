"""
Configuration settings for Git Assistant MCP.

This module provides centralized configuration management using Pydantic settings
with environment variable support.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be configured via environment variables or .env file.
    """
    
    # =============================================================================
    # LLM Configuration
    # =============================================================================
    
    # Primary LLM provider
    llm_provider: str = Field(
        default="gemini",
        description="LLM provider to use: gemini, openai, anthropic, or local"
    )
    
    # Google Gemini Configuration
    google_api_key: str = Field(
        default="",
        description="Google API key for Gemini access"
    )
    gemini_model_name: str = Field(
        default="gemini-pro",
        description="Gemini model to use (e.g., gemini-pro, gemini-pro-vision)"
    )
    gemini_max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for Gemini response generation"
    )
    gemini_temperature: float = Field(
        default=0.1,
        description="Temperature setting for Gemini (0.0 = deterministic, 1.0 = creative)"
    )
    
    # OpenAI Configuration (fallback)
    openai_api_key: str = Field(
        default="",
        description="OpenAI API key for GPT models"
    )
    openai_model_name: str = Field(
        default="gpt-4",
        description="OpenAI model to use"
    )
    openai_max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for OpenAI response generation"
    )
    openai_temperature: float = Field(
        default=0.1,
        description="Temperature setting for OpenAI"
    )
    
    # Anthropic Configuration (fallback)
    anthropic_api_key: str = Field(
        default="",
        description="Anthropic API key for Claude models"
    )
    anthropic_model_name: str = Field(
        default="claude-3-sonnet-20240229",
        description="Anthropic model to use"
    )
    anthropic_max_tokens: int = Field(
        default=1000,
        description="Maximum tokens for Anthropic response generation"
    )
    
    # =============================================================================
    # Git Configuration
    # =============================================================================
    
    git_timeout: int = Field(
        default=30,
        description="Timeout for Git operations in seconds"
    )
    max_commits: int = Field(
        default=5,
        description="Maximum number of recent commits to analyze"
    )
    safe_mode: bool = Field(
        default=True,
        description="Enable safe mode with warnings for destructive operations"
    )
    git_path: str = Field(
        default="git",
        description="Path to git executable"
    )
    
    # =============================================================================
    # UI Configuration
    # =============================================================================
    
    enable_colors: bool = Field(
        default=True,
        description="Enable colored output in terminal"
    )
    verbose_output: bool = Field(
        default=False,
        description="Enable verbose logging output"
    )
    show_progress: bool = Field(
        default=True,
        description="Show progress indicators for long operations"
    )
    
    # =============================================================================
    # Security Configuration
    # =============================================================================
    
    enable_command_validation: bool = Field(
        default=True,
        description="Enable validation of generated Git commands"
    )
    log_commands: bool = Field(
        default=True,
        description="Log all executed Git commands"
    )
    require_confirmation: bool = Field(
        default=True,
        description="Require confirmation for destructive operations"
    )
    
    # =============================================================================
    # Performance Configuration
    # =============================================================================
    
    enable_caching: bool = Field(
        default=True,
        description="Enable caching of Git state information"
    )
    cache_ttl: int = Field(
        default=300,
        description="Cache time-to-live in seconds"
    )
    max_concurrent_operations: int = Field(
        default=3,
        description="Maximum concurrent Git operations"
    )
    
    # =============================================================================
    # Development Configuration
    # =============================================================================
    
    debug: bool = Field(
        default=False,
        description="Enable debug mode with additional logging"
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level: DEBUG, INFO, WARNING, ERROR"
    )
    test_mode: bool = Field(
        default=False,
        description="Test mode (disables actual Git operations)"
    )
    
    # =============================================================================
    # Cursor Integration Configuration
    # =============================================================================
    
    cursor_integration_enabled: bool = Field(
        default=True,
        description="Enable Cursor editor integration"
    )
    chat_command_prefix: str = Field(
        default="@git",
        description="Prefix for chat commands in Cursor"
    )
    auto_execute_safe_commands: bool = Field(
        default=False,
        description="Automatically execute safe commands without confirmation"
    )
    
    # =============================================================================
    # Validation and Configuration
    # =============================================================================
    
    @field_validator('llm_provider')
    @classmethod
    def validate_llm_provider(cls, v):
        """Validate LLM provider selection."""
        allowed_providers = ['gemini', 'openai', 'anthropic', 'local']
        if v not in allowed_providers:
            raise ValueError(f'llm_provider must be one of {allowed_providers}')
        return v
    
    @field_validator('gemini_temperature', 'openai_temperature')
    @classmethod
    def validate_temperature(cls, v):
        """Validate temperature settings."""
        if not 0.0 <= v <= 1.0:
            raise ValueError('Temperature must be between 0.0 and 1.0')
        return v
    
    @field_validator('max_commits')
    @classmethod
    def validate_max_commits(cls, v):
        """Validate maximum commits setting."""
        if v < 1 or v > 100:
            raise ValueError('max_commits must be between 1 and 100')
        return v
    
    @field_validator('git_timeout')
    @classmethod
    def validate_git_timeout(cls, v):
        """Validate Git timeout setting."""
        if v < 5 or v > 300:
            raise ValueError('git_timeout must be between 5 and 300 seconds')
        return v
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        
        # Environment variable mapping
        fields = {
            'google_api_key': {'env': 'GOOGLE_API_KEY'},
            'gemini_model_name': {'env': 'GEMINI_MODEL_NAME'},
            'gemini_max_tokens': {'env': 'GEMINI_MAX_TOKENS'},
            'gemini_temperature': {'env': 'GEMINI_TEMPERATURE'},
            'openai_api_key': {'env': 'OPENAI_API_KEY'},
            'openai_model_name': {'env': 'OPENAI_MODEL_NAME'},
            'openai_max_tokens': {'env': 'OPENAI_MAX_TOKENS'},
            'openai_temperature': {'env': 'OPENAI_TEMPERATURE'},
            'anthropic_api_key': {'env': 'ANTHROPIC_API_KEY'},
            'anthropic_model_name': {'env': 'ANTHROPIC_MODEL_NAME'},
            'anthropic_max_tokens': {'env': 'ANTHROPIC_MAX_TOKENS'},
        }


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """
    Get the global settings instance.
    
    Returns:
        Settings instance with current configuration
    """
    return settings


def reload_settings() -> Settings:
    """
    Reload settings from environment variables.
    
    Returns:
        Updated settings instance
    """
    global settings
    settings = Settings()
    return settings
