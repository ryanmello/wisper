# Wisper - AI-Powered Development Automation Platform

> **Transform repository analysis, security scanning, and code review with AI-driven workflows**

Wisper is an intelligent development automation platform that combines natural language AI with visual workflow orchestration to streamline complex development tasks. Built with enterprise-grade architecture, it features four specialized modules that work together to automate code analysis, vulnerability detection, pull request management, and workflow execution.

[![Next.js](https://img.shields.io/badge/Next.js-15.3-black?logo=next.js)](https://nextjs.org/)
[![React](https://img.shields.io/badge/React-19.0-blue?logo=react)](https://react.dev/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.0-blue?logo=typescript)](https://www.typescriptlang.org/)
[![Python](https://img.shields.io/badge/Python-3.9+-yellow?logo=python)](https://www.python.org/)

---

## 🎯 What is Wisper?

Wisper is a full-stack AI application that automates software development workflows by combining:

- **🤖 AI-Powered Analysis**: Uses OpenAI GPT-4.1 with LangChain/LangGraph for intelligent code understanding
- **📊 Visual Workflow Design**: Drag-and-drop interface for building custom automation pipelines
- **🔒 Security Scanning**: Automated vulnerability detection and remediation suggestions
- **🔄 Real-Time Execution**: WebSocket-based live progress tracking and streaming updates
- **💾 Template System**: Reusable workflow templates for common development tasks

---

## 🚀 Key Features

### 🔐 Cipher - AI-Driven Repository Analysis
Analyze any GitHub repository using natural language prompts. Cipher automatically:
- Clones and explores codebases to understand architecture and structure
- Detects programming languages, frameworks, and architectural patterns
- Scans for security vulnerabilities using specialized tools (govulncheck for Go)
- Generates comprehensive analysis reports with actionable insights
- Creates pull requests with automated fixes

**Use Cases:**
- "Scan this Go repository for vulnerabilities and create a PR with fixes"
- "Analyze the architecture and identify potential security issues"
- "Generate a comprehensive report on code quality and dependencies"

### 🎨 Waypoint - Visual Workflow Builder
Design custom automation workflows without writing code:
- Drag-and-drop tools from an organized sidebar (Repository, Analysis, Security, Git Operations)
- Connect tools to define execution order and dependencies
- Validate workflow configuration before execution
- Monitor real-time progress with visual node status indicators
- Save workflows as reusable playbooks for future use

**Workflow Tools:**
- `clone_repository` - Clone GitHub repositories
- `explore_codebase` - Comprehensive language/framework/architecture analysis
- `scan_go_vulnerabilities` - Security vulnerability scanning
- `apply_fixes` - Automated code fixes
- `create_pull_request` - Generate PRs with changes
- `generate_summary` - Create detailed analysis reports

### 📝 Veda - AI Pull Request Analysis
Intelligent PR review and modification:
- Fetch and analyze pull request changes and metadata
- Understand code diffs across multiple files
- Respond to natural language requests to modify PRs
- Automatically update pull requests with requested changes
- Context-aware suggestions based on entire PR scope

**Use Cases:**
- "Add error handling to the authentication changes in this PR"
- "Refactor these API endpoints to follow REST best practices"
- "Add unit tests for the new features in this pull request"

### 📚 Playbook - Workflow Template Management
Save and reuse successful workflows:
- Store frequently used analysis prompts (Cipher playbooks)
- Save complex workflow configurations (Waypoint playbooks)
- One-click workflow loading with pre-configured settings
- Share automation patterns across team members

---

## 🏗️ Technical Architecture

### Frontend Stack
- **Framework**: Next.js 15 with App Router and Turbopack
- **UI Library**: React 19 with TypeScript 5
- **Styling**: Tailwind CSS 4 with shadcn/ui component library
- **State Management**: React Context API with custom hooks
- **Drag & Drop**: react-dnd for visual workflow builder
- **Real-Time**: Native WebSocket API for streaming updates
- **Forms**: React Hook Form with Zod validation

### Backend Stack
- **API Framework**: Python FastAPI with async/await support
- **AI Orchestration**: LangGraph for multi-step agent workflows
- **LLM Integration**: LangChain with OpenAI GPT-4.1
- **Real-Time Communication**: WebSockets for progress streaming
- **Version Control**: GitPython and PyGithub for repository operations
- **Security Scanning**: Integration with govulncheck and extensible tool architecture

### System Design Highlights
- **Agentic AI Architecture**: LLM-powered orchestrator with tool-calling capabilities
- **Standardized Tool Interface**: All tools return consistent response formats with status, data, metrics, and errors
- **WebSocket Streaming**: Real-time progress updates with tool execution state management
- **Topological Workflow Execution**: Smart dependency resolution for parallel and sequential tool execution
- **Error Recovery**: Graceful error handling with detailed logging and user feedback
- **Repository Isolation**: Temporary directories for safe concurrent repository analysis

---

## 🎓 Why Wisper Stands Out

### 1. **Intelligent Agentic System**
Unlike traditional automation tools, Wisper uses an LLM-powered orchestrator that:
- Dynamically selects and sequences tools based on natural language goals
- Adapts execution plans based on intermediate results
- Handles errors gracefully and adjusts strategies
- Provides reasoning and context for each action taken

### 2. **Production-Ready Architecture**
- **Type-Safe**: Full TypeScript on frontend, Pydantic models on backend
- **Scalable**: Async/await throughout, concurrent task handling
- **Observable**: Comprehensive logging, error tracking, and real-time progress monitoring
- **Testable**: Modular design with dependency injection and standardized interfaces

### 3. **Developer Experience**
- **Intuitive UI**: Modern, responsive design with smooth animations and visual feedback
- **Real-Time Feedback**: WebSocket streams provide live progress updates
- **Flexible Workflows**: Use natural language (Cipher) OR visual builder (Waypoint)
- **GitHub Integration**: Seamless OAuth, repository access, and PR management

### 4. **Extensible Tool System**
Adding new automation capabilities is straightforward:
- Standardized tool decorator pattern
- Consistent response format across all tools
- Built-in error handling and logging
- Tool categorization and metadata

---

## 📋 Prerequisites

- **Node.js** (v18 or higher) - [Download](https://nodejs.org/)
- **Python** (v3.9 or higher) - [Download](https://www.python.org/)
- **Git** - [Download](https://git-scm.com/)
- **OpenAI API Key** - Required for AI functionality ([Get API Key](https://platform.openai.com/api-keys))
- **GitHub Personal Access Token** - Required for repository operations ([Create Token](https://github.com/settings/tokens))
- **govulncheck** (optional) - For Go vulnerability scanning ([Install Guide](https://pkg.go.dev/golang.org/x/vuln/cmd/govulncheck))

---

## 🛠️ Installation & Setup

### Quick Start

```bash
# 1. Clone the repository
git clone <repository-url>
cd wisper

# 2. Install frontend dependencies
npm install

# 3. Setup backend
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux  
source venv/bin/activate

pip install -r requirements.txt

# 4. Configure environment (see below)
# Create backend/.env with your API keys

# 5. Run the application
# Terminal 1 - Backend
cd backend
python main.py

# Terminal 2 - Frontend (new terminal)
npm run dev
```

Access the application at `http://localhost:3000` 🎉

---

### Detailed Setup Instructions

#### 1️⃣ Frontend Setup

```bash
# Install dependencies
npm install

# Start development server with Turbopack
npm run dev

# Build for production
npm run build
npm start
```

**Frontend runs on:** `http://localhost:3000`

#### 2️⃣ Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Start FastAPI server
python main.py
```

**Backend API runs on:** `http://localhost:8000`
**API Documentation:** `http://localhost:8000/docs` (Swagger UI)

#### 3️⃣ Environment Configuration

Create a `.env` file in the `backend/` directory:

```env
# === REQUIRED ===
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx

# === OPTIONAL (with sensible defaults) ===
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=info
FRONTEND_URL=http://localhost:3000
GITHUB_API_URL=https://api.github.com
GITHUB_DRY_RUN=false
```

#### 🔑 Getting Your API Keys

**OpenAI API Key:**
1. Visit [OpenAI API Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-`) and add to `.env`
5. **Note**: You'll need billing enabled and credits available

**GitHub Personal Access Token:**
1. Go to [GitHub Settings → Developer Settings → Personal Access Tokens](https://github.com/settings/tokens)
2. Click "Generate new token (classic)"
3. Select required scopes:
   - ✅ `repo` - Full control of private repositories
   - ✅ `read:user` - Read user profile data
   - ✅ `write:repo_hook` - Write repository hooks (for PR operations)
4. Generate and copy token (starts with `ghp_`)
5. Add to `.env` file

**govulncheck (Optional for Go scanning):**
```bash
go install golang.org/x/vuln/cmd/govulncheck@latest
```

---

## 🚀 Using Wisper

### Starting the Application

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # Windows: venv\Scripts\activate
python main.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

**Access Points:**
- 🌐 Frontend: `http://localhost:3000`
- 📡 Backend API: `http://localhost:8000`
- 📖 API Docs: `http://localhost:8000/docs`

---

## 📖 Usage Guide

### 🔐 Cipher - Natural Language Repository Analysis

1. **Navigate to Cipher** (`/cipher`)
2. **Enter Repository Details:**
   - GitHub repository URL (e.g., `https://github.com/username/repo`)
   - Natural language prompt describing your goal
3. **Examples:**
   ```
   "Scan this repository for security vulnerabilities and create a PR with fixes"
   
   "Analyze the architecture, detect all frameworks used, and generate a summary report"
   
   "Clone this repo, explore the codebase structure, and identify the main entry points"
   ```
4. **Monitor Progress:**
   - Real-time WebSocket updates show each tool execution
   - View LLM reasoning and decision-making process
   - Track tool results as they complete
5. **Review Results:**
   - Comprehensive analysis data
   - Tool execution logs
   - Generated reports and summaries
   - Links to created PRs (if applicable)

**Cipher Workflow:**
```
User Prompt → LLM Orchestrator → Tool Selection → Tool Execution → Results
                     ↓
              (Real-time WebSocket Updates)
```

---

### 🎨 Waypoint - Visual Workflow Builder

1. **Navigate to Waypoint** (`/waypoint`)
2. **Select Repository:**
   - Choose from your authenticated GitHub repositories
3. **Build Your Workflow:**
   - **Drag Tools** from the sidebar onto the canvas
   - **Connect Tools** by clicking output handles and dragging to input handles
   - **Arrange Nodes** for clarity (execution follows connections, not layout)
4. **Verify Configuration:**
   - Click "Verify" to validate workflow structure
   - System checks for:
     - Connected components
     - Valid tool sequences
     - No circular dependencies
5. **Execute Workflow:**
   - Click "Start" to begin execution
   - Watch nodes change status in real-time:
     - ⏳ **Queued** - Ready to execute
     - 🔵 **Executing** - Currently running
     - ✅ **Completed** - Finished successfully
     - ❌ **Failed** - Encountered an error
6. **View Results:**
   - Click "View Results" when complete
   - See detailed output from each tool
   - Review execution timeline and metrics
7. **Save as Playbook:**
   - Click "Save Playbook" to store workflow for reuse
   - Name and describe your workflow template

**Example Workflow:**
```
[Clone Repository] → [Explore Codebase] → [Scan Vulnerabilities]
                                              ↓
                                      [Generate Summary]
```

---

### 📝 Veda - AI Pull Request Modification

1. **Navigate to Veda** (`/veda`)
2. **Select a Pull Request:**
   - Choose repository
   - Select open pull request
3. **Make Natural Language Requests:**
   ```
   "Add comprehensive error handling to all API endpoints in this PR"
   
   "Refactor the authentication logic to use async/await"
   
   "Add unit tests covering the new features introduced in this PR"
   
   "Update the TypeScript interfaces to be more type-safe"
   ```
4. **AI Analysis:**
   - Fetches full PR context (files, diffs, metadata)
   - Understands code changes across all modified files
   - Applies requested changes intelligently
   - Updates the PR with new commits
5. **Review Changes:**
   - See what modifications were made
   - Review updated files
   - Check PR comments for AI reasoning

**Veda Workflow:**
```
PR Selection → Fetch PR Data → User Request → AI Analysis → Apply Changes → Update PR
```

---

### 📚 Playbook - Template Management

1. **Navigate to Playbook** (`/playbook`)
2. **Create Playbooks:**
   - **From Cipher:** Click "Save as Playbook" after a successful analysis
   - **From Waypoint:** Click "Save Playbook" after building a workflow
3. **Manage Templates:**
   - View all saved playbooks
   - Edit names and descriptions
   - Delete unused templates
4. **Use Playbooks:**
   - **In Cipher:** Click playbook card → Redirects to Cipher with pre-filled prompt
   - **In Waypoint:** Click playbook card → Loads entire workflow configuration
5. **Share Knowledge:**
   - Export/import playbook JSON (future feature)
   - Standardize team workflows

**Playbook Types:**
- **Cipher Playbooks** - Saved natural language prompts
- **Waypoint Playbooks** - Complete visual workflow configurations with nodes and connections

---

## 🏗️ Production Deployment

### Frontend Build
```bash
npm run build
npm start
```
Builds optimized production bundle with:
- Server-side rendering
- Static page generation
- Optimized assets and code splitting

### Backend Production
```bash
# Set production environment variables
export RELOAD=false
export LOG_LEVEL=warning

# Run with production ASGI server
python main.py
```

**Production Considerations:**
- Use environment variables for secrets (never commit `.env`)
- Enable HTTPS/TLS for WebSocket connections
- Configure CORS for your production frontend URL
- Set up proper logging and monitoring
- Consider rate limiting for API endpoints
- Use a process manager (PM2, systemd, supervisord)

---

## 🔧 Development

### Available Scripts

**Frontend:**
```bash
npm run dev        # Start development server with Turbopack (hot reload)
npm run build      # Build for production (optimized)
npm start          # Start production server
npm run lint       # Run ESLint for code quality
```

**Backend:**
```bash
python main.py     # Start FastAPI server with auto-reload
pytest             # Run test suite (when available)
```

---

### Project Structure

```
wisper/
├── app/                           # Next.js App Router (Frontend Pages)
│   ├── (auth)/                   # Authentication routes group
│   │   ├── sign-in/              # Sign in page
│   │   └── auth/callback/        # OAuth callback handler
│   ├── (conscience)/             # Main app layout group
│   │   └── page.tsx              # Landing page
│   ├── cipher/                   # Cipher module
│   │   ├── page.tsx              # Main Cipher interface
│   │   └── [taskId]/page.tsx    # Task detail view
│   ├── waypoint/                 # Waypoint visual builder
│   │   └── page.tsx              # Workflow canvas
│   ├── veda/                     # Veda PR analysis
│   │   └── page.tsx              # PR interface
│   ├── playbook/                 # Playbook management
│   │   └── page.tsx              # Template library
│   ├── docs/                     # Documentation
│   ├── settings/                 # User settings
│   ├── api/                      # Next.js API routes
│   │   └── auth/github/          # GitHub OAuth
│   ├── layout.tsx                # Root layout with providers
│   └── globals.css               # Global styles
│
├── components/                    # React Components
│   ├── ui/                       # shadcn/ui base components
│   │   ├── button.tsx            # Button component
│   │   ├── dialog.tsx            # Modal dialogs
│   │   ├── card.tsx              # Card layouts
│   │   └── ...                   # Other UI primitives
│   ├── cipher/                   # Cipher-specific components
│   │   ├── Chat.tsx              # Prompt input interface
│   │   ├── TaskTab.tsx           # Task list display
│   │   └── RepoDropdown.tsx      # Repository selector
│   ├── waypoint/                 # Waypoint components
│   │   ├── Canvas.tsx            # Workflow canvas
│   │   ├── WorkflowNode.tsx      # Draggable tool nodes
│   │   ├── ToolSidebar.tsx       # Tool palette
│   │   ├── StatusBar.tsx         # Control panel
│   │   └── WorkflowResultsSheet.tsx  # Results viewer
│   ├── veda/                     # Veda components
│   │   ├── File.tsx              # File diff viewer
│   │   └── PullRequestsDropdown.tsx  # PR selector
│   ├── playbook/                 # Playbook components
│   │   ├── PlaybookCard.tsx      # Template card
│   │   ├── PlaybookDialog.tsx    # Save dialog
│   │   └── PlaybookForm.tsx      # Template form
│   ├── Sidebar.tsx               # App navigation
│   ├── AuthLoadingScreen.tsx     # Loading state
│   └── EmptyState.tsx            # Empty state UI
│
├── context/                       # React Context Providers
│   ├── auth-context.tsx          # Authentication state
│   └── task-context.tsx          # Task management state
│
├── lib/                           # Frontend Libraries
│   ├── api/                      # API client functions
│   │   ├── cipher-api.ts         # Cipher API calls
│   │   ├── waypoint-api.ts       # Waypoint API calls
│   │   ├── veda-api.ts           # Veda API calls
│   │   ├── github-api.ts         # GitHub API calls
│   │   └── playbook-api.ts       # Local storage for playbooks
│   ├── interface/                # TypeScript interfaces
│   │   ├── cipher-interface.ts   # Cipher types
│   │   ├── waypoint-interface.ts # Waypoint types
│   │   └── ...                   # Other type definitions
│   └── utils.ts                  # Utility functions (cn, etc.)
│
├── backend/                       # Python FastAPI Backend
│   ├── main.py                   # Application entry point
│   ├── config/                   # Configuration
│   │   └── settings.py           # Environment settings
│   ├── core/                     # Core application
│   │   ├── app.py                # FastAPI app factory
│   │   └── orchestrator.py       # LLM orchestrator (agentic system)
│   ├── api/                      # API route handlers
│   │   ├── cipher.py             # Cipher endpoints
│   │   ├── waypoint.py           # Waypoint endpoints
│   │   ├── veda.py               # Veda endpoints
│   │   ├── github.py             # GitHub integration
│   │   └── websocket.py          # WebSocket connections
│   ├── services/                 # Business logic
│   │   ├── analysis_service.py   # Analysis orchestration
│   │   ├── task_service.py       # Task management
│   │   ├── tool_service.py       # Tool discovery
│   │   ├── waypoint_service.py   # Workflow validation
│   │   ├── github_service.py     # GitHub operations
│   │   └── websocket_service.py  # WebSocket management
│   ├── tools/                    # LangChain Tools
│   │   ├── __init__.py           # Tool registry
│   │   ├── repository/           # Repository operations
│   │   │   ├── clone_repository_tool.py
│   │   │   └── cleanup_repository_tool.py
│   │   ├── analysis/             # Analysis tools
│   │   │   ├── explore_codebase_tool.py
│   │   │   └── analyze_dependencies_tool.py
│   │   ├── security/             # Security scanning
│   │   │   └── scan_go_vulnerabilities_tool.py
│   │   ├── git_operations/       # Git operations
│   │   │   ├── create_pull_request_tool.py
│   │   │   ├── update_pull_request_tool.py
│   │   │   └── apply_fixes_tool.py
│   │   └── reporting/            # Report generation
│   │       └── generate_summary_tool.py
│   ├── models/                   # Pydantic Models
│   │   └── api_models.py         # Request/response schemas
│   ├── utils/                    # Utility modules
│   │   ├── logging_config.py     # Logging setup
│   │   ├── response_builder.py   # Response formatting
│   │   ├── tool_metadata_decorator.py  # Tool decorators
│   │   ├── async_tool_decorator.py     # Async utilities
│   │   └── build_validator.py    # Validation utilities
│   └── requirements.txt          # Python dependencies
│
├── public/                        # Static Assets
│   └── *.svg                     # Icons and images
│
├── package.json                   # Node.js dependencies
├── tsconfig.json                  # TypeScript configuration
├── next.config.ts                 # Next.js configuration
├── tailwind.config.js             # Tailwind CSS configuration
├── components.json                # shadcn/ui configuration
└── README.md                      # This file
```

---

## 🔍 API Documentation

Once the backend is running, access interactive API documentation:

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

### Key Endpoints

**Cipher:**
- `POST /cipher` - Start AI-driven repository analysis
- Returns `task_id` and WebSocket URL for monitoring

**Waypoint:**
- `GET /tools` - Get available workflow tools
- `POST /verify` - Validate workflow configuration
- `POST /start_workflow` - Execute workflow

**Veda:**
- `POST /analyze_comment` - Analyze and modify pull request

**GitHub:**
- `GET /repositories` - List user's repositories
- Requires GitHub authentication token

**WebSocket:**
- `WS /ws/cipher/{task_id}` - Real-time Cipher updates
- `WS /ws/waypoint/{task_id}` - Real-time Waypoint updates
- `WS /ws/veda/{task_id}` - Real-time Veda updates

---

## ⚠️ Troubleshooting

### Common Issues

#### 1. Port Conflicts
**Problem:** Port 3000 or 8000 already in use
```bash
# Find process using port (macOS/Linux)
lsof -i :3000
lsof -i :8000

# Find process using port (Windows)
netstat -ano | findstr :3000
netstat -ano | findstr :8000

# Kill process or change ports in .env and package.json
```

#### 2. Python Virtual Environment Issues
**Problem:** Commands fail or use wrong Python version
```bash
# Verify virtual environment is activated
which python  # macOS/Linux
where python  # Windows

# Should show path inside venv/ directory
# If not, activate again:
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate     # Windows
```

#### 3. Missing API Keys
**Problem:** "OPENAI_API_KEY is required" or GitHub features don't work
```bash
# Verify .env file exists in backend/ directory
ls -la backend/.env

# Check contents (don't share these!)
cat backend/.env

# Ensure no extra spaces or quotes around values
OPENAI_API_KEY=sk-proj-xxxx
GITHUB_TOKEN=ghp_xxxx
```

#### 4. Node Modules Issues
**Problem:** Frontend fails to start or build
```bash
# Clear and reinstall
rm -rf node_modules package-lock.json
npm install

# Try with clean cache
npm cache clean --force
npm install
```

#### 5. WebSocket Connection Failed
**Problem:** Real-time updates don't work
- Check browser console for WebSocket errors
- Verify backend is running on correct port
- Check CORS settings in `backend/config/settings.py`
- Ensure firewall allows WebSocket connections

#### 6. GitHub Authentication Issues
**Problem:** Can't access repositories or create PRs
- Verify token has correct scopes (`repo`, `read:user`)
- Check token hasn't expired
- Ensure `GITHUB_TOKEN` is set in backend `.env`
- Try generating a new token

#### 7. LLM Tool Call Failures
**Problem:** Orchestrator gets stuck or tools don't execute
- Check OpenAI API key is valid and has credits
- Review backend logs for error details
- Verify repository URL is accessible
- Check tool-specific requirements (e.g., govulncheck installed)

### Debugging Tips

**Frontend Debugging:**
```javascript
// Check in browser console
console.log('Auth status:', localStorage.getItem('github_token'))
console.log('Active tasks:', /* check task context */)
```

**Backend Debugging:**
```bash
# Increase log level for more details
export LOG_LEVEL=debug
python main.py

# Check logs for specific errors
# Logs show: HTTP requests, WebSocket connections, tool executions, LLM calls
```

**WebSocket Debugging:**
Open browser DevTools → Network → WS tab to see WebSocket messages in real-time

### Logs and Monitoring

- **Frontend Logs**: Browser console (`F12` → Console tab)
- **Backend Logs**: Terminal running `python main.py`
- **WebSocket Messages**: Browser DevTools → Network → WS
- **API Requests**: Browser DevTools → Network → Fetch/XHR

---

## 🤝 Contributing

Contributions are welcome! Here's how to add new features:

### Adding New Tools

1. Create tool file in appropriate category:
```python
# backend/tools/category/my_tool.py
from langchain_core.tools import tool
from utils.tool_metadata_decorator import tool_category
from models.api_models import StandardToolResponse

@tool_category("category_name")
@tool
def my_tool(param: str) -> StandardToolResponse:
    """Tool description for LLM.
    
    Args:
        param: Parameter description
        
    Returns:
        StandardToolResponse with results
    """
    # Implementation
    pass
```

2. Register in `tools/__init__.py`:
```python
from .category.my_tool import my_tool
ALL_TOOLS = [existing_tools..., my_tool]
```

3. Tool automatically appears in Waypoint sidebar!

### Technology Choices Explained

- **Next.js 15**: Latest App Router for better performance and DX
- **React 19**: Concurrent rendering and improved suspense
- **FastAPI**: Async Python framework with automatic API docs
- **LangChain/LangGraph**: Production-ready LLM orchestration
- **WebSockets**: Native real-time without polling overhead
- **shadcn/ui**: Unstyled components for full customization
- **Tailwind CSS 4**: Utility-first styling with design tokens

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://www.langchain.com/) - LLM orchestration framework
- [Next.js](https://nextjs.org/) - React framework
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [shadcn/ui](https://ui.shadcn.com/) - Beautiful component library
- [OpenAI](https://openai.com/) - GPT-4.1 language model

---

<div align="center">

**⭐ Star this repository if you find it helpful!**

Made with ❤️ for developers who love automation

</div>
