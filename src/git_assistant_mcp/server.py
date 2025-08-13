import uvicorn
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional, Union
import asyncio
import json
import logging

# Assuming the refactored mcp_wrapper is in core
from .core.mcp_wrapper import create_git_assistant, GitAssistantMCP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define the request body models
class McpRequest(BaseModel):
    user_request: str

class JsonRpcRequest(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: Union[str, int, None] = None
    method: str
    params: Optional[Dict[str, Any]] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = Field(default="2.0")
    id: Union[str, int, None] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[Dict[str, Any]] = None

class JsonRpcError(BaseModel):
    code: int
    message: str
    data: Optional[Any] = None

app = FastAPI(
    title="Git Assistant MCP Server",
    description="AI-powered Git assistant supporting both HTTP and MCP protocols",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

# Create a long-lived assistant instance
try:
    assistant = create_git_assistant()
    logger.info("GitAssistantMCP instance created successfully")
except Exception as e:
    logger.error(f"Error creating GitAssistantMCP instance: {e}")
    assistant = None

@app.on_event("startup")
async def startup_event():
    """
    On startup, ensure the assistant is ready.
    """
    global assistant
    if assistant is None:
        try:
            assistant = create_git_assistant()
            logger.info("GitAssistantMCP instance created successfully on startup.")
        except Exception as e:
            logger.error(f"Failed to create GitAssistantMCP instance on startup: {e}")

# HTTP API Endpoints (Original functionality)
@app.get("/mcp")
async def get_mcp_info(request: Request):
    """
    The GET endpoint for MCP to discover tools and resources.
    """
    if assistant is None:
        raise HTTPException(status_code=500, detail="Git Assistant is not available due to an initialization error.")
    
    # Return the server's manifest
    return assistant.get_manifest()

@app.post("/mcp")
async def process_mcp_request(request: McpRequest):
    """
    The main MCP endpoint for processing user requests.
    """
    if assistant is None:
        raise HTTPException(status_code=500, detail="Git Assistant is not available due to an initialization error.")

    try:
        # Use the process_request method from the assistant
        response = await assistant.process_request(request.user_request)
        return response
    except Exception as e:
        # Handle potential errors during request processing
        raise HTTPException(status_code=500, detail=f"An error occurred while processing your request: {e}")

@app.get("/status")
async def get_status():
    """
    An endpoint to check the status of the MCP server and the Git Assistant.
    """
    if assistant is None:
        return {"status": "error", "message": "Git Assistant failed to initialize."}
    
    try:
        # You might want to add a dedicated status method to your assistant
        repo_status = await assistant.get_repository_status()
        return {
            "status": "ok",
            "message": "Git Assistant is running.",
            "repository_status": repo_status
        }
    except Exception as e:
        return {"status": "error", "message": f"Git Assistant is running, but failed to get repository status: {e}"}

# MCP Protocol Endpoints (JSON-RPC 2.0)
@app.get("/mcp/rpc")
async def get_mcp_rpc_info():
    """
    GET endpoint for MCP RPC information and testing.
    """
    return {
        "message": "Git Assistant MCP JSON-RPC 2.0 Endpoint",
        "version": "2.0",
        "methods": [
            "initialize",
            "tools/list",
            "tools/call",
            "resources/list",
            "resources/read"
        ],
        "example_request": {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "tools/list",
            "params": {}
        },
        "usage": "Send POST requests with JSON-RPC 2.0 format to this endpoint"
    }

@app.get("/mcp/sse")
@app.post("/mcp/sse")
async def handle_mcp_sse(request: Request):
    """
    Handle MCP Server-Sent Events (SSE) requests.
    This is the proper MCP HTTP transport protocol.
    Supports both GET (for connection establishment) and POST (for requests).
    """
    if request.method == "GET":
        # Handle GET request for SSE connection establishment
        async def event_stream():
            # Send initial connection message
            init_response = {
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
            yield f"data: {json.dumps(init_response)}\n\n"
            
            # Keep connection alive
            while True:
                await asyncio.sleep(30)  # Send keepalive every 30 seconds
                yield f"data: {json.dumps({'type': 'keepalive'})}\n\n"
        
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
    async def event_stream():
        try:
            # Read the request body
            body = await request.body()
            if not body:
                error_response = JsonRpcResponse(
                    error=JsonRpcError(
                        code=-32700,
                        message="Parse error - empty request body"
                    ).dict()
                )
                yield f"data: {error_response.json()}\n\n"
                return
            
            # Parse JSON-RPC request
            try:
                request_data = json.loads(body.decode())
                rpc_request = JsonRpcRequest(**request_data)
            except (json.JSONDecodeError, Exception) as e:
                error_response = JsonRpcResponse(
                    error=JsonRpcError(
                        code=-32700,
                        message=f"Parse error: {str(e)}"
                    ).dict()
                )
                yield f"data: {error_response.json()}\n\n"
                return
            
            # Process the request
            if assistant is None:
                error_response = JsonRpcResponse(
                    id=rpc_request.id,
                    error=JsonRpcError(
                        code=-32603,
                        message="Internal error",
                        data="Git Assistant is not available"
                    ).dict()
                )
                yield f"data: {error_response.json()}\n\n"
                return
            
            try:
                result = await process_mcp_method(rpc_request.method, rpc_request.params or {})
                response = JsonRpcResponse(id=rpc_request.id, result=result)
                yield f"data: {response.json()}\n\n"
            except Exception as e:
                logger.error(f"Error processing MCP SSE request: {e}")
                error_response = JsonRpcResponse(
                    id=rpc_request.id,
                    error=JsonRpcError(
                        code=-32603,
                        message="Internal error",
                        data=str(e)
                    ).dict()
                )
                yield f"data: {error_response.json()}\n\n"
                
        except Exception as e:
            logger.error(f"SSE stream error: {e}")
            error_response = JsonRpcResponse(
                error=JsonRpcError(
                    code=-32603,
                    message="Internal error",
                    data=str(e)
                ).dict()
            )
            yield f"data: {error_response.json()}\n\n"
    
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

@app.post("/mcp/rpc")
async def handle_mcp_rpc(request: JsonRpcRequest):
    """
    Handle MCP JSON-RPC 2.0 requests.
    """
    if assistant is None:
        return JsonRpcResponse(
            id=request.id,
            error=JsonRpcError(
                code=-32603,
                message="Internal error",
                data="Git Assistant is not available due to an initialization error."
            ).dict()
        )

    try:
        result = await process_mcp_method(request.method, request.params or {})
        return JsonRpcResponse(id=request.id, result=result)
    except Exception as e:
        logger.error(f"Error processing MCP RPC request: {e}")
        return JsonRpcResponse(
            id=request.id,
            error=JsonRpcError(
                code=-32603,
                message="Internal error",
                data=str(e)
            ).dict()
        )

async def process_mcp_method(method: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process MCP method calls.
    """
    logger.debug(f"process_mcp_method called with method={method!r}, params={params!r} (types: {type(params)})")
    if method == "initialize":
        return {
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
    
    elif method == "tools/list":
        return {
            "tools": [
                {
                    "name": "process_git_request",
                    "description": "Process natural language Git requests and execute commands",
                    "inputSchema": {
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
                },
                {
                    "name": "get_git_status",
                    "description": "Get current Git repository status",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "detailed": {
                                "type": "boolean",
                                "description": "Include detailed file information",
                                "default": False
                            }
                        }
                    }
                },
                {
                    "name": "explain_git_command",
                    "description": "Explain what a Git command does",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": "Git command to explain"
                            }
                        },
                        "required": ["command"]
                    }
                }
            ]
        }
    
    elif method == "tools/call":
        tool_name = params.get("name")
        tool_arguments = params.get("arguments", {})
        logger.debug(f"tools/call: tool_name={tool_name!r}, tool_arguments={tool_arguments!r} (types: {type(tool_arguments)})")
        
        if tool_name == "process_git_request":
            request_text = tool_arguments.get("request", "")
            logger.debug(f"process_git_request: request_text={request_text!r} (type: {type(request_text)})")
            result = await assistant.process_request(request_text)
            logger.debug(f"process_git_request result: {result!r} (type: {type(result)})")
            formatted = format_git_response(result)
            logger.debug(f"process_git_request formatted: {formatted!r} (type: {type(formatted)})")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": formatted
                    }
                ]
            }
        
        elif tool_name == "get_git_status":
            logger.debug("get_git_status called")
            result = await assistant.get_repository_status()
            logger.debug(f"get_git_status result: {result!r} (type: {type(result)})")
            formatted = format_status_response(result)
            logger.debug(f"get_git_status formatted: {formatted!r} (type: {type(formatted)})")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": formatted
                    }
                ]
            }
        
        elif tool_name == "explain_git_command":
            command = tool_arguments.get("command", "")
            logger.debug(f"explain_git_command: command={command!r} (type: {type(command)})")
            result = await assistant.explain_command(command)
            logger.debug(f"explain_git_command result: {result!r} (type: {type(result)})")
            formatted = format_explanation_response(result)
            logger.debug(f"explain_git_command formatted: {formatted!r} (type: {type(formatted)})")
            return {
                "content": [
                    {
                        "type": "text",
                        "text": formatted
                    }
                ]
            }
        
        else:
            logger.error(f"Unknown tool called: {tool_name!r}")
            raise ValueError(f"Unknown tool: {tool_name}")
    
    elif method == "resources/list":
        return {
            "resources": [
                {
                    "uri": "git://current-status",
                    "name": "Current Git Status",
                    "description": "Current status of the Git repository",
                    "mimeType": "application/json"
                },
                {
                    "uri": "git://system-info",
                    "name": "System Information",
                    "description": "Information about the Git Assistant system",
                    "mimeType": "application/json"
                }
            ]
        }
    
    elif method == "resources/read":
        uri = params.get("uri", "")
        logger.debug(f"resources/read: uri={uri!r} (type: {type(uri)})")
        
        if uri == "git://current-status":
            result = await assistant.get_repository_status()
            logger.debug(f"resources/read current-status result: {result!r} (type: {type(result)})")
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        elif uri == "git://system-info":
            result = assistant.get_system_info()
            logger.debug(f"resources/read system-info result: {result!r} (type: {type(result)})")
            return {
                "contents": [
                    {
                        "uri": uri,
                        "mimeType": "application/json",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
        
        else:
            logger.error(f"Unknown resource URI called: {uri!r}")
            raise ValueError(f"Unknown resource URI: {uri}")
    
    else:
        raise ValueError(f"Unknown method: {method}")

def format_git_response(result: Dict[str, Any]) -> str:
    """Format git command response for display."""
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        f"**Git Command Generated:** `{result.get('generated_command', 'N/A')}`",
        f"**Explanation:** {result.get('explanation', 'N/A')}",
        ""
    ]
    
    execution_result = result.get("execution_result", {})
    if execution_result.get("executed"):
        if execution_result.get("success"):
            response.append("**Execution Result:** ✅ Command executed successfully")
            if execution_result.get("stdout"):
                response.append("```")
                response.append(execution_result["stdout"])
                response.append("```")
        else:
            response.append("**Execution Result:** ❌ Command failed")
            if execution_result.get("stderr"):
                response.append("```")
                response.append(execution_result["stderr"])
                response.append("```")
    else:
        response.append("**Execution Result:** Command not executed")
        if execution_result.get("reason"):
            response.append(f"**Reason:** {execution_result['reason']}")
    
    alternatives = result.get("alternatives", [])
    if alternatives:
        response.append("")
        response.append("**Alternative approaches:**")
        for i, alt in enumerate(alternatives, 1):
            response.append(f"{i}. {alt}")
    
    return "\n".join(response)

def format_status_response(result: Dict[str, Any]) -> str:
    """Format repository status response for display."""
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        "**Repository Status**",
        f"**Path:** {result.get('repository_path', 'N/A')}",
        f"**Current Branch:** {result.get('current_branch', 'N/A')}",
        f"**Status:** {result.get('status_summary', 'N/A')}",
        "",
        "**File Counts:**"
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
        states.append("Has conflicts")
    if special_states.get("is_merging"):
        states.append("Merging")
    if special_states.get("is_rebasing"):
        states.append("Rebasing")
    if special_states.get("is_detached_head"):
        states.append("Detached HEAD")
    
    if states:
        response.append("")
        response.append("**Special States:**")
        for state in states:
            response.append(f"- {state}")
    
    return "\n".join(response)

def format_explanation_response(result: Dict[str, Any]) -> str:
    """Format command explanation response for display."""
    if not result.get("success"):
        return f"Error: {result.get('error', 'Unknown error occurred')}"
    
    response = [
        f"**Command:** `{result.get('command', 'N/A')}`",
        f"**Explanation:** {result.get('explanation', 'N/A')}"
    ]
    
    if result.get("reply"):
        response.insert(0, f"**Summary:** {result['reply']}")
        response.insert(1, "")
    
    return "\n".join(response)

# WebSocket endpoint for real-time MCP communication
@app.websocket("/mcp/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for MCP communication.
    """
    await websocket.accept()
    logger.info("WebSocket connection established")
    
    try:
        while True:
            # Receive JSON-RPC message
            data = await websocket.receive_text()
            try:
                request_data = json.loads(data)
                request = JsonRpcRequest(**request_data)
                
                # Process the request
                if assistant is None:
                    response = JsonRpcResponse(
                        id=request.id,
                        error=JsonRpcError(
                            code=-32603,
                            message="Internal error",
                            data="Git Assistant is not available"
                        ).dict()
                    )
                else:
                    try:
                        result = await process_mcp_method(request.method, request.params or {})
                        response = JsonRpcResponse(id=request.id, result=result)
                    except Exception as e:
                        logger.error(f"Error processing WebSocket MCP request: {e}")
                        response = JsonRpcResponse(
                            id=request.id,
                            error=JsonRpcError(
                                code=-32603,
                                message="Internal error",
                                data=str(e)
                            ).dict()
                        )
                
                # Send response
                await websocket.send_text(response.json())
                
            except json.JSONDecodeError:
                error_response = JsonRpcResponse(
                    error=JsonRpcError(
                        code=-32700,
                        message="Parse error"
                    ).dict()
                )
                await websocket.send_text(error_response.json())
            except Exception as e:
                logger.error(f"WebSocket error: {e}")
                error_response = JsonRpcResponse(
                    error=JsonRpcError(
                        code=-32603,
                        message="Internal error",
                        data=str(e)
                    ).dict()
                )
                await websocket.send_text(error_response.json())
                
    except Exception as e:
        logger.error(f"WebSocket connection error: {e}")
    finally:
        logger.info("WebSocket connection closed")

def start_server():
    """
    Function to run the Uvicorn server.
    This can be called from a __main__ block or a separate run script.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("Starting Git Assistant MCP Server with HTTP and MCP protocol support...")
    start_server()
