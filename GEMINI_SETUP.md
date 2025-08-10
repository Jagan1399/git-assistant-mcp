# Gemini Setup Guide for Git Assistant MCP

This guide will help you set up Google's Gemini API as your primary LLM provider for the Git Assistant MCP project.

## 🚀 Quick Start

### 1. Get Your Google API Key

1. **Visit Google AI Studio**: Go to [Google AI Studio](https://aistudio.google.com/)
2. **Sign in**: Use your Google account
3. **Get API Key**: Click on "Get API key" in the top right
4. **Create New Key**: Choose "Create API key in new project" or use existing project
5. **Copy the Key**: Save your API key securely

### 2. Set Up Environment Variables

Create a `.env` file in your project root:

```bash
# Copy the example file
cp env.example .env

# Edit the .env file with your API key
nano .env
```

Add your Google API key:

```env
# Primary LLM provider
LLM_PROVIDER=gemini

# Google Gemini Configuration
GOOGLE_API_KEY=your_actual_api_key_here
GEMINI_MODEL_NAME=gemini-pro
GEMINI_MAX_TOKENS=1000
GEMINI_TEMPERATURE=0.1
```

### 3. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate     # On Windows

# Install requirements
pip install -r requirements.txt
```

### 4. Test the Integration

Run the test script to verify everything is working:

```bash
python test_gemini_integration.py
```

## 🔧 Configuration Options

### Gemini Model Selection

| Model | Description | Use Case |
|-------|-------------|----------|
| `gemini-pro` | Most capable model | General Git operations |
| `gemini-pro-vision` | Includes image understanding | Complex repository analysis |

### Temperature Settings

| Value | Behavior | Recommendation |
|-------|----------|----------------|
| 0.0 | Most deterministic | Production use, consistent commands |
| 0.1 | Slightly creative | Default setting, good balance |
| 0.3+ | More creative | Development/testing, alternative approaches |

### Token Limits

| Setting | Use Case |
|---------|----------|
| 500 | Simple Git commands |
| 1000 | Standard operations with context |
| 2000+ | Complex multi-step operations |

## 🧪 Testing Your Setup

### Basic Test

```bash
# Test with a simple Git operation
python test_gemini_integration.py
```

### Expected Output

```
🧪 Testing Gemini Integration for Git Assistant MCP
============================================================
✅ Google API key found: AIzaSyC...
✅ Settings loaded successfully
   - LLM Provider: gemini
   - Gemini Model: gemini-pro
   - Max Tokens: 1000
   - Temperature: 0.1
✅ Gemini provider initialized successfully
📤 Sending test prompt to Gemini...
   Prompt length: 1234 characters
✅ Response received successfully!
   - Reply: I'll stage your modified file for you.
   - Command: git add test.txt
   - Explanation: This command stages the modified test.txt file
   - Is Destructive: False
   - Confidence: 0.95
✅ Response validation passed
   - Safety Level: safe
✅ Command is safe to execute

🎉 All tests passed! Gemini integration is working correctly.
```

## 🚨 Troubleshooting

### Common Issues

#### 1. API Key Not Found
```
❌ GOOGLE_API_KEY environment variable not set!
```
**Solution**: Make sure your `.env` file exists and contains the correct API key.

#### 2. Import Errors
```
❌ Import error: No module named 'git_assistant_mcp'
```
**Solution**: Ensure you're running from the project root and the package structure is correct.

#### 3. API Rate Limits
```
❌ Error during testing: Quota exceeded
```
**Solution**: Check your Google AI Studio quota and billing status.

#### 4. Network Issues
```
❌ Error during testing: Connection timeout
```
**Solution**: Check your internet connection and firewall settings.

### Debug Mode

Enable debug logging by setting in your `.env`:

```env
DEBUG=true
LOG_LEVEL=DEBUG
```

## 🔒 Security Best Practices

### API Key Management

1. **Never commit API keys** to version control
2. **Use environment variables** or `.env` files
3. **Rotate keys regularly** for production use
4. **Monitor usage** in Google AI Studio dashboard

### Rate Limiting

- **Free tier**: 15 requests per minute
- **Paid tier**: Higher limits based on billing
- **Monitor usage** to avoid unexpected charges

## 📊 Performance Optimization

### Caching

Enable response caching in your `.env`:

```env
ENABLE_CACHING=true
CACHE_TTL=300
```

### Batch Operations

For multiple Git operations, consider batching requests to reduce API calls.

## 🔄 Updating Gemini

### Check for Updates

```bash
pip install --upgrade google-generativeai
```

### Model Updates

Google regularly updates Gemini models. Check [Google AI Studio](https://aistudio.google.com/) for the latest models and features.

## 📚 Next Steps

Once Gemini is working:

1. **Implement StateScraper**: Start building the Git state gathering component
2. **Create MCPWrapper**: Build the main logic that coordinates everything
3. **Add Cursor Integration**: Connect with Cursor's chat interface
4. **Implement Safety Features**: Add command validation and confirmation

## 🆘 Getting Help

- **Google AI Studio**: [https://aistudio.google.com/](https://aistudio.google.com/)
- **Gemini API Docs**: [https://ai.google.dev/docs](https://ai.google.dev/docs)
- **Project Issues**: Use GitHub issues for project-specific problems

---

**Happy coding with Gemini! 🚀**
