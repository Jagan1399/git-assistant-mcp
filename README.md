# Git Assistant MCP

An AI-powered Git assistant that integrates with Cursor editor to provide intelligent Git operations through natural language commands.

## 🚀 Overview

Git Assistant MCP is a Model Context Protocol (MCP) implementation that transforms how developers interact with Git. Instead of memorizing complex Git commands, simply describe what you want to do in natural language, and the assistant will:

- Analyze your repository's current state
- Understand your intent
- Provide the exact Git commands needed
- Execute them safely with confirmation for destructive operations

## ✨ Features

### Phase 1: Core Engine (MVP)
- **StateScraper**: Automatically gathers Git repository status
- **MCPWrapper**: Processes natural language queries and generates Git commands
- **LLM Integration**: Uses AI models to understand user intent

### Phase 2: Cursor Integration
- **@git Chat Commands**: Direct integration with Cursor's chat interface
- **Actionable Commands**: One-click execution of generated Git commands
- **Real-time Context Updates**: Automatic state refresh after operations

### Phase 3: Advanced Intelligence
- **Safety Layer**: Warns about destructive operations
- **Multi-step Wizards**: Handles complex Git operations like interactive rebases
- **Context Awareness**: Maintains operation state across multiple commands

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git repository
- Cursor editor
- Access to LLM API (OpenAI, Claude, etc.)

### Setup
```bash
# Clone the repository
git clone <repository-url>
cd git-assistant-mcp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys
```

### Environment Variables
Create a `.env` file with:
```env
OPENAI_API_KEY=your_openai_api_key_here
# or
ANTHROPIC_API_KEY=your_anthropic_api_key_here
```

## 🚀 Usage

### Basic Usage
```bash
# Stage all changes
python git_pal.py "stage my changes"

# Commit with message
python git_pal.py "commit with message 'fix bug'"

# Check status
python git_pal.py "what's my current git status?"
```

### Cursor Integration
1. Open Cursor editor
2. Use `@git` commands in the chat panel:
   - `@git stage my changes`
   - `@git commit with message 'update feature'`
   - `@git start interactive rebase on last 3 commits`

## 🏗️ Project Structure

```
git-assistant-mcp/
├── README.md                 # This file
├── requirements.txt          # Python dependencies
├── PROJECT_OVERVIEW.md       # Detailed project plan
├── state_scraper.py         # Git state gathering component
├── git_pal.py              # Main MCP wrapper
├── config/
│   ├── prompts.py          # LLM prompt templates
│   └── settings.py         # Configuration settings
├── utils/
│   ├── git_parser.py       # Git output parsing utilities
│   └── safety_checker.py   # Command safety validation
├── tests/                  # Test suite
└── examples/               # Usage examples
```

## 🔧 Development

### Running Tests
```bash
python -m pytest tests/
```

### Adding New Features
1. Create a feature branch: `git checkout -b feature/new-feature`
2. Implement your changes
3. Add tests
4. Submit a pull request

### Code Style
- Follow PEP 8 guidelines
- Use type hints
- Add docstrings for all functions
- Keep functions small and focused

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

### Areas for Contribution
- New Git operation support
- Additional LLM providers
- UI/UX improvements
- Documentation
- Testing

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Inspired by the need for more intuitive Git workflows
- Built with modern AI/LLM capabilities
- Designed for seamless Cursor editor integration

## 📞 Support

- **Issues**: Report bugs and request features on GitHub
- **Discussions**: Join community discussions
- **Documentation**: Check our [docs](docs/) folder

## 🗺️ Roadmap

- [x] Project planning and architecture
- [ ] Phase 1: Core Engine implementation
- [ ] Phase 2: Cursor integration
- [ ] Phase 3: Advanced intelligence features
- [ ] Community plugins and extensions
- [ ] Multi-editor support

---

**Made with ❤️ for developers who want to focus on code, not Git commands.**
