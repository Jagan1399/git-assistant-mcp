# Git Assistant MCP - Project Overview

## 🎯 Project Vision

Transform Git operations from command memorization to natural language interaction, making version control intuitive and accessible to all developers while maintaining the power and flexibility of Git.

## 🏗️ Architecture Overview

### Core Components

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   User Input   │───▶│  MCP Wrapper   │───▶│   LLM API      │
│  (@git command)│    │                │    │  (OpenAI/Claude)│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       ▼                       │
         │              ┌─────────────────┐              │
         │              │ State Scraper   │              │
         │              │                │              │
         │              │ - Git Status    │              │
         │              │ - Branch Info   │              │
         │              │ - Recent Commits│              │
         │              └─────────────────┘              │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Response      │    │  Git Context    │    │  LLM Response   │
│  Processing    │    │  JSON Object    │    │  JSON Object    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       │                       │
┌─────────────────┐              │                       │
│ Command Output  │              │                       │
│ & Execution     │              │                       │
└─────────────────┘              │                       │
         │                       │                       │
         ▼                       │                       │
┌─────────────────┐              │                       │
│ State Update    │              │                       │
│ & Feedback      │              │                       │
└─────────────────┘              │                       │
```

## 📋 Implementation Phases

### Phase 1: Core Engine (MVP) - Weeks 1-2

#### Component 1: StateScraper (`state_scraper.py`)
**Purpose**: Gather comprehensive Git repository state information

**Key Functions**:
- `get_current_branch()`: Current branch name
- `get_git_status()`: Parsed status of all files
- `get_recent_commits()`: Last 5 commits with metadata
- `get_remote_info()`: Remote repository details
- `get_stash_info()`: Stash contents

**Output Format**:
```json
{
  "current_branch": "feature/new-feature",
  "status": [
    {
      "file": "src/main.py",
      "status": "modified",
      "staged": false,
      "changes": "unstaged"
    }
  ],
  "recent_commits": [
    {
      "hash": "a1b2c3d",
      "message": "Add new feature",
      "author": "John Doe",
      "date": "2024-01-15T10:30:00Z"
    }
  ],
  "remote_info": {
    "origin": "https://github.com/user/repo.git",
    "upstream": "https://github.com/upstream/repo.git"
  },
  "repository_path": "/path/to/repo"
}
```

#### Component 2: MCPWrapper (`git_pal.py`)
**Purpose**: Main interface that coordinates all operations

**Key Functions**:
- `process_query(query: str)`: Main entry point
- `build_context_prompt()`: Construct LLM prompt
- `call_llm_api(prompt: str)`: API communication
- `parse_llm_response(response: str)`: Response parsing
- `execute_git_command(command: str)`: Command execution

**LLM Prompt Structure**:
```
You are an expert Git assistant. Your goal is to help the user by providing the exact Git command needed to accomplish their task.

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
{git_context_json}
---
USER'S REQUEST:
"{user_query}"
```

### Phase 2: Cursor Integration - Weeks 3-4

#### Component 3: @git Chat Command Integration
**Purpose**: Seamless integration with Cursor's chat interface

**Implementation**:
- Custom command registration in Cursor
- Terminal access integration
- Response formatting for chat display
- Command execution buttons

**User Experience Flow**:
1. User types `@git stage my changes` in chat
2. System captures command and executes `python git_pal.py "stage my changes"`
3. Response appears in chat with:
   - Natural language confirmation
   - Executable Git command in code block
   - Copy/Run buttons automatically added by Cursor

#### Component 4: Actionable Command Execution
**Purpose**: One-click command execution with safety

**Features**:
- Automatic command formatting for Cursor
- Safety confirmation for destructive operations
- Real-time state updates after execution
- Error handling and user feedback

### Phase 3: Advanced Intelligence - Weeks 5-6

#### Component 5: Safety & Confirmation Layer
**Purpose**: Prevent accidental data loss

**Safety Checks**:
- **High Risk**: `git reset --hard`, `git push --force`
- **Medium Risk**: `git rebase`, `git merge --abort`
- **Low Risk**: `git add`, `git commit`, `git status`

**Implementation**:
```python
def assess_command_risk(command: str) -> RiskLevel:
    high_risk_patterns = [
        r"git reset --hard",
        r"git push --force",
        r"git clean -fd"
    ]
    # Risk assessment logic
