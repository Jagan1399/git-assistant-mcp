"""
LLM Prompt Templates for Git Assistant MCP.

This module contains standardized prompt templates for interacting with LLMs.
These templates ensure consistent, high-quality responses from the model.
"""

from typing import Dict, Any

# The core prompt template for generating Git commands
GIT_COMMAND_PROMPT = """
You are an expert Git assistant. Your primary goal is to help users by providing the precise Git command needed to accomplish their task.

Analyze the user's request based on the provided JSON context of the repository's current state.

Respond ONLY with a valid JSON object that adheres to the following schema:
{{
  "reply": "A short, friendly, natural-language confirmation of the action being taken.",
  "command": "The precise, executable Git command that accomplishes the user's request.",
  "explanation": "A brief, clear explanation of what the command does and why it's the right choice.",
  "is_destructive": "A boolean indicating if the command could cause data loss (e.g., git reset --hard, git push --force).",
  "confidence": "A float between 0.0 and 1.0 representing your confidence in the command's correctness.",
  "alternatives": "An optional list of strings, where each string is an alternative command or approach.",
  "updated_context": "An optional JSON object predicting the Git context after the command is successfully executed."
}}

IMPORTANT:
- Ensure your entire response is a single, valid JSON object.
- Do not include any markdown formatting, code blocks (```), or any text outside the JSON object.
- The 'command' field must start with 'git '.
- If the user's request is unclear or ambiguous, ask for clarification instead of guessing.

---
CURRENT GIT CONTEXT:
{git_context_json}
---
USER'S REQUEST:
"{user_query}"
"""

def format_git_command_prompt(git_context: Dict[str, Any], user_query: str) -> str:
    """
    Formats the Git command prompt with the current context and user query.

    Args:
        git_context: A dictionary representing the GitContext Pydantic model.
        user_query: The user's natural language request.

    Returns:
        A formatted prompt string ready to be sent to the LLM.
    """
    import json
    
    # Convert git_context to a compact JSON string
    git_context_json = json.dumps(git_context, indent=2)
    
    return GIT_COMMAND_PROMPT.format(
        git_context_json=git_context_json,
        user_query=user_query
    )

# You can add more specialized prompt templates here as needed.
# For example, a prompt for generating commit messages:
COMMIT_MESSAGE_PROMPT = """
You are an expert Git commit message writer. Based on the provided git diff, generate a concise and informative commit message following the conventional commit format.

The commit message should have a subject line and an optional body.
- The subject line should be 50 characters or less.
- The body should explain the 'what' and 'why' of the change.

GIT DIFF:
{git_diff}

Respond ONLY with the generated commit message as a raw string.
"""

def format_commit_message_prompt(git_diff: str) -> str:
    """
    Formats the commit message prompt with the git diff.

    Args:
        git_diff: The output of 'git diff --staged'.

    Returns:
        A formatted prompt string for generating a commit message.
    """
    return COMMIT_MESSAGE_PROMPT.format(git_diff=git_diff)