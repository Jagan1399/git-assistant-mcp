#!/usr/bin/env python3
"""
Test script for Git Assistant MCP Wrapper

This script demonstrates the complete end-to-end functionality of the
Git Assistant MCP system, including natural language processing,
Git state analysis, and command execution.
"""

import asyncio
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from git_assistant_mcp.core import create_git_assistant
from git_assistant_mcp.config.settings import get_settings


async def test_mcp_wrapper():
    """Test the MCP wrapper functionality."""
    print("🚀 Testing Git Assistant MCP Wrapper")
    print("=" * 60)
    
    try:
        # Create Git Assistant instance
        print("🔧 Initializing Git Assistant MCP...")
        assistant = create_git_assistant()
        print(f"✅ Git Assistant initialized for: {assistant.repo_path}")
        
        # Test 1: Get system information
        print(f"\n📊 System Information:")
        print("-" * 30)
        system_info = assistant.get_system_info()
        if system_info["success"]:
            print(f"✅ System: {system_info['system']['name']} v{system_info['system']['version']}")
            print(f"✅ Repository: {system_info['system']['repository_path']}")
            print(f"✅ Safe Mode: {system_info['system']['safe_mode']}")
            print(f"✅ Require Confirmation: {system_info['system']['require_confirmation']}")
            
            if system_info["llm_provider"]:
                llm_info = system_info["llm_provider"]
                print(f"✅ LLM Provider: {llm_info['provider']}")
                print(f"✅ Model: {llm_info['model_name']}")
        else:
            print(f"❌ Failed to get system info: {system_info['error']}")
        
        # Test 2: Get repository status
        print(f"\n📋 Repository Status:")
        print("-" * 30)
        status = await assistant.get_repository_status()
        if status["success"]:
            print(f"✅ Repository: {status['repository_path']}")
            print(f"✅ Current Branch: {status['current_branch']}")
            print(f"✅ Status: {status['status_summary']}")
            
            file_counts = status["file_counts"]
            print(f"✅ Files: {file_counts['modified']} modified, {file_counts['staged']} staged, {file_counts['untracked']} untracked")
            
            special_states = status["special_states"]
            if any(special_states.values()):
                print("⚠️  Special States:")
                for state, value in special_states.items():
                    if value:
                        print(f"   - {state}: {value}")
        else:
            print(f"❌ Failed to get repository status: {status['error']}")
        
        # Test 3: Process natural language requests
        print(f"\n🧠 Natural Language Processing:")
        print("-" * 30)
        
        test_requests = [
            "Show me the current status of my repository",
            "What files have I modified?",
            "Stage all my changes",
            "Create a commit with the message 'Update documentation'",
            "Show me the recent commit history"
        ]
        
        for i, request in enumerate(test_requests, 1):
            print(f"\n📝 Test {i}: {request}")
            print("-" * 40)
            
            try:
                # Process the request
                print(f"🔄 Processing request...")
                response = await assistant.process_request(request)
                
                if response["success"]:
                    print(f"✅ Success!")
                    print(f"   └─ Generated Command: {response['generated_command']}")
                    print(f"   └─ Explanation: {response['explanation']}")
                    
                    if response.get("execution_result"):
                        exec_result = response["execution_result"]
                        if exec_result["executed"]:
                            if exec_result["success"]:
                                print(f"   └─ Execution: ✅ Success")
                                if exec_result.get("stdout"):
                                    print(f"   └─ Output: {exec_result['stdout'][:100]}...")
                            else:
                                print(f"   └─ Execution: ❌ Failed")
                                if exec_result.get("stderr"):
                                    print(f"   └─ Error: {exec_result['stderr']}")
                        else:
                            print(f"   └─ Execution: ⏸️  Not executed")
                            print(f"   └─ Reason: {exec_result.get('reason', 'Unknown')}")
                    
                    if response.get("alternatives"):
                        print(f"   └─ Alternatives: {len(response['alternatives'])} options available")
                    
                    if response.get("confidence"):
                        print(f"   └─ Confidence: {response['confidence']:.2f}")
                        
                else:
                    print(f"❌ Failed: {response.get('error', 'Unknown error')}")
                    
            except Exception as e:
                print(f"❌ Error processing request: {str(e)}")
        
        # Test 4: Command explanation
        print(f"\n📚 Command Explanation:")
        print("-" * 30)
        
        test_commands = [
            "git status",
            "git add .",
            "git commit -m 'Update'",
            "git push origin main",
            "git reset --hard HEAD~1"
        ]
        
        for command in test_commands:
            print(f"\n🔍 Explaining: {command}")
            try:
                explanation = await assistant.explain_command(command)
                if explanation["success"]:
                    print(f"✅ Explanation: {explanation['explanation'][:100]}...")
                else:
                    print(f"❌ Failed: {explanation.get('error', 'Unknown error')}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        
        print(f"\n🎉 MCP Wrapper test completed successfully!")
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()


async def test_specific_scenario():
    """Test a specific Git scenario."""
    print(f"\n🎯 Testing Specific Git Scenario")
    print("=" * 50)
    
    try:
        assistant = create_git_assistant()
        
        # Test a realistic Git workflow
        print("🔄 Testing Git workflow: Check status → Stage changes → Commit")
        
        # Step 1: Check status
        print(f"\n📋 Step 1: Check repository status")
        response1 = await assistant.process_request("Show me the current status of my repository")
        print(f"✅ Status check: {response1['success']}")
        
        # Step 2: Stage changes (if any)
        print(f"\n📦 Step 2: Stage any changes")
        response2 = await assistant.process_request("Stage all my changes")
        print(f"✅ Stage changes: {response2['success']}")
        
        # Step 3: Create commit (if there are staged changes)
        print(f"\n💾 Step 3: Create commit")
        response3 = await assistant.process_request("Create a commit with the message 'Update from Git Assistant'")
        print(f"✅ Create commit: {response3['success']}")
        
        print(f"\n🎉 Git workflow test completed!")
        
    except Exception as e:
        print(f"❌ Scenario test failed: {str(e)}")


def main():
    """Main test function."""
    print("🎯 Git Assistant MCP Wrapper Test Suite")
    print("=" * 70)
    
    # Test 1: Basic functionality
    asyncio.run(test_mcp_wrapper())
    
    # Test 2: Specific scenario
    asyncio.run(test_specific_scenario())
    
    print(f"\n🏁 All tests completed!")
    print(f"💡 The MCP Wrapper is now ready to coordinate all Git operations!")
    print(f"🚀 Next step: Implement Prompt Templates for better LLM responses")


if __name__ == "__main__":
    main()
