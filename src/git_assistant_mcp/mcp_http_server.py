"""
Simple MCP HTTP Server implementation using standard MCP HTTP transport.
"""

import uvicorn
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import json
import asyncio
import logging
from typing import Dict, Any

from .core.mcp_wrapper import create_git_assistant

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Git Assistant MCP HTTP Server",
    description="MCP HTTP transport for Git Assistant",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create assistant instance
try:
    assistant = create_git_assistant()
    logger.info("GitAssistantMCP instance created successfully")
except Exception as e:
    logger.error(f"Error creating GitAssistantMCP instance: {e}")
    assistant = None

@app.get("/sse")
async def mcp_sse_endpoint(request: Request):
    """
    MCP Server-Sent Events endpoint.
    This implements the MCP HTTP transport protocol.
    """
    async def event_stream():
        try:
            logger.info("SSE connection established")
            
            # Send initial server info
            server_info = {
                "jsonrpc": "2.0",
                "method": "notifications/initialized",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {
                        "tools": {},
                        "resources": {}
                    },
                    "serverInfo": {
                        "name": "git-assistant-mcp",
                        "version": "1.0.0"
                    }
                }
            }
            yield f"data: {json.dumps(server_info)}\n\n"
            
            # Keep connection alive and handle incoming messages
            while True:
                await asyncio.sleep(1)
                # In a real implementation, you'd handle incoming JSON-RPC messages here
                # For now, just keep the connection alive
                
        except asyncio.CancelledError:
            logger.info("SSE connection cancelled")
            return
        except Exception as e:
            logger.error(f"SSE error: {e}")
            return
    
    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
            "Access-Control-Allow-Headers": "*",
        }
    )

@app.post("/message")
async def handle_mcp_message(request: Request):
    """
    Handle MCP JSON-RPC messages.
    """
    try:
        body = await request.body()
        if not body:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
        
        try:
            message = json.loads(body.decode())
        except json.JSONDecodeError:
            return {"jsonrpc": "2.0", "error": {"code": -32700, "message": "Parse error"}}
        
        # Handle different MCP methods
        method = message.get("method")
        params = message.get("params", {})
        msg_id = message.get("id")
        
        if assistant is None:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32603, "message": "Internal error", "data": "Assistant not available"}
            }
        
        if method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {},
                    "resources": {}
                },
                "serverInfo": {
                    "name": "git-assistant-mcp",
                    "version": "1.0.0"
                }
            }
            return {"jsonrpc": "2.0", "id": msg_id, "result": result}
        
        elif method == "tools/list":
            tools = [
                {
                    "name": "process_git_request",
                    "description": "Process natural language Git requests",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "request": {"type": "string", "description": "Git request in natural language"}
                        },
                        "required": ["request"]
                    }
                },
                {
                    "name": "get_git_status",
                    "description": "Get current Git repository status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "detailed": {"type": "boolean", "description": "Include detailed information"}
                        }
                    }
                }
            ]
            return {"jsonrpc": "2.0", "id": msg_id, "result": {"tools": tools}}
        
        elif method == "tools/call":
            tool_name = params.get("name")
            tool_args = params.get("arguments", {})
            
            if tool_name == "process_git_request":
                request_text = tool_args.get("request", "")
                result = await assistant.process_request(request_text)
                
                # Format response for MCP
                content = []
                if result.get("success"):
                    text = f"**Command:** `{result.get('generated_command', 'N/A')}`\n"
                    text += f"**Explanation:** {result.get('explanation', 'N/A')}\n"
                    
                    exec_result = result.get("execution_result", {})
                    if exec_result.get("executed"):
                        if exec_result.get("success"):
                            text += "**Result:** ✅ Success\n"
                            if exec_result.get("stdout"):
                                text += f"```\n{exec_result['stdout']}\n```"
                        else:
                            text += "**Result:** ❌ Failed\n"
                            if exec_result.get("stderr"):
                                text += f"```\n{exec_result['stderr']}\n```"
                    else:
                        text += "**Result:** Command not executed\n"
                        if exec_result.get("reason"):
                            text += f"**Reason:** {exec_result['reason']}"
                    
                    content.append({"type": "text", "text": text})
                else:
                    content.append({"type": "text", "text": f"Error: {result.get('error', 'Unknown error')}"})
                
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": content}}
            
            elif tool_name == "get_git_status":
                result = await assistant.get_repository_status()
                
                if result.get("success"):
                    text = f"**Repository:** {result.get('repository_path', 'N/A')}\n"
                    text += f"**Branch:** {result.get('current_branch', 'N/A')}\n"
                    text += f"**Status:** {result.get('status_summary', 'N/A')}\n"
                    
                    file_counts = result.get("file_counts", {})
                    text += f"**Files:** {file_counts.get('modified', 0)} modified, "
                    text += f"{file_counts.get('staged', 0)} staged, "
                    text += f"{file_counts.get('untracked', 0)} untracked"
                    
                    content = [{"type": "text", "text": text}]
                else:
                    content = [{"type": "text", "text": f"Error: {result.get('error', 'Unknown error')}"}]
                
                return {"jsonrpc": "2.0", "id": msg_id, "result": {"content": content}}
            
            else:
                return {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "error": {"code": -32601, "message": f"Unknown tool: {tool_name}"}
                }
        
        else:
            return {
                "jsonrpc": "2.0",
                "id": msg_id,
                "error": {"code": -32601, "message": f"Unknown method: {method}"}
            }
    
    except Exception as e:
        logger.error(f"Error handling MCP message: {e}")
        return {
            "jsonrpc": "2.0",
            "id": message.get("id") if 'message' in locals() else None,
            "error": {"code": -32603, "message": "Internal error", "data": str(e)}
        }

def start_mcp_http_server():
    """Start the MCP HTTP server."""
    uvicorn.run(app, host="0.0.0.0", port=8001)

if __name__ == "__main__":
    print("Starting Git Assistant MCP HTTP Server...")
    start_mcp_http_server()