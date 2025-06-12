# Whisper - Backend

This is the backend service for Whisper, built with FastAPI and LangGraph for AI-powered repository analysis.

## 🚀 Features

- **AI-Powered Repository Analysis**: Comprehensive codebase analysis using GPT-4
- **Real-time Updates**: WebSocket-based progress tracking and live results
- **Multiple Analysis Types**: Support for various analysis tasks (explore, security, bugs, etc.)
- **Scalable Architecture**: Built with FastAPI and async/await patterns
- **Type Safety**: Full Pydantic model validation
- **Service-Oriented**: Clean separation of concerns with service layer

## 🏗️ Architecture

The backend uses a service-oriented architecture with LangGraph for AI workflow orchestration:

### Core Components

1. **Whisper Analysis Agent**: Analyzes codebase structure, architecture patterns, and dependencies
2. **Analysis Service**: Manages tasks, WebSocket connections, and agent orchestration
3. **FastAPI Application**: REST API and WebSocket endpoints
4. **Pydantic Models**: Type-safe request/response validation

### Technology Stack

- **FastAPI**: Modern, fast web framework for building APIs
- **LangGraph**: Multi-agent workflow orchestration
- **LangChain**: LLM integration and tooling
- **WebSockets**: Real-time communication
- **Pydantic**: Data validation and serialization
- **GitPython**: Git repository operations
- **OpenAI GPT-4**: AI-powered code analysis

## 📡 API Endpoints

### REST Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | API status and welcome message |
| `GET` | `/health` | Health check with service status |
| `POST` | `/api/tasks/` | Create new analysis task |
| `GET` | `/api/tasks/{task_id}` | Get specific task status |
| `GET` | `/api/active-connections` | Get active connections info |

### WebSocket Endpoints

| Endpoint | Description |
|----------|-------------|
| `WS /ws/tasks/{task_id}` | Real-time analysis updates and results |

## 🛠️ Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Environment Configuration

Copy the example environment file and configure:

```bash
cp env.example .env
```

Edit `.env` with your settings:

```env
# Required
OPENAI_API_KEY=your_openai_api_key_here

# Optional (defaults shown)
HOST=127.0.0.1
PORT=8000
RELOAD=true
LOG_LEVEL=info
FRONTEND_URL=http://localhost:3000
```

### 3. Run the Server

```bash
# Using the main entry point
python main.py

# Or using the startup script
python start.py

# Or directly with uvicorn
uvicorn fastapi_backend:app --host 127.0.0.1 --port 8000 --reload
```

The API will be available at:
- **API**: http://127.0.0.1:8000
- **Interactive Docs**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📖 Usage Examples

### Creating an Analysis Task

```python
import requests

# Create a new analysis task
response = requests.post("http://localhost:8000/api/tasks/", json={
    "repository_url": "https://github.com/facebook/react",
    "task_type": "explore-codebase"
})

data = response.json()
task_id = data["task_id"]
websocket_url = data["websocket_url"]
print(f"Task created: {task_id}")
```

### WebSocket Connection for Real-time Updates

```javascript
const taskId = "your-task-id";
const ws = new WebSocket(`ws://localhost:8000/ws/tasks/${taskId}`);

ws.onopen = () => {
    // Send task parameters
    ws.send(JSON.stringify({
        repository_url: "https://github.com/facebook/react",
        task_type: "explore-codebase"
    }));
};

ws.onmessage = (event) => {
    const data = JSON.parse(event.data);
    
    switch(data.type) {
        case 'task.started':
            console.log('Analysis started:', data);
            break;
        case 'task.progress':
            console.log(`Progress: ${data.progress}% - ${data.current_step}`);
            break;
        case 'task.completed':
            console.log('Analysis completed:', data.results);
            break;
        case 'task.error':
            console.error('Analysis failed:', data.error);
            break;
    }
};
```

### Python WebSocket Client

```python
import asyncio
import websockets
import json

async def analyze_repository():
    uri = "ws://localhost:8000/ws/tasks/your-task-id"
    
    async with websockets.connect(uri) as websocket:
        # Send task parameters
        await websocket.send(json.dumps({
            "repository_url": "https://github.com/facebook/react",
            "task_type": "explore-codebase"
        }))
        
        # Listen for updates
        async for message in websocket:
            data = json.loads(message)
            print(f"Received: {data['type']}")
            
            if data['type'] == 'task.completed':
                print("Analysis complete!")
                break

asyncio.run(analyze_repository())
```

## 🏗️ Development

### Project Structure

```
backend/
├── main.py                     # Application entry point
├── start.py                    # Simple startup script
├── fastapi_backend.py          # FastAPI application and routes
├── repository_explorer_agent.py # Whisper analysis agent
├── services/                   # Service layer
│   ├── __init__.py
│   └── analysis_service.py     # Analysis task management
├── models/                     # Pydantic models
│   ├── __init__.py
│   └── api_models.py          # Request/response models
├── requirements.txt            # Python dependencies
├── env.example                 # Environment template
└── README.md                  # This file
```

### Key Classes

- **`AnalysisService`**: Manages analysis tasks and WebSocket connections
- **`WhisperAnalysisAgent`**: Performs AI-powered repository analysis
- **`AnalysisRequest/Response`**: Type-safe API models



### Testing

```bash
# Install test dependencies
pip install pytest pytest-asyncio

# Run tests
pytest

# Run with coverage
pytest --cov=.
```

## 🔧 Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `OPENAI_API_KEY` | OpenAI API key (required) | - |
| `HOST` | Server host | `127.0.0.1` |
| `PORT` | Server port | `8000` |
| `RELOAD` | Enable auto-reload | `true` |
| `LOG_LEVEL` | Logging level | `info` |
| `FRONTEND_URL` | Frontend URL for CORS | `http://localhost:3000` |

### Supported Analysis Types

- `explore-codebase`: Comprehensive repository analysis
- `dependency-audit`: Security vulnerability analysis with automatic PR creation

## 🚨 Troubleshooting

### Common Issues

1. **Import Error for `langchain_openai`**:
   ```bash
   pip install -r requirements.txt
   ```

2. **OpenAI API Key Missing**:
   - Set `OPENAI_API_KEY` in your `.env` file
   - The server will start but analysis will fail without it

3. **Port Already in Use**:
   - Change `PORT` in `.env` file
   - Or kill the process using the port

4. **WebSocket Connection Failed**:
   - Ensure the backend is running
   - Check firewall settings
   - Verify the WebSocket URL format

## 📝 License

MIT License - see LICENSE file for details

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request 