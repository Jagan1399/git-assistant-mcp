# LLM Provider Auto-Detection System

## 🎯 Overview

The Git Assistant MCP now features a sophisticated **auto-detection system** that automatically selects the appropriate LLM provider based on available API keys. This system ensures seamless operation regardless of whether you have Gemini, OpenAI, or other API keys configured.

## ✨ Key Features

### 🔍 **Automatic Provider Detection**
- **Smart Detection**: Automatically detects which LLM provider is available based on API keys
- **Priority-Based Selection**: Uses a configurable priority order (Gemini → OpenAI → Anthropic)
- **Fallback Support**: Gracefully falls back to alternative providers if the primary one fails

### 🏭 **Provider Factory Pattern**
- **Centralized Management**: Single factory class manages all provider instances
- **Lazy Initialization**: Providers are only created when needed
- **Dynamic Switching**: Can switch between providers at runtime
- **Error Handling**: Robust error handling with detailed logging

### 🔧 **Flexible Configuration**
- **Environment Variables**: Configure via `.env` file or environment variables
- **Auto-Detection**: Set `llm_provider=None` for automatic detection
- **Manual Override**: Force specific provider selection when needed
- **Runtime Updates**: Update provider settings without restarting

## 🚀 How It Works

### 1. **Configuration Loading**
```python
from git_assistant_mcp.config.settings import get_settings

settings = get_settings()
# Automatically loads from .env file or environment variables
```

### 2. **Provider Auto-Detection**
```python
# Auto-detect based on available API keys
detected_provider = settings.auto_detect_provider()
# Returns: "gemini", "openai", or "anthropic"

# Get the active provider (auto-detects if not specified)
active_provider = settings.get_active_provider()
```

### 3. **Provider Factory Usage**
```python
from git_assistant_mcp.llm import get_llm_provider, get_provider_factory

# Get the best available provider automatically
provider = get_llm_provider(settings)

# Or force a specific provider
provider = get_llm_provider(settings, force_provider="openai")

# Get provider factory for advanced operations
factory = get_provider_factory(settings)
```

## 📋 Supported Providers

### 🔸 **Google Gemini**
- **Model**: `gemini-1.5-flash`, `gemini-1.5-pro`, `gemini-2.0-flash-exp`
- **API Key**: `GOOGLE_API_KEY`
- **Priority**: 1 (highest)

### 🔸 **OpenAI**
- **Model**: `gpt-4`, `gpt-3.5-turbo`, `gpt-4-turbo`
- **API Key**: `OPENAI_API_KEY`
- **Priority**: 2

### 🔸 **Anthropic Claude**
- **Model**: `claude-3-sonnet-20240229`, `claude-3-haiku-20240307`
- **API Key**: `ANTHROPIC_API_KEY`
- **Priority**: 3

## 🛠️ Configuration

### **Environment Variables (.env file)**
```bash
# Gemini Configuration
GOOGLE_API_KEY=your_gemini_api_key_here
GEMINI_MODEL_NAME=gemini-1.5-flash
GEMINI_MAX_TOKENS=1000
GEMINI_TEMPERATURE=0.1

# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL_NAME=gpt-4
OPENAI_MAX_TOKENS=1000
OPENAI_TEMPERATURE=0.1

# Anthropic Configuration
ANTHROPIC_API_KEY=your_anthropic_api_key_here
ANTHROPIC_MODEL_NAME=claude-3-sonnet-20240229
ANTHROPIC_MAX_TOKENS=1000

# Provider Selection (optional - auto-detects if not set)
LLM_PROVIDER=gemini  # or "openai", "anthropic", or None for auto-detection
```

### **Priority Order**
The system automatically selects providers in this order:
1. **Gemini** (if `GOOGLE_API_KEY` is available)
2. **OpenAI** (if `OPENAI_API_KEY` is available)
3. **Anthropic** (if `ANTHROPIC_API_KEY` is available)

## 💻 Usage Examples

### **Basic Usage**
```python
from git_assistant_mcp.llm import get_llm_provider
from git_assistant_mcp.config.settings import get_settings

# Get settings and provider
settings = get_settings()
provider = get_llm_provider(settings)

# Use the provider
response = await provider.generate_response(prompt, context)
```

### **Advanced Usage**
```python
from git_assistant_mcp.llm import get_provider_factory

# Get factory for advanced operations
factory = get_provider_factory(settings)

# List all providers and their status
provider_status = factory.list_providers()
for name, status in provider_status.items():
    print(f"{name}: {'✅' if status['available'] else '❌'}")

# Force a specific provider
provider = factory.get_provider(force_provider="openai")

# Get current provider info
info = factory.get_current_provider_info()
print(f"Using: {info['provider_name']} with {info['model_name']}")
```

