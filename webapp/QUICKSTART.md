# ⚡ Quick Start Guide

Get the LLM Agent UI running in **2 simple steps**!

## Step 1: Set Your OpenAI API Key

```bash
export OPENAI_API_KEY="sk-your-api-key-here"
```

💡 **Tip**: Add this to your `~/.bashrc` or `~/.zshrc` to make it permanent.

## Step 2: Run the Application

From the **project root** directory:

```bash
# Install dependencies (first time only)
bun run install:all

# Run both frontend and backend
bun run dev
```

You should see:
```
[0] INFO: Uvicorn running on http://0.0.0.0:8000
[1] VITE ready in xxx ms
[1] ➜ Local: http://localhost:5173/
```

## Step 3: Open Your Browser

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

### API Key Issues?
- **Check API Key**: `echo $OPENAI_API_KEY`
- Make sure it starts with `sk-`

### Port Already in Use?
- **Backend (8000)**: `lsof -ti:8000 | xargs kill -9`
- **Frontend (5173)**: `lsof -ti:5173 | xargs kill -9`

### Dependencies Not Installed?
```bash
# Install backend dependencies (UV)
bun run install:backend

# Install frontend dependencies (Bun)
bun run install:frontend
```

### Can't connect?
- Make sure **both** backend and frontend are running
- Backend must be on port **8000**
- Frontend must be on port **5173**
- Check that no firewall is blocking the ports

## 💻 Alternative Commands

Run services individually:
```bash
# Backend only
bun run dev:backend

# Frontend only
bun run dev:frontend
```

## 📚 Next Steps

- Read [README.md](README.md) for detailed architecture
- Explore the code in `backend/server.py` and `backend/enhanced_agent.py`
- Check out the React components in `frontend/src/`
- Review [ARCHITECTURE.md](ARCHITECTURE.md) for system design
- See [EXAMPLES.md](EXAMPLES.md) for more usage patterns

---

**Happy coding!** 🚀
