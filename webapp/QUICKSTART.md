# ⚡ Quick Start Guide

Get the LLM Agent UI running in **3 simple steps**!

## Step 1: Set Your OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

💡 **Tip**: Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Step 2: Start the Backend

Open a terminal and run:

```bash
cd webapp
./start-backend.sh
```

You should see:
```
✅ Starting FastAPI server on http://localhost:8000
📡 WebSocket endpoint: ws://localhost:8000/ws/{client_id}
```

## Step 3: Start the Frontend

Open a **new terminal** and run:

```bash
cd webapp
./start-frontend.sh
```

You should see:
```
✅ Starting Vite development server on http://localhost:5173
```

## Step 4: Open Your Browser

Navigate to: **http://localhost:5173**

## 🎉 You're Ready!

Try these prompts to see the magic:

### UI Tools (Executed in Browser)
```
"Change the theme to purple"
"Enable high contrast mode"
"Make the UI pink"
```

### Backend Tools (Executed on Server)
```
"What's 25 * 47?"
"Search for Python information"
"What's the current date?"
```

### Mix Both!
```
"Change the theme to teal and calculate 99 * 88"
"Enable high contrast and tell me the date"
```

## 🐛 Troubleshooting

### Backend won't start?
- **Check API Key**: `echo $OPENAI_API_KEY`
- **Install dependencies**: `cd webapp/backend && pip install -r requirements.txt`

### Frontend won't start?
- **Install dependencies**: `cd webapp/frontend && npm install`
- **Check Node version**: `node --version` (should be 18+)

### Can't connect?
- Make sure **both** backend and frontend are running
- Backend must be on port **8000**
- Frontend must be on port **5173**

## 📚 Next Steps

- Read [README.md](README.md) for detailed architecture
- Explore the code in `webapp/backend/server.py`
- Check out the React components in `webapp/frontend/src/`

---

**Happy coding!** 🚀