```

#### Component 6: Multi-Step Wizards
**Purpose**: Handle complex Git operations

**Supported Operations**:
- Interactive rebases
- Complex merges
- Cherry-picking sequences
- Stash management

**State Management**:
```python
class OperationState:
    current_operation: str
    step_number: int
    total_steps: int
    context: Dict[str, Any]
    user_confirmations: List[bool]
```

## 🔧 Technical Implementation Details

### Data Models

#### GitContext (Pydantic Model)
```python
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime

class FileStatus(BaseModel):
    file: str
    status: str
    staged: bool
    changes: Optional[str] = None

class Commit(BaseModel):
    hash: str
    message: str
    author: str
    date: datetime

class GitContext(BaseModel):
    current_branch: str
    status: List[FileStatus]
    recent_commits: List[Commit]
    remote_info: Dict[str, str]
    repository_path: str
```

#### LLMResponse (Pydantic Model)
```python
class LLMResponse(BaseModel):
    reply: str
    command: str
    updated_context: Optional[Dict[str, Any]]
    is_destructive: bool
    explanation: str
    alternatives: Optional[List[str]] = None
    confidence: float
```

### Configuration Management

#### Settings (`config/settings.py`)
```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # LLM Configuration
    llm_provider: str = "gemini"  # gemini, openai, anthropic, local
    api_key: str
    model_name: str = "gemini-pro"
    max_tokens: int = 1000
    temperature: float = 0.1
    
    # Git Configuration
    git_timeout: int = 30
    max_commits: int = 5
    safe_mode: bool = True
    
    # UI Configuration
    enable_colors: bool = True
    verbose_output: bool = False
    
    class Config:
        env_file = ".env"
```

### Error Handling Strategy

#### Error Types
1. **GitOperationError**: Git command failures
2. **LLMAPIError**: API communication issues
3. **ContextParseError**: Git output parsing failures
4. **SafetyViolationError**: Unsafe command attempts

#### Error Recovery
- Automatic retry for transient failures
- Fallback to simpler Git commands
- User-friendly error messages
- Logging for debugging

### Testing Strategy

#### Unit Tests
- Mock Git commands
- Mock LLM API responses
- Edge case handling
- Error condition testing

#### Integration Tests
- Real Git repository operations
- End-to-end workflow testing
- Performance benchmarking
- Security validation

#### Test Coverage Goals
- Core functions: 95%+
- Error handling: 90%+
- Integration flows: 85%+

## 🚀 Deployment & Distribution

### Package Distribution
- PyPI package for easy installation
- Docker container for consistent environments
- GitHub releases with pre-built binaries

### Cursor Integration
- Extension marketplace submission
- Custom command configuration
- User preference management

### Configuration Management
- Environment-based configuration
- User-specific settings
- Team configuration sharing

## 🔒 Security Considerations

### API Key Management
- Secure environment variable storage
- API key rotation support
- Access logging and monitoring

### Command Validation
- Whitelist of safe Git commands
- Parameter sanitization
- Execution context validation

### Data Privacy
- No repository content sent to LLM APIs
- Local processing of sensitive information
- Configurable data retention policies

## 📊 Performance & Scalability

### Optimization Strategies
- Caching of Git state information
- Async processing for multiple operations
- Lazy loading of repository details
- Connection pooling for API calls

### Monitoring & Metrics
- Response time tracking
- Success rate monitoring
- API usage analytics
- Error rate tracking

## 🌟 Future Enhancements

### Phase 4: Advanced Features
- Multi-repository support
- Git workflow templates
- Team collaboration features
- Integration with CI/CD pipelines

### Phase 5: Ecosystem Expansion
- VS Code extension
- JetBrains plugin
- Command-line interface
- Web-based interface

### Phase 6: AI Enhancement
- Learning from user patterns
- Predictive command suggestions
- Automated conflict resolution
- Intelligent commit message generation

## 📚 Documentation & Support

### User Documentation
- Quick start guide
- Command reference
- Best practices
- Troubleshooting guide

### Developer Documentation
- API reference
- Contributing guidelines
- Architecture documentation
- Testing guide

### Community Support
- GitHub discussions
- Discord community
- Stack Overflow tags
- Video tutorials

---

This project represents a fundamental shift in how developers interact with Git, making version control more accessible while maintaining the power and flexibility that Git provides. The phased approach ensures we can deliver value incrementally while building toward a comprehensive solution.
