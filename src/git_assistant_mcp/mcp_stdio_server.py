#!/usr/bin/env python3
"""
MCP Stdio Server implementation for Git Assistant.

This module provides a standard MCP server that communicates via stdio,
following the MCP protocol specification for stdio transport.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import (
    Resource,
    Tool,
    TextContent,
    ImageContent,
    EmbeddedResource,
    CallToolResult,
    ListResourcesResult,
    ListToolsResult,
    ReadResourceResult,
)

from .core.mcp_wrapper import create_git_assistant

# Configure logging to stderr to avoid interfering with stdio communication
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stderr
)
logger = logging.getLogger(__name__)

# Create the MCP server
server = Server("git-assistant-mcp")

# Global assistant instance
assistant = None

async def initialize_assistant():
    """Initialize the Git Assistant instance."""
    global assistant
    try:
        assistant = create_git_assistant()
        logger.info("Git Assistant MCP initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize Git Assistant: {e}")
        raise

@server.list_tools()
async def handle_list_tools() -> ListToolsResult:
    """List available tools."""
    tools = [
        Tool(
            name="process_git_request",
            description="Process natural language Git requests and execute commands",
            inputSchema={
                "type": "object",
                "properties": {
                    "request": {
                        "type": "string",
                        "description": "Natural language description of what you want to do with git"
                    },
                    "safe_mode": {
                        "type": "boolean",
                        "description": "Enable safe mode for destructive operations",
                        "default": True
                    }
                },
                "required": ["request"]
            }
        ),
        Tool(
            name="get_git_status",
            description="Get current Git repository status",
            inputSchema={
                "type": "object",
                "properties": {
                    "detailed": {
                        "type": "boolean",
                        "description": "Include detailed file information",
                        "default": False
                    }
                }
            }
        ),
        Tool(
            name="explain_git_command",
            description="Explain what a Git command does",
            inputSchema={
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "Git command to explain"
                    }
                },
                "required": ["command"]
            }
        )
    ]
    
    return ListToolsResult(tools=tools)

@server.call_tool()
async def handle_call_tool(name: str, arguments: Dict[str, Any]) -> CallToolResult:
    """Handle tool calls."""
    if assistant is None:
        return CallToolResult(
            content=[TextContent(type="text", text="Error: Git Assistant is not initialized")]
        )
    
    try:
        if name == "process_git_request":
            request_text = arguments.get("request", "")
            if not request_text:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: No request provided")]
                )
            
            result = await assistant.process_request(request_text)
            formatted_response = format_git_response(result)
            
            return CallToolResult(
                content=[TextContent(type="text", text=formatted_response)]
            )
        
        elif name == "get_git_status":
            result = await assistant.get_repository_status()
            formatted_response = format_status_response(result)
            
            return CallToolResult(
                content=[TextContent(type="text", text=formatted_response)]
            )
        
        elif name == "explain_git_command":
            command = arguments.get("command", "")
            if not command:
                return CallToolResult(
                    content=[TextContent(type="text", text="Error: No command provided")]
                )
            
            result = await assistant.explain_command(command)
            formatted_response = format_explanation_response(result)
            
            return CallToolResult(
                content=[TextContent(type="text", text=formatted_response)]
            )
        
        else:
            return CallToolResult(
                content=[TextContent(type="text", text=f"Error: Unknown tool '{name}'")]
            )
    
    except Exception as e:
        logger.error(f"Error calling tool {name}: {e}")
        return CallToolResult(
            content=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

@server.list_resources()
async def handle_list_resources() -> ListResourcesResult:
    """List available resources."""
    resources = [
        Resource(
            uri="git://current-status",
            name="Current Git Status",
            description="Current status of the Git repository",
            mimeType="application/json"
        ),
        Resource(
            uri="git://system-info",
            name="System Information", 
            description="Information about the Git Assistant system",
            mimeType="application/json"
        )
    ]
    
    return ListResourcesResult(resources=resources)

@server.read_resource()
async def handle_read_resource(uri: str) -> ReadResourceResult:
    """Handle resource reading."""
    if assistant is None:
        return ReadResourceResult(
            contents=[TextContent(type="text", text="Error: Git Assistant is not initialized")]
        )
    
    try:
        if uri == "git://current-status":
            result = await assistant.get_repository_status()
            return ReadResourceResult(
                contents=[TextContent(
                    type="text", 
                    text=json.dumps(result, indent=2)
                )]
            )
        
        elif uri == "git://system-info":
            result = assistant.get_system_info()
            return ReadResourceResult(
                contents=[TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
            )
        
        else:
            return ReadResourceResult(
                contents=[TextContent(type="text", text=f"Error: Unknown resource URI '{uri}'")]
            )
    
    except Exception as e:
        logger.error(f"Error reading resource {uri}: {e}")
        return ReadResourceResult(
            contents=[TextContent(type="text", text=f"Error: {str(e)}")]
        )

def format_git_response(result: Dict[str, Any]) -> str:
    """Format git command response for display."""
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        f"🤖 **Git Command Generated:** `{result.get('generated_command', 'N/A')}`",
        f"📝 **Explanation:** {result.get('explanation', 'N/A')}",
        ""
    ]
    
    execution_result = result.get("execution_result", {})
    if execution_result.get("executed"):
        if execution_result.get("success"):
            response.append("✅ **Execution Result:** Command executed successfully")
            if execution_result.get("stdout"):
                response.append("```")
                response.append(execution_result["stdout"])
                response.append("```")
        else:
            response.append("❌ **Execution Result:** Command failed")
            if execution_result.get("stderr"):
                response.append("```")
                response.append(execution_result["stderr"])
                response.append("```")
    else:
        response.append("⏸️ **Execution Result:** Command not executed")
        if execution_result.get("reason"):
            response.append(f"**Reason:** {execution_result['reason']}")
    
    alternatives = result.get("alternatives", [])
    if alternatives:
        response.append("")
        response.append("💡 **Alternative approaches:**")
        for i, alt in enumerate(alternatives, 1):
            response.append(f"{i}. {alt}")
    
    return "\n".join(response)

def format_status_response(result: Dict[str, Any]) -> str:
    """Format repository status response for display."""
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        "📁 **Repository Status**",
        f"**Path:** {result.get('repository_path', 'N/A')}",
        f"**Current Branch:** {result.get('current_branch', 'N/A')}",
        f"**Status:** {result.get('status_summary', 'N/A')}",
        "",
        "📊 **File Counts:**"
    ]
    
    file_counts = result.get("file_counts", {})
    response.extend([
        f"- Modified: {file_counts.get('modified', 0)}",
        f"- Staged: {file_counts.get('staged', 0)}",
        f"- Untracked: {file_counts.get('untracked', 0)}",
        f"- Total: {file_counts.get('total', 0)}"
    ])
    
    special_states = result.get("special_states", {})
    states = []
    if special_states.get("has_conflicts"):
        states.append("⚠️ Has conflicts")
    if special_states.get("is_merging"):
        states.append("🔀 Merging")
    if special_states.get("is_rebasing"):
        states.append("🔄 Rebasing")
    if special_states.get("is_detached_head"):
        states.append("🔗 Detached HEAD")
    
    if states:
        response.append("")
        response.append("🚨 **Special States:**")
        for state in states:
            response.append(f"- {state}")
    
    return "\n".join(response)

def format_explanation_response(result: Dict[str, Any]) -> str:
    """Format command explanation response for display."""
    if not result.get("success"):
        return f"❌ Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        f"💻 **Command:** `{result.get('command', 'N/A')}`",
        f"📖 **Explanation:** {result.get('explanation', 'N/A')}"
    ]
    
    if result.get("reply"):
        response.insert(0, f"💬 **Summary:** {result['reply']}")
        response.insert(1, "")
    
    return "\n".join(response)

async def main():
    """Main entry point for the MCP stdio server."""
    try:
        # Initialize the assistant
        await initialize_assistant()
        
        # Run the stdio server
        async with stdio_server() as (read_stream, write_stream):
            await server.run(
                read_stream,
                write_stream,
                server.create_initialization_options()
            )
    except Exception as e:
        logger.error(f"Server error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())