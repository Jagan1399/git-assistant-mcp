# Project Structure Guide

This document outlines the recommended directory structure for the Git Assistant MCP project.

## 📁 Root Directory Structure

```
git-assistant-mcp/
├── README.md                 # Project overview and setup instructions
├── requirements.txt          # Python dependencies
├── PROJECT_OVERVIEW.md       # Detailed technical specification
├── PROJECT_STRUCTURE.md      # This file - directory organization guide
├── env.example              # Environment variables template
├── .gitignore               # Git ignore patterns
├── setup.py                 # Package installation script
├── pyproject.toml           # Modern Python project configuration
├── LICENSE                  # Project license
├── CONTRIBUTING.md          # Contribution guidelines
│
├── src/                     # Source code directory
│   └── git_assistant_mcp/  # Main package directory
│       ├── __init__.py
│       ├── core/            # Core functionality
│       │   ├── __init__.py
│       │   ├── state_scraper.py
│       │   ├── mcp_wrapper.py
│       │   └── git_operations.py
│       │
│       ├── llm/             # LLM integration
│       │   ├── __init__.py
│       │   ├── providers/
│       │   │   ├── __init__.py
│       │   │   ├── openai_provider.py
│       │   │   └── anthropic_provider.py
│       │   ├── prompt_templates.py
│       │   └── response_parser.py
│       │
│       ├── models/          # Data models
│       │   ├── __init__.py
│       │   ├── git_context.py
│       │   ├── llm_response.py
│       │   └── operation_state.py
│       │
│       ├── config/          # Configuration management
│       │   ├── __init__.py
│       │   ├── settings.py
│       │   └── prompts.py
│       │
│       ├── utils/           # Utility functions
│       │   ├── __init__.py
│       │   ├── git_parser.py
│       │   ├── safety_checker.py
│       │   ├── command_validator.py
│       │   └── logger.py
│       │
│       ├── cli/             # Command-line interface
│       │   ├── __init__.py
│       │   ├── main.py
│       │   └── commands.py
│       │
│       └── cursor/          # Cursor editor integration
│           ├── __init__.py
│           ├── chat_commands.py
│           └── terminal_integration.py
│
├── tests/                   # Test suite
│   ├── __init__.py
│   ├── conftest.py          # Pytest configuration
│   ├── unit/                # Unit tests
│   │   ├── __init__.py
│   │   ├── test_state_scraper.py
│   │   ├── test_mcp_wrapper.py
│   │   └── test_git_operations.py
│   ├── integration/         # Integration tests
│   │   ├── __init__.py
│   │   ├── test_end_to_end.py
│   │   └── test_cursor_integration.py
│   └── fixtures/            # Test data and fixtures
│       ├── sample_repos/
│       └── mock_responses/
│
├── docs/                    # Documentation
│   ├── README.md
│   ├── api/                 # API documentation
│   ├── user_guide/          # User documentation
│   ├── developer_guide/     # Developer documentation
│   └── examples/            # Usage examples
│
├── examples/                # Example scripts and configurations
│   ├── basic_usage.py
│   ├── cursor_integration.py
│   └── custom_prompts.py
│
├── scripts/                 # Build and deployment scripts
│   ├── build.sh
│   ├── deploy.sh
│   └── setup_dev_env.sh
│
├── .github/                 # GitHub-specific files
│   ├── workflows/           # GitHub Actions
│   ├── ISSUE_TEMPLATE/      # Issue templates
│   └── PULL_REQUEST_TEMPLATE.md
│
└── tools/                   # Development tools
    ├── pre-commit-hooks/    # Git hooks
    ├── linting/             # Linting configuration
    └── formatting/          # Code formatting tools
```

## 🚀 Development Workflow

### Phase 1: Core Engine (Current Focus)
Start with these files in order:
1. `src/git_assistant_mcp/models/git_context.py` - Data models
2. `src/git_assistant_mcp/core/state_scraper.py` - Git state gathering
3. `src/git_assistant_mcp/llm/prompt_templates.py` - LLM prompts
4. `src/git_assistant_mcp/core/mcp_wrapper.py` - Main logic
5. `src/git_assistant_mcp/cli/main.py` - Command-line interface

### Phase 2: Cursor Integration
Focus on:
1. `src/git_assistant_mcp/cursor/chat_commands.py` - @git command handling
2. `src/git_assistant_mcp/cursor/terminal_integration.py` - Terminal execution

### Phase 3: Advanced Features
Implement:
1. `src/git_assistant_mcp/utils/safety_checker.py` - Command safety
2. `src/git_assistant_mcp/core/git_operations.py` - Complex operations

## 📝 File Naming Conventions

- **Python files**: Use snake_case (e.g., `state_scraper.py`)
- **Classes**: Use PascalCase (e.g., `GitContext`)
- **Functions**: Use snake_case (e.g., `get_git_status()`)
- **Constants**: Use UPPER_SNAKE_CASE (e.g., `MAX_COMMITS`)
- **Directories**: Use snake_case (e.g., `git_assistant_mcp/`)

## 🔧 Configuration Files

### `pyproject.toml`
Modern Python project configuration including:
- Build system requirements
- Project metadata
- Development dependencies
- Tool configurations (black, flake8, mypy)

### `setup.py`
Package installation configuration for:
- PyPI distribution
- Dependencies
- Entry points
- Package data

### `.gitignore`
Git ignore patterns for:
- Python cache files
- Virtual environments
- Environment files
- IDE files
- Build artifacts

## 🧪 Testing Strategy

### Test Organization
- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test component interactions
- **End-to-end tests**: Test complete workflows
- **Fixtures**: Reusable test data and mock objects

### Test Coverage
- Aim for 95%+ coverage on core functions
- Focus on error handling and edge cases
- Mock external dependencies (Git, LLM APIs)
- Use real Git repositories for integration tests

## 📚 Documentation Structure

### User Documentation
- Quick start guide
- Command reference
- Best practices
- Troubleshooting

### Developer Documentation
- API reference
- Architecture overview
- Contributing guidelines
- Development setup

### API Documentation
- Auto-generated from docstrings
- Interactive examples
- Request/response schemas
- Error codes and handling

## 🚀 Getting Started

1. **Clone the repository**
2. **Set up virtual environment**
3. **Install dependencies**: `pip install -r requirements.txt`
4. **Copy environment file**: `cp env.example .env`
5. **Configure API keys** in `.env`
6. **Run tests**: `python -m pytest tests/`
7. **Start development** with Phase 1 components

## 🔄 Iterative Development

- Build and test each component individually
- Integrate components incrementally
- Maintain working functionality throughout development
- Use feature branches for new development
- Regular testing and validation

This structure provides a solid foundation for building a professional, maintainable, and scalable Git Assistant MCP project.
