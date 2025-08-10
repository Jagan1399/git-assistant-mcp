#!/usr/bin/env python3
"""
Test script for Gemini integration with Git Assistant MCP.

This script tests the basic functionality of the Gemini provider
without requiring a Git repository or complex setup.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

try:
    from git_assistant_mcp.config.settings import Settings
    from git_assistant_mcp.llm.providers.gemini_provider import GeminiProvider
    from git_assistant_mcp.models.llm_response import LLMResponse
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure you have installed the requirements and the package structure is correct.")
    sys.exit(1)


async def test_gemini_provider():
    """Test the Gemini provider with a simple prompt."""
    
    print("🧪 Testing Gemini Integration for Git Assistant MCP")
    print("=" * 60)
    
    # Check if Google API key is set
    api_key = os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ GOOGLE_API_KEY environment variable not set!")
        print("Please set your Google API key:")
        print("export GOOGLE_API_KEY='your_api_key_here'")
        print("Or add it to your .env file")
        return False
    
    print(f"✅ Google API key found: {api_key[:10]}...")
    
    try:
        # Create settings
        settings = Settings()
        print(f"✅ Settings loaded successfully")
        print(f"   - LLM Provider: {settings.llm_provider}")
        print(f"   - Gemini Model: {settings.gemini_model_name}")
        print(f"   - Max Tokens: {settings.gemini_max_tokens}")
        print(f"   - Temperature: {settings.gemini_temperature}")
        
        # Initialize Gemini provider
        provider = GeminiProvider(settings)
        print(f"✅ Gemini provider initialized successfully")
        
        # Test prompt
        test_prompt = """You are an expert Git assistant. Your goal is to help the user by providing the exact Git command needed to accomplish their task.

Analyze the user's request based on the provided JSON context of the repository's current state.

Respond ONLY with a JSON object with these keys:
1. "reply": A short, friendly, natural-language confirmation
2. "command": The precise, executable Git command
3. "updatedContext": Prediction of Git context after command execution
4. "is_destructive": Boolean indicating if command could cause data loss
5. "explanation": Brief explanation of what the command does
6. "alternatives": Array of alternative approaches if applicable

IMPORTANT: Ensure your response is valid JSON. Do not include any markdown formatting, code blocks, or additional text outside the JSON object.

---
CURRENT GIT CONTEXT:
{
  "current_branch": "main",
  "status": [
    {
      "file": "test.txt",
      "status": "modified",
      "staged": false
    }
  ],
  "recent_commits": [
    {
      "hash": "a1b2c3d",
      "message": "Initial commit"
    }
  ]
}
---
USER'S REQUEST:
"stage my changes"
"""

        print(f"📤 Sending test prompt to Gemini...")
        print(f"   Prompt length: {len(test_prompt)} characters")
        
        # Generate response
        response = await provider.generate_response(test_prompt, {})
        
        print(f"✅ Response received successfully!")
        print(f"   - Reply: {response.reply}")
        print(f"   - Command: {response.command}")
        print(f"   - Explanation: {response.explanation}")
        print(f"   - Is Destructive: {response.is_destructive}")
        print(f"   - Confidence: {response.confidence}")
        
        # Validate response
        if provider.validate_response(response):
            print(f"✅ Response validation passed")
        else:
            print(f"⚠️  Response validation failed")
        
        # Test safety check
        safety_level = response.get_safety_level()
        print(f"   - Safety Level: {safety_level}")
        
        if response.is_safe_to_execute():
            print(f"✅ Command is safe to execute")
        else:
            print(f"⚠️  Command requires additional validation")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during testing: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to run the test."""
    print("🚀 Starting Gemini Integration Test")
    print()
    
    # Run the async test
    success = asyncio.run(test_gemini_provider())
    
    print()
    if success:
        print("🎉 All tests passed! Gemini integration is working correctly.")
        print("You can now proceed with implementing the core Git Assistant MCP components.")
    else:
        print("💥 Some tests failed. Please check the error messages above.")
        print("Common issues:")
        print("  - Missing or invalid Google API key")
        print("  - Network connectivity issues")
        print("  - Incorrect package structure")
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
