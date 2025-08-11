import uvicorn
from fastapi import FastAPI, Request, HTTPException
from pydantic import BaseModel
import asyncio
from mcp.types import InitializeRequest, InitializeResult

# Assuming the refactored mcp_wrapper is in core
from .core.mcp_wrapper import create_git_assistant, GitAssistantMCP

# Define the request body model
class McpRequest(BaseModel):
    user_request: str

app = FastAPI()



# Create a long-lived assistant instance
try:
    assistant = create_git_assistant()
except Exception as e:
    # If creation fails, log it and set assistant to None
    print(f"Error creating GitAssistantMCP instance: {e}")
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
            print("GitAssistantMCP instance created successfully on startup.")
        except Exception as e:
            print(f"Failed to create GitAssistantMCP instance on startup: {e}")
            # The application will run, but the /mcp endpoint will fail.
            # This can be handled in the endpoint logic.

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

def start_server():
    """
    Function to run the Uvicorn server.
    This can be called from a __main__ block or a separate run script.
    """
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    print("Starting Git Assistant MCP Server...")
    start_server()
