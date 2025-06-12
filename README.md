# Whisper - AI-Powered Repository Analysis

Whisper is a comprehensive repository analysis tool that combines a modern Next.js frontend with an AI-powered FastAPI backend to provide deep insights into codebases.

## 🚀 Features

- **AI-Powered Analysis**: Comprehensive codebase exploration using GPT-4
- **Real-time Updates**: WebSocket-based progress tracking
- **Multiple Analysis Types**: Explore codebase, find bugs, security audits, and more
- **GitHub Integration**: Browse your repositories or analyze any public repo by URL
- **Modern UI**: Beautiful, responsive interface built with Next.js and Tailwind CSS
- **Export Reports**: Download analysis results as JSON

## 🏗️ Architecture

- **Frontend**: Next.js 15 with TypeScript, Tailwind CSS, and shadcn/ui components
- **Backend**: FastAPI with WebSocket support, LangGraph workflows, and OpenAI integration
- **AI Engine**: Whisper Analysis Agent using LangChain and OpenAI GPT-4

## 📋 Prerequisites

- Node.js 18+ and npm
- Python 3.8+
- OpenAI API key
- Git

## 🛠️ Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd whisper
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Install Python dependencies
pip install -r requirements.txt

# Create environment file
cp .env.example .env

# Edit .env and add your OpenAI API key
# OPENAI_API_KEY=your_openai_api_key_here
```

### 3. Frontend Setup

```bash
# Navigate back to root directory
cd ..

# Install Node.js dependencies
npm install

# Create environment file (optional)
cp env.example .env.local

# Edit .env.local if you want to configure GitHub OAuth
# NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id_here
```

### 4. Start the Application

**Terminal 1 - Backend:**
```bash
cd backend
python main.py
```

**Terminal 2 - Frontend:**
```bash
npm run dev
```

### 5. Access the Application

- Frontend: [http://localhost:3000](http://localhost:3000)
- Backend API: [http://localhost:8000](http://localhost:8000)
- API Documentation: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🎯 Usage

1. **Connect to GitHub** (optional):
   - Use GitHub OAuth or Personal Access Token
   - Browse your repositories

2. **Analyze Any Repository**:
   - Click "Analyze Any Public Repository"
   - Enter a GitHub repository URL
   - Example: `https://github.com/microsoft/vscode`

3. **Choose Analysis Type**:
   - **Explore Codebase**: Comprehensive overview and architecture analysis
   - **Find Bugs**: Identify potential issues and code quality problems
   - **Security Audit**: Security vulnerabilities and best practices
   - And more...

4. **Real-time Analysis**:
   - Watch progress in real-time via WebSocket connection
   - Get AI-powered insights and recommendations

5. **Export Results**:
   - Download detailed analysis reports as JSON

## 🔧 Configuration

### Backend Configuration (`backend/.env`)

```env
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_MODEL=gpt-4
LOG_LEVEL=INFO
```

### Frontend Configuration (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
NEXT_PUBLIC_GITHUB_CLIENT_ID=your_github_client_id_here
```

## 🧪 Testing

### Test Backend API

```bash
cd backend
python test_backend.py
```

### Test with Sample Repository

```bash
cd backend
python test_small_repo.py
```

## 📚 API Documentation

The backend provides a comprehensive REST API with WebSocket support:

- `POST /api/tasks/` - Create analysis task
- `GET /api/tasks/{task_id}` - Get task status
- `WS /ws/tasks/{task_id}` - Real-time updates
- `GET /health` - Health check

Visit [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API documentation.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Troubleshooting

### Common Issues

1. **Backend won't start**: Check that your OpenAI API key is set in `backend/.env`
2. **WebSocket connection fails**: Ensure backend is running on port 8000
3. **GitHub OAuth not working**: Set up GitHub OAuth app and configure client ID
4. **Analysis fails**: Check backend logs for detailed error messages

### Getting Help

- Check the [API documentation](http://localhost:8000/docs)
- Review backend logs for error details
- Ensure all dependencies are installed correctly
