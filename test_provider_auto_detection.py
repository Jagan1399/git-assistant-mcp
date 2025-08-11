#!/usr/bin/env python3
"""
Test script for LLM Provider Auto-Detection

This script demonstrates how the system automatically detects and selects
the appropriate LLM provider based on available API keys.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from git_assistant_mcp.config.settings import get_settings
from git_assistant_mcp.llm import get_provider_factory, get_llm_provider


def test_provider_auto_detection():
    """Test the provider auto-detection functionality."""
    print("🚀 Testing LLM Provider Auto-Detection")
    print("=" * 50)
    
    # Get settings
    try:
        settings = get_settings()
        print(f"✅ Settings loaded successfully")
        print(f"📋 Current LLM provider setting: {settings.llm_provider}")
    except Exception as e:
        print(f"❌ Failed to load settings: {e}")
        return
    
    # Test auto-detection
    try:
        detected_provider = settings.auto_detect_provider()
        print(f"🔍 Auto-detected provider: {detected_provider}")
    except Exception as e:
        print(f"❌ Auto-detection failed: {e}")
        return
    
    # Test provider factory
    try:
        factory = get_provider_factory(settings)
        print(f"🏭 Provider factory initialized successfully")
        
        # List all providers and their status
        print("\n📊 Provider Status:")
        print("-" * 30)
        provider_status = factory.list_providers()
        
        for provider_name, status in provider_status.items():
            status_icon = "✅" if status["available"] else "❌"
            print(f"{status_icon} {provider_name}: {status['status']}")
            
            if status["available"] and status["model_info"]:
                model_info = status["model_info"]
                print(f"   └─ Model: {model_info.get('model_name', 'Unknown')}")
                print(f"   └─ Max Tokens: {model_info.get('max_tokens', 'Unknown')}")
                print(f"   └─ Temperature: {model_info.get('temperature', 'Unknown')}")
        
        # Get the active provider
        print(f"\n🎯 Active Provider Selection:")
        print("-" * 30)
        
        try:
            active_provider = factory.get_provider()
            provider_info = active_provider.get_model_info()
            print(f"✅ Selected provider: {provider_info['provider']}")
            print(f"   └─ Model: {provider_info['model_name']}")
            print(f"   └─ Max Tokens: {provider_info['max_tokens']}")
            print(f"   └─ Temperature: {provider_info['temperature']}")
            
            # Test provider availability
            if active_provider.is_available():
                print(f"   └─ Status: Available ✅")
            else:
                print(f"   └─ Status: Not Available ❌")
                
        except Exception as e:
            print(f"❌ Failed to get active provider: {e}")
        
        # Test forcing a specific provider
        print(f"\n🔧 Testing Provider Override:")
        print("-" * 30)
        
        # Try to force each available provider
        for provider_name, status in provider_status.items():
            if status["available"]:
                try:
                    forced_provider = factory.get_provider(force_provider=provider_name)
                    provider_info = forced_provider.get_model_info()
                    print(f"✅ Forced {provider_name} provider: {provider_info['model_name']}")
                except Exception as e:
                    print(f"❌ Failed to force {provider_name} provider: {e}")
        
    except Exception as e:
        print(f"❌ Provider factory test failed: {e}")
        return
    
    print(f"\n🎉 Provider auto-detection test completed successfully!")


async def test_provider_response():
    """Test that a provider can actually generate responses."""
    print(f"\n🧪 Testing Provider Response Generation")
    print("=" * 50)
    
    try:
        settings = get_settings()
        provider = get_llm_provider(settings)
        
        print(f"✅ Got provider: {provider.get_model_info()['provider']}")
        
        # Test with a simple prompt
        test_prompt = """
        You are a Git assistant. The user wants to check the status of their repository.
        Please provide a response in the following JSON format:
        {
            "reply": "I'll help you check the Git status",
            "command": "git status",
            "explanation": "This command shows the current status of your working directory and staging area",
            "is_destructive": false
        }
        """
        
        print(f"📝 Testing with prompt: {test_prompt[:100]}...")
        
        # Note: This will fail if no actual API key is configured
        # but it tests that the provider interface works
        try:
            response = await provider.generate_response(test_prompt, {})
            print(f"✅ Response generated successfully!")
            print(f"   └─ Reply: {response.reply}")
            print(f"   └─ Command: {response.command}")
            print(f"   └─ Explanation: {response.explanation}")
        except Exception as e:
            print(f"⚠️  Response generation failed (expected without API key): {e}")
            print(f"   └─ This is normal if no valid API key is configured")
        
    except Exception as e:
        print(f"❌ Provider response test failed: {e}")


def main():
    """Main test function."""
    print("🎯 LLM Provider Auto-Detection Test Suite")
    print("=" * 60)
    
    # Test 1: Auto-detection
    test_provider_auto_detection()
    
    # Test 2: Provider response (async)
    asyncio.run(test_provider_response())
    
    print(f"\n🏁 All tests completed!")
    print(f"💡 Tip: Configure API keys in your .env file to test actual API calls")


if __name__ == "__main__":
    main()
