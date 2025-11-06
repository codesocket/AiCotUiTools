# AiCotUiTools - Quick Start Guide

## Prerequisites

- [Bun](https://bun.sh/) installed
- [UV](https://github.com/astral-sh/uv) installed
- OpenAI API Key

## Setup

1. **Set your OpenAI API Key**
   ```bash
   export OPENAI_API_KEY='your-api-key-here'
   ```

2. **Install all dependencies**
   ```bash
   bun run install:all
   ```
   This will install both backend (using UV) and frontend (using Bun) dependencies.

## Running the Application

**Start both frontend and backend with a single command:**

```bash
bun run dev
```

This will start:
- **Backend** (FastAPI + WebSockets) on http://localhost:8000
- **Frontend** (React + Vite) on http://localhost:5173

## Individual Commands

If you need to run services separately:

- **Backend only**: `bun run dev:backend`
- **Frontend only**: `bun run dev:frontend`

## API Endpoints

- Backend API: http://localhost:8000
- WebSocket: ws://localhost:8000/ws/{client_id}
- Frontend: http://localhost:5173

## Project Structure

```
AiCotUiTools/
├── webapp/
│   ├── backend/          # FastAPI backend with WebSockets
│   │   ├── server.py     # Main server file
│   │   ├── pyproject.toml # UV dependencies
│   │   └── ...
│   └── frontend/         # React + TypeScript frontend
│       ├── src/
│       ├── package.json
│       └── ...
├── package.json          # Root package.json for running both services
└── main.py              # Standalone CoT agent examples
```

## Troubleshooting

1. **OPENAI_API_KEY not set**: Make sure to export your API key before running the dev command
2. **Port already in use**: Make sure ports 8000 and 5173 are available
3. **Dependencies not installed**: Run `bun run install:all` to install all dependencies

## Documentation

- See `webapp/README.md` for detailed webapp documentation
- See `webapp/ARCHITECTURE.md` for system architecture
- See `webapp/EXAMPLES.md` for usage examples
