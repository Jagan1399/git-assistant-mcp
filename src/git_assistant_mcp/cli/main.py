"""
Command-Line Interface for Git Assistant MCP.

This module provides a CLI for interacting with the Git Assistant, allowing users
to get Git command suggestions from natural language queries.
"""

import argparse
import asyncio
import json
import logging
from typing import List, Optional

from ..core.mcp_wrapper import create_git_assistant
from ..config.settings import get_settings

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main(args: Optional[List[str]] = None):
    """
    Main function to run the Git Assistant CLI.
    
    Args:
        args: Command-line arguments (for testing purposes)
    """
    parser = create_parser()
    parsed_args = parser.parse_args(args)
    
    # Load settings
    settings = get_settings()
    
    # Create assistant instance
    assistant = create_git_assistant(settings=settings, repo_path=parsed_args.repo_path)
    
    # Run the appropriate command
    try:
        asyncio.run(run_command(parsed_args, assistant))
    except Exception as e:
        logger.error(f"An unexpected error occurred: {e}")
        exit(1)

def create_parser() -> argparse.ArgumentParser:
    """
    Create the argument parser for the CLI.
    
    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="Git Assistant MCP - Your AI-powered Git sidekick."
    )
    
    parser.add_argument(
        "user_request",
        nargs="?",
        default=None,
        help="Natural language request for a Git command (e.g., 'stage all changes')."
    )
    
    parser.add_argument(
        "--repo-path",
        type=str,
        default=None,
        help="Path to the Git repository (defaults to current directory)."
    )
    
    parser.add_argument(
        "--status",
        action="store_true",
        help="Get a quick status overview of the repository."
    )
    
    parser.add_argument(
        "--explain",
        type=str,
        metavar="GIT_COMMAND",
        help="Explain what a given Git command does."
    )
    
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output the result in JSON format."
    )
    
    return parser

async def run_command(args: argparse.Namespace, assistant):
    """
    Run the appropriate command based on parsed arguments.
    
    Args:
        args: Parsed command-line arguments
        assistant: GitAssistantMCP instance
    """
    if args.status:
        result = await assistant.get_repository_status()
        print_result(result, args.json)
    elif args.explain:
        result = await assistant.explain_command(args.explain)
        print_result(result, args.json)
    elif args.user_request:
        result = await assistant.process_request(args.user_request)
        print_result(result, args.json)
    else:
        # Default behavior: show help
        parser = create_parser()
        parser.print_help()

def print_result(result: dict, as_json: bool):
    """
    Print the result in the specified format.
    
    Args:
        result: Result dictionary from the assistant
        as_json: Whether to print as JSON or human-readable text
    """
    if as_json:
        print(json.dumps(result, indent=2))
    else:
        if result.get("success"):
            if "generated_command" in result:
                # Process request output
                print(f"✅ {result.get('message', 'Success')}")
                print(f"\n🤖 Assistant's Reply: {result.get('explanation')}")
                print(f"\n✨ Suggested Command:\n    git {result['generated_command'].replace('git ', '', 1)}")
                
                if result.get("execution_result", {}).get("executed"):
                    print("\n📝 Execution Output:")
                    print(result["execution_result"].get("stdout") or "No output")
            elif "status_summary" in result:
                # Status output
                print(f"Repository Status: {result['repository_path']}")
                print(f"Current Branch: {result['current_branch']}")
                print(f"Summary: {result['status_summary']}")
            elif "explanation" in result:
                # Explain output
                print(f"Explanation for: {result['command']}")
                print(f"\n{result['explanation']}")
        else:
            print(f"❌ Error: {result.get('error', 'An unknown error occurred.')}")

if __name__ == "__main__":
    main()