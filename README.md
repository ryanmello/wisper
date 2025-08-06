# Conscience - Agentic Operating System

Conscience is an AI-powered development tool that combines natural language processing with visual workflow design to automate complex development tasks. It features multiple specialized modules for code analysis, workflow automation, and pull request management.

## Features

- **Cipher**: AI-driven repository analysis and vulnerability detection
- **Waypoint**: Visual drag-and-drop workflow builder for development automation
- **Veda**: AI-powered pull request analysis and code review
- **Playbook**: Template management for reusable analysis workflows

## Architecture

- **Frontend**: Next.js 15 + React 19 + TypeScript + Tailwind CSS + shadcn/ui
- **Backend**: Python FastAPI + LangGraph + LangChain + OpenAI GPT-4.1
- **Real-time Communication**: WebSockets for live progress tracking
- **AI Orchestration**: LangGraph for multi-step AI workflows

##Prerequisites

- **Node.js** (v18 or higher)
- **Python** (v3.9 or higher)
- **Git**
- **GitHub Personal Access Token** (for repository operations)
- **OpenAI API Key** (for AI functionality)

## 🛠️ Installation & Setup

### 1. Clone the Repository

```bash
git clone <repository-url>
cd cipher
```

### 2. Frontend Setup

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:3000`

### 3. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create Python virtual environment
python -m venv venv

# Activate virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt

# Start backend server
python main.py
```

The backend API will be available at `http://localhost:8000`

### 4. Environment Configuration

Create a `.env` file in the `backend` directory with the following variables:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here
GITHUB_TOKEN=your_github_personal_access_token

# Optional (with defaults)
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=info
FRONTEND_URL=http://localhost:3000
GITHUB_DRY_RUN=false
```

#### Getting Required Tokens:

**OpenAI API Key:**
1. Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
2. Create a new API key
3. Copy and add to your `.env` file

**GitHub Personal Access Token:**
1. Go to GitHub Settings → Developer settings → Personal access tokens
2. Generate new token (classic) with these scopes:
   - `repo` (Full control of private repositories)
   - `read:user` (Read user profile data)
3. Copy and add to your `.env` file

## 🚀 Running the Application

### Development Mode

1. **Start Backend** (Terminal 1):
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
python main.py
```

2. **Start Frontend** (Terminal 2):
```bash
npm run dev
```

3. **Access the Application**:
   - Frontend: `http://localhost:3000`
   - Backend API Docs: `http://localhost:8000/docs`

### Production Build

```bash
# Build frontend
npm run build
npm start

# Backend runs the same way
cd backend
python main.py
```

## 📚 Module Guide

### Cipher - AI Code Analysis
- Navigate to `/cipher`
- Enter a GitHub repository URL
- Describe what you want to analyze in natural language
- Monitor real-time progress via WebSocket connection
- View detailed analysis results and tool execution logs

### Waypoint - Visual Workflow Builder
- Navigate to `/waypoint`
- Drag and drop tools from the sidebar
- Connect tools to create workflows
- Configure tool parameters
- Execute workflows with real-time monitoring

### Veda - Pull Request Analysis
- Navigate to `/veda`
- Select a repository and pull request
- Get AI-powered insights on code changes
- Review file-by-file analysis

### Playbook - Template Management
- Navigate to `/playbook`
- Save frequently used analysis prompts
- Reuse templates across Cipher and Waypoint

## 🔧 Development

### Available Scripts

**Frontend:**
- `npm run dev` - Start development server with Turbopack
- `npm run build` - Build for production
- `npm start` - Start production server
- `npm run lint` - Run ESLint

**Backend:**
- `python main.py` - Start FastAPI server
- `pytest` - Run tests (when available)

### Project Structure

```
cipher/
├── app/                    # Next.js app directory
│   ├── (auth)/            # Authentication routes
│   ├── cipher/            # Cipher module pages
│   ├── waypoint/          # Waypoint module pages
│   ├── veda/              # Veda module pages
│   └── api/               # API routes
├── components/            # React components
│   ├── ui/                # shadcn/ui components
│   ├── cipher/            # Cipher-specific components
│   ├── waypoint/          # Waypoint-specific components
│   └── veda/              # Veda-specific components
├── context/               # React context providers
├── lib/                   # Utilities and API clients
├── backend/               # Python FastAPI backend
│   ├── api/               # API route handlers
│   ├── core/              # Core application logic
│   ├── services/          # Business logic services
│   ├── tools/             # LangGraph tools
│   ├── models/            # Pydantic models
│   └── utils/             # Utility functions
└── public/                # Static assets
```

## 🔍 API Documentation

Once the backend is running, visit `http://localhost:8000/docs` for interactive API documentation powered by FastAPI's automatic OpenAPI generation.


### Common Issues

1. **Port conflicts**: Make sure ports 3000 (frontend) and 8000 (backend) are available
2. **Python virtual environment**: Always activate the virtual environment before running backend commands
3. **Missing API keys**: Ensure both OPENAI_API_KEY and GITHUB_TOKEN are set in backend/.env
4. **Node modules**: If you encounter frontend issues, try deleting node_modules and running `npm install` again

### Logs

- Frontend: Check browser console for client-side errors
- Backend: Server logs are displayed in the terminal where you ran `python main.py`
- WebSocket: Connection issues will be logged in both frontend console and backend logs
