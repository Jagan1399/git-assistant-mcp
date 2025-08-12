"""
MCP Wrapper for Git Assistant MCP

This module provides the main interface that coordinates all Git Assistant operations.
It handles natural language requests, state scraping, LLM processing, and command execution.
"""

import asyncio
import logging
import subprocess
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from ..config.settings import Settings, get_settings
from ..core.state_scraper import StateScraper, GitCommandError
from ..llm import get_llm_provider
from ..models.git_context import GitContext
from ..models.llm_response import LLMResponse
from ..llm.prompt_templates import format_git_command_prompt

logger = logging.getLogger(__name__)

class GitAssistantMCP:
    """
    Main Git Assistant MCP wrapper that coordinates all operations.
    
    This class provides a unified interface for:
    1. Understanding natural language Git requests
    2. Gathering current repository state
    3. Generating appropriate Git commands
    4. Executing commands safely
    5. Providing explanations and alternatives
    """
    
    def __init__(self, settings: Optional[Settings] = None, repo_path: Optional[str] = None):
        """
        Initialize the Git Assistant MCP.
        
        Args:
            settings: Application settings (auto-loaded if not provided)
            repo_path: Path to Git repository (auto-detected if not provided)
        """
        self.settings = settings or get_settings()
        if repo_path:
            self.repo_path = Path(repo_path)
        else:
            # Try to find a Git repository in the current directory or subdirectories
            current_path = Path.cwd()
            if (current_path / ".git").exists():
                self.repo_path = current_path
            elif (current_path / "git-assistant-mcp" / ".git").exists():
                self.repo_path = current_path / "git-assistant-mcp"
            else:
                # Search for any .git directory in subdirectories
                for subdir in current_path.iterdir():
                    if subdir.is_dir() and (subdir / ".git").exists():
                        self.repo_path = subdir
                        break
                else:
                    self.repo_path = current_path
        
        # Initialize components
        self.state_scraper = StateScraper(self.repo_path)
        self.llm_provider = None  # Lazy initialization
        
        # Safety and validation flags
        self.safe_mode = self.settings.safe_mode
        self.require_confirmation = self.settings.require_confirmation
        self.enable_command_validation = self.settings.enable_command_validation
        
        logger.info(f"Initialized Git Assistant MCP for repository: {self.repo_path}")
    
    async def get_llm_provider(self):
        """Get the LLM provider, initializing it if necessary."""
        if self.llm_provider is None:
            self.llm_provider = get_llm_provider(self.settings)
            logger.info(f"Initialized LLM provider: {self.llm_provider.get_model_info()['provider']}")
        return self.llm_provider
    
    async def process_request(
        self, 
        user_request: str, 
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Process a natural language Git request.
        
        This is the main entry point for all Git assistance requests.
        
        Args:
            user_request: Natural language description of what the user wants to do
            context: Additional context information
            
        Returns:
            Dictionary containing the response, generated command, and metadata
        """
        try:
            logger.info(f"Processing request: {user_request[:100]}...")
            
            # Step 1: Gather current Git repository state
            git_context = await self._gather_git_state()
            
            # Step 2: Generate LLM response with context
            llm_response = await self._generate_llm_response(user_request, git_context, context)
            
            # Step 3: Validate and prepare command execution
            execution_plan = await self._prepare_execution_plan(llm_response, git_context)
            
            # Step 4: Execute command if safe and confirmed
            execution_result = await self._execute_command(execution_plan)
            
            # Step 5: Compile final response
            return self._compile_response(user_request, llm_response, execution_result, git_context)
            
        except Exception as e:
            logger.error(f"Error processing request: {str(e)}")
            return self._create_error_response(user_request, str(e))
    
    async def _gather_git_state(self) -> GitContext:
        """
        Gather the current state of the Git repository.
        
        Returns:
            GitContext object containing current repository state
        """
        try:
            logger.debug("Gathering Git repository state...")
            git_context = self.state_scraper.scrape_state()
            logger.debug(f"Git state gathered: {git_context.get_summary()}")
            return git_context
        except GitCommandError as e:
            logger.error(f"Failed to gather Git state: {str(e)}")
            raise RuntimeError(f"Unable to access Git repository: {str(e)}")
    
    async def _generate_llm_response(
        self, 
        user_request: str, 
        git_context: GitContext, 
        context: Optional[Dict[str, Any]] = None
    ) -> LLMResponse:
        """
        Generate LLM response based on user request and Git context.
        
        Args:
            user_request: What the user wants to do
            git_context: Current Git repository state
            context: Additional context
            
        Returns:
            LLMResponse object containing generated command and explanation
        """
        try:
            # Get LLM provider
            llm_provider = await self.get_llm_provider()
            
            # Create prompt with Git context
            prompt = self._create_prompt(user_request, git_context, context)
            
            # Generate response
            logger.debug("Generating LLM response...")
            response = await llm_provider.generate_response(prompt, {
                "git_context": git_context,
                "user_request": user_request,
                "additional_context": context or {}
            })
            
            # Validate response
            if self.enable_command_validation:
                if not llm_provider.validate_response(response):
                    logger.warning("LLM response validation failed")
                    # Could implement fallback or retry logic here
            
            logger.debug(f"LLM response generated: {response.command}")
            return response
            
        except Exception as e:
            logger.error(f"Failed to generate LLM response: {str(e)}")
            raise RuntimeError(f"LLM processing failed: {str(e)}")
    
    def _create_prompt(
        self,
        user_request: str,
        git_context: GitContext,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Create a structured prompt for the LLM using the centralized template.

        Args:
            user_request: What the user wants to do
            git_context: Current Git repository state
            context: Additional context (not used in this implementation)

        Returns:
            Formatted prompt string
        """
        # Conditionally use full or summarized git context for LLM prompts
        user_request_lower = user_request.lower()
        if any(kw in user_request_lower for kw in ["file", "diff", "branch list", "show all", "details"]):
            # Use full context for file-specific or detail-heavy operations
            git_context_dict = git_context.model_dump(mode="json")
            # Limit files unless user explicitly requests all files
            if not any(kw in user_request_lower for kw in ["all files", "list all files", "every file"]):
                if "working_directory_status" in git_context_dict:
                    git_context_dict["working_directory_status"] = [
                        f for f in git_context_dict["working_directory_status"]
                        if f["status"] in ["modified", "deleted", "renamed", "untracked"]
                    ]
                if "staging_area_status" in git_context_dict:
                    git_context_dict["staging_area_status"] = [
                        f for f in git_context_dict["staging_area_status"]
                        if f["status"] in ["modified", "deleted", "renamed", "untracked"]
                    ]
            # Exclude large lists unless explicitly requested
            if not any(kw in user_request_lower for kw in ["remote branch", "remote branches", "show stashes", "stash", "list stashes"]):
                if "remote_branches" in git_context_dict:
                    git_context_dict["remote_branches"] = []
                if "stashes" in git_context_dict:
                    git_context_dict["stashes"] = []
        else:
            # Use summarized context for most requests
            git_context_dict = git_context.to_summarized_dict()

        return format_git_command_prompt(
            git_context=git_context_dict,
            user_query=user_request
        )
    
    async def _prepare_execution_plan(
        self, 
        llm_response: LLMResponse, 
        git_context: GitContext
    ) -> Dict[str, Any]:
        """
        Prepare the execution plan for the generated command.
        
        Args:
            llm_response: LLM-generated response
            git_context: Current Git context
            
        Returns:
            Execution plan dictionary
        """
        command = llm_response.command.strip()
        
        # Basic validation
        if not command.startswith('git '):
            raise ValueError(f"Invalid Git command: {command}")
        
        # Check for dangerous operations
        dangerous_patterns = [
            'git reset --hard',
            'git push --force',
            'git clean -fd',
            'git branch -D',
            'git remote remove'
        ]
        
        is_dangerous = any(pattern in command for pattern in dangerous_patterns)
        
        # Create execution plan
        execution_plan = {
            "command": command,
            "is_destructive": is_dangerous or llm_response.is_destructive,
            "explanation": llm_response.explanation,
            "alternatives": llm_response.alternatives,
            "confidence": llm_response.confidence,
            "requires_confirmation": is_dangerous or self.require_confirmation,
            "estimated_risk": "HIGH" if is_dangerous else "LOW",
            "git_context": git_context
        }
        
        logger.info(f"Execution plan prepared: {command} (destructive: {is_dangerous})")
        return execution_plan
    
    async def _execute_command(self, execution_plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the Git command based on the execution plan.
        
        Args:
            execution_plan: Prepared execution plan
            
        Returns:
:           Execution result dictionary
        """
        command = execution_plan["command"]
        is_destructive = execution_plan["is_destructive"]
        
        # Check if confirmation is required
        if execution_plan["requires_confirmation"]:
            logger.info(f"Command requires confirmation: {command}")
            # In a real implementation, this would prompt the user
            # For now, we'll simulate confirmation
            confirmed = True  # TODO: Implement actual user confirmation
            if not confirmed:
                return {
                    "executed": False,
                    "reason": "User cancelled execution",
                    "command": command
                }
        
        try:
            logger.info(f"Executing command: {command}")
            
            # Execute the command (use shell=True for complex commands with quotes)
            if '"' in command or "'" in command:
                # Use shell=True for commands with quotes to handle them properly
                result = subprocess.run(
                    command,
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=self.settings.git_timeout,
                    shell=True
                )
            else:
                # Use split() for simple commands
                result = subprocess.run(
                    command.split(),
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                    timeout=self.settings.git_timeout
                )
            
            # Process result
            success = result.returncode == 0
            stdout = result.stdout.strip()
            stderr = result.stderr.strip()
            
            execution_result = {
                "executed": True,
                "success": success,
                "command": command,
                "return_code": result.returncode,
                "stdout": stdout,
                "stderr": stderr,
                "is_destructive": is_destructive
            }
            
            if success:
                logger.info(f"Command executed successfully: {command}")
            else:
                logger.warning(f"Command failed: {command} (return code: {result.returncode})")
                if stderr:
                    logger.warning(f"Error output: {stderr}")
            
            return execution_result
            
        except subprocess.TimeoutExpired:
            logger.error(f"Command timed out: {command}")
            return {
                "executed": False,
                "reason": "Command execution timed out",
                "command": command
            }
        except Exception as e:
            logger.error(f"Failed to execute command: {command} - {str(e)}")
            return {
                "executed": False,
                "reason": f"Execution error: {str(e)}",
                "command": command
            }
    
    def _compile_response(
        self, 
        user_request: str, 
        llm_response: LLMResponse, 
        execution_result: Dict[str, Any], 
        git_context: GitContext
    ) -> Dict[str, Any]:
        """
        Compile the final response for the user.
        
        Args:
            user_request: Original user request
            llm_response: LLM-generated response
            execution_result: Command execution result
            git_context: Git context used for the operation
            
        Returns:
            Final response dictionary
        """
        response = {
            "success": True,
            "user_request": user_request,
            "generated_command": llm_response.command,
            "explanation": llm_response.explanation,
            "execution_result": execution_result,
            "alternatives": llm_response.alternatives,
            "confidence": llm_response.confidence,
            "timestamp": git_context.captured_at.isoformat(),
            "repository_info": {
                "path": str(git_context.repository_path),
                "branch": getattr(git_context.current_branch, 'name', 'unknown'),
                "status_summary": git_context.get_summary()
            }
        }
        
        # Add execution details
        if execution_result["executed"]:
            if execution_result["success"]:
                response["message"] = "Command executed successfully"
                if execution_result["stdout"]:
                    response["output"] = execution_result["stdout"]
            else:
                response["message"] = "Command executed but failed"
                response["error"] = execution_result["stderr"]
                response["success"] = False
        else:
            response["message"] = "Command not executed"
            response["reason"] = execution_result.get("reason", "Unknown reason")
        
        return response
    
    def _create_error_response(self, user_request: str, error_message: str) -> Dict[str, Any]:
        """
        Create an error response when processing fails.
        
        Args:
            user_request: Original user request
            error_message: Error description
            
        Returns:
            Error response dictionary
        """
        return {
            "success": False,
            "user_request": user_request,
            "error": error_message,
            "message": "Failed to process request",
            "timestamp": None,
            "repository_info": None
        }
    
    async def get_repository_status(self) -> Dict[str, Any]:
        """
        Get a quick status overview of the repository.
        
        Returns:
            Repository status dictionary
        """
        try:
            git_context = await self._gather_git_state()
            return {
                "success": True,
                "repository_path": str(git_context.repository_path),
                "current_branch": getattr(git_context.current_branch, 'name', 'unknown'),
                "status_summary": git_context.get_summary(),
                "file_counts": {
                    "modified": git_context.modified_files,
                    "staged": git_context.staged_files,
                    "untracked": git_context.untracked_files,
                    "total": git_context.total_files
                },
                "special_states": {
                    "has_conflicts": git_context.has_conflicts,
                    "is_merging": git_context.is_merging,
                    "is_rebasing": git_context.is_rebasing,
                    "is_detached_head": git_context.is_detached_head
                }
            }
        except Exception as e:
            logger.error(f"Failed to get repository status: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def explain_command(self, git_command: str) -> Dict[str, Any]:
        """
        Explain what a Git command does.
        
        Args:
            git_command: Git command to explain
            
        Returns:
            Command explanation dictionary
        """
        try:
            llm_provider = await self.get_llm_provider()
            
            prompt = f"""
            Explain what this Git command does: {git_command}
            
            Format your response as JSON with EXACTLY these fields:
            {{
              "reply": "Brief explanation of what the command does",
              "command": "{git_command}",
              "explanation": "Detailed explanation of what the command does, when to use it, and any risks",
              "is_destructive": false,
              "confidence": 0.9
            }}
            
            IMPORTANT: Only include the fields above. Do not add alternatives or other fields.
            """
            
            response = await llm_provider.generate_response(prompt, {"command": git_command})
            
            return {
                "success": True,
                "command": git_command,
                "explanation": response.explanation,
                "reply": response.reply
            }
            
        except Exception as e:
            logger.error(f"Failed to explain command: {str(e)}")
            return {
                "success": False,
                "command": git_command,
                "error": str(e)
            }
    
    def get_system_info(self) -> Dict[str, Any]:
        """
        Get information about the Git Assistant system.
        
        Returns:
            System information dictionary
        """
        try:
            llm_info = self.llm_provider.get_model_info() if self.llm_provider else None
            
            return {
                "success": True,
                "system": {
                    "name": "Git Assistant MCP",
                    "version": "1.0.0",
                    "repository_path": str(self.repo_path),
                    "safe_mode": self.safe_mode,
                    "require_confirmation": self.require_confirmation
                },
                "llm_provider": llm_info,
                "settings": {
                    "git_timeout": self.settings.git_timeout,
                    "max_commits": self.settings.max_commits,
                    "enable_command_validation": self.enable_command_validation
                }
            }
        except Exception as e:
            logger.error(f"Failed to get system info: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    def get_manifest(self) -> Dict[str, Any]:
        """
        Get the MCP manifest, which describes the server's capabilities.

        Returns:
            MCP manifest dictionary
        """
        return {
            "name": "git-assistant-mcp",
            "display_name": "Git Assistant MCP",
            "description": "An AI-powered assistant for Git command-line operations.",
            "tools": {
                "get_git_context": {
                    "display_name": "Get Git Context",
                    "description": "Get the current git status, including branch, status, and recent commits.",
                    "input_schema": {
                        "type": "object",
                        "properties": {},
                        "required": []
                    }
                }
            },
            "resources": {}
        }


# Convenience function for quick access
def create_git_assistant(
    repo_path: Optional[str] = None,
    settings: Optional[Settings] = None
) -> GitAssistantMCP:
    """
    Create a Git Assistant MCP instance.
    
    Args:
        repo_path: Path to Git repository (auto-detected if not provided)
        settings: Application settings (auto-loaded if not provided)
        
    Returns:
        Configured GitAssistantMCP instance
    """
    # Load settings if not provided
    s = settings or get_settings()
    # Log relevant environment variables before initializing LLM
    logger.info("LLM environment variables for initialization:")
    logger.info(f"llm_provider: {s.llm_provider}")
    logger.info(f"google_api_key: {s.google_api_key}")
    logger.info(f"gemini_model_name: {s.gemini_model_name}")
    logger.info(f"openai_api_key: {s.openai_api_key}")
    logger.info(f"openai_model_name: {s.openai_model_name}")
    logger.info(f"openai_base_url: {s.openai_base_url}")
    logger.info(f"anthropic_api_key: {getattr(s, 'anthropic_api_key', None)}")
    logger.info(f"anthropic_model_name: {getattr(s, 'anthropic_model_name', None)}")
    return GitAssistantMCP(settings=s, repo_path=repo_path)