### **Provider Switching**
```python
# Switch providers at runtime
factory.refresh_provider()  # Forces re-evaluation of available providers

# Or force a specific provider
provider = factory.get_provider(force_provider="openai")
```

## 🔍 **Provider Status Monitoring**

### **Check Provider Availability**
```python
factory = get_provider_factory(settings)
status = factory.list_providers()

for provider_name, info in status.items():
    if info["available"]:
        print(f"✅ {provider_name}: {info['status']}")
        if info["model_info"]:
            print(f"   Model: {info['model_info']['model_name']}")
    else:
        print(f"❌ {provider_name}: {info['status']}")
```

### **Get Current Provider Info**
```python
provider = get_llm_provider(settings)
info = provider.get_model_info()

print(f"Provider: {info['provider']}")
print(f"Model: {info['model_name']}")
print(f"Max Tokens: {info['max_tokens']}")
print(f"Temperature: {info['temperature']}")
```

## 🧪 Testing

### **Run Auto-Detection Test**
```bash
python test_provider_auto_detection.py
```

This test script demonstrates:
- ✅ Settings loading and validation
- 🔍 Provider auto-detection
- 🏭 Provider factory functionality
- 📊 Provider status reporting
- 🔧 Provider override capabilities
- 🧪 Basic response generation (without API calls)

### **Expected Output**
```
🎯 LLM Provider Auto-Detection Test Suite
============================================================
🚀 Testing LLM Provider Auto-Detection
==================================================
✅ Settings loaded successfully
📋 Current LLM provider setting: gemini
🔍 Auto-detected provider: gemini
🏭 Provider factory initialized successfully

📊 Provider Status:
------------------------------
✅ gemini: Available
   └─ Model: gemini-1.5-flash
   └─ Max Tokens: 1000
   └─ Temperature: 0.1
❌ openai: Error: OpenAI API key is required

🎯 Active Provider Selection:
------------------------------
✅ Selected provider: gemini
   └─ Model: gemini-1.5-flash
   └─ Max Tokens: 1000
   └─ Temperature: 0.1
   └─ Status: Available ✅
```

## 🔧 **Troubleshooting**

### **Common Issues**

#### **1. No Providers Available**
```
RuntimeError: No LLM providers are available. Please check your API keys and configuration.
```
**Solution**: Ensure at least one API key is configured in your `.env` file.

#### **2. Provider Initialization Failed**
```
RuntimeError: Failed to initialize gemini provider: Google API key is required
```
**Solution**: Check that your API key environment variable is set correctly.

#### **3. Model Not Found**
```
404 models/gemini-pro is not found for API version v1beta
```
**Solution**: Update the model name to a valid one (e.g., `gemini-1.5-flash`).

### **Debug Mode**
Enable debug logging to see detailed provider selection information:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🚀 **Next Steps**

### **Immediate Benefits**
- ✅ **Seamless Operation**: Works with any available API key
- ✅ **Automatic Fallback**: No manual provider switching needed
- ✅ **Easy Configuration**: Just add your API keys to `.env`
- ✅ **Future-Proof**: Easy to add new providers

### **Future Enhancements**
- 🔮 **Local Models**: Support for local LLM models (Ollama, etc.)
- 🔮 **Provider Load Balancing**: Distribute requests across multiple providers
- 🔮 **Cost Optimization**: Automatically select most cost-effective provider
- 🔮 **Performance Monitoring**: Track response times and success rates

## 📚 **Architecture Details**

### **Class Hierarchy**
```
BaseLLMProvider (ABC)
├── GeminiProvider
├── OpenAIProvider
└── AnthropicProvider (future)

LLMProviderFactory
├── Provider selection logic
├── Availability checking
└── Instance management
```

### **Key Design Patterns**
- **Factory Pattern**: Centralized provider creation and management
- **Strategy Pattern**: Interchangeable provider implementations
- **Observer Pattern**: Provider status monitoring and updates
- **Singleton Pattern**: Global factory instance management

## 🎉 **Summary**

The new LLM Provider Auto-Detection System provides:

1. **🔍 Automatic Detection**: No manual configuration needed
2. **🔄 Seamless Fallback**: Works with any available provider
3. **⚡ Easy Setup**: Just add API keys to environment
4. **🔧 Flexible Control**: Override auto-detection when needed
5. **📊 Full Visibility**: Monitor provider status and performance
6. **🚀 Future-Ready**: Easy to extend with new providers

This system ensures that your Git Assistant MCP will work immediately with whatever LLM provider you have configured, while maintaining the flexibility to use specific providers when needed.
