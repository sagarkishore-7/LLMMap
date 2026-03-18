# Deployment Guide — PromptLab

## Architecture

```
                     ┌──────────────────────────────────────────────┐
                     │              Ollama Cloud                    │
                     │  (shared by local dev AND production)        │
                     └─────────────────────┬────────────────────────┘
                                           │ OLLAMA_API_KEY
                                           │
         ┌─────────────────┐     HTTP      │      ┌──────────────────┐
         │   Vercel         │ ◄────────────┼────► │   Railway         │
         │   (Next.js UI)   │              │      │   (FastAPI API)   │
         │                  │──────────────┘      │                   │
         │  NEXT_PUBLIC_    │   JSON/REST          │  PORT (auto)      │
         │  API_BASE_URL    │ ──────────────────► │  PROMPTLAB_CORS_  │
         └──────────────────┘                      │  ORIGINS          │
                                                   └──────────────────┘
```

**Key insight:** PromptLab's simulator is fully deterministic — it does NOT call any LLM backend. The sandbox targets are Python functions. This means the Railway backend has **zero runtime dependency on Ollama Cloud**. The Ollama Cloud configuration only matters for the LLMMap CLI scanner.

---

## Environment Variables

| Variable | Where | Default | Description |
|----------|-------|---------|-------------|
| `OLLAMA_BASE_URL` | Backend / CLI | `https://api.ollama.com` | Ollama API base URL |
| `OLLAMA_MODEL` | Backend / CLI | `qwen3-coder-next:cloud` | Default Ollama model |
| `OLLAMA_API_KEY` | Backend / CLI | (none) | Ollama Cloud API key |
| `PORT` | Backend | `8000` | HTTP port (Railway sets this automatically) |
| `PROMPTLAB_CORS_ORIGINS` | Backend | `http://localhost:3000` | Comma-separated allowed origins |
| `NEXT_PUBLIC_API_BASE_URL` | Frontend | `http://localhost:8000` | Backend API URL (build-time) |
| `OPENAI_API_KEY` | CLI only | (none) | OpenAI API key (alternative provider) |
| `ANTHROPIC_API_KEY` | CLI only | (none) | Anthropic API key (alternative provider) |
| `GOOGLE_API_KEY` | CLI only | (none) | Google API key (alternative provider) |

---

## Local Development

Both local and production use the same configuration pattern. The only difference is the URLs.

### 1. Backend

```bash
# From project root
python -m venv .venv && source .venv/bin/activate
pip install -e ".[web]"

# Set environment (or copy .env.example to .env)
export OLLAMA_BASE_URL=https://api.ollama.com
export OLLAMA_MODEL=qwen3-coder-next:cloud
export OLLAMA_API_KEY=your-key-here

# Start the API
uvicorn promptlab.api.main:app --reload --port 8000
```

### 2. Frontend

```bash
cd web
npm install

# Create .env.local (gitignored)
echo "NEXT_PUBLIC_API_BASE_URL=http://localhost:8000" > .env.local

npm run dev
# Open http://localhost:3000
```

### 3. Verify

```bash
curl http://localhost:8000/api/health
# {"status":"ok","service":"promptlab"}

curl http://localhost:8000/api/scenarios
# [{"scenario_id":"support_bot",...}]
```

### Using Local Ollama Instead (Advanced)

If you prefer to run Ollama locally instead of using Ollama Cloud:

```bash
# Start local Ollama
ollama serve

# Override the base URL
export OLLAMA_BASE_URL=http://127.0.0.1:11434
export OLLAMA_MODEL=dolphin3:8b
# No API key needed for local
unset OLLAMA_API_KEY
```

---

## Railway Deployment (Backend)

### Step 1: Create a Railway project

```bash
# Install Railway CLI
npm install -g @railway/cli
railway login
railway init
```

### Step 2: Configure environment variables

In the Railway dashboard (or via CLI):

```bash
railway variables set PROMPTLAB_CORS_ORIGINS=https://your-app.vercel.app
railway variables set OLLAMA_BASE_URL=https://api.ollama.com
railway variables set OLLAMA_MODEL=qwen3-coder-next:cloud
railway variables set OLLAMA_API_KEY=your-ollama-cloud-key
```

`PORT` is set automatically by Railway — do not set it manually.

### Step 3: Deploy

Railway auto-detects Python from `pyproject.toml` and uses the `Procfile`:

```bash
railway up
```

Or connect your GitHub repo in the Railway dashboard for automatic deploys on push.

### Step 4: Verify

```bash
curl https://your-api.railway.app/api/health
# {"status":"ok","service":"promptlab"}
```

### Railway Configuration Files

- `Procfile` — start command: `uvicorn promptlab.api.main:app --host 0.0.0.0 --port $PORT`
- `railway.toml` — build settings and health check path
- `pyproject.toml` — Python dependencies (Railway installs from this)

---

## Vercel Deployment (Frontend)

### Step 1: Import project

1. Go to [vercel.com/new](https://vercel.com/new)
2. Import your GitHub repository
3. Set **Root Directory** to `web`
4. Framework preset: **Next.js** (auto-detected)

### Step 2: Configure environment variables

In Vercel project settings > Environment Variables:

| Key | Value |
|-----|-------|
| `NEXT_PUBLIC_API_BASE_URL` | `https://your-api.railway.app` |

This is a **build-time** variable — it's baked into the JavaScript bundle. Redeploy after changing it.

### Step 3: Deploy

Vercel deploys automatically when you push to main. Or trigger manually:

```bash
cd web
npx vercel --prod
```

### Step 4: Verify

Open your Vercel URL. The landing page should load and scenarios should be fetched from the Railway backend.

---

## Simulating Production Locally

To test the full production-like setup on your machine:

```bash
# Terminal 1: Backend (simulating Railway)
export PORT=8000
export PROMPTLAB_CORS_ORIGINS=http://localhost:3000
export OLLAMA_BASE_URL=https://api.ollama.com
export OLLAMA_API_KEY=your-key
uvicorn promptlab.api.main:app --host 0.0.0.0 --port $PORT

# Terminal 2: Frontend (simulating Vercel)
cd web
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm run build
NEXT_PUBLIC_API_BASE_URL=http://localhost:8000 npm start
```

---

## Limitations

1. **PromptLab is stateless.** Each simulation request is independent. There is no session persistence, user accounts, or conversation history. This is by design — the sandbox is deterministic.

2. **No LLM calls in PromptLab.** The simulator uses deterministic pattern matching, not live LLM inference. Ollama Cloud is only used by the LLMMap CLI scanner (a separate tool). The Railway deployment has zero dependency on Ollama Cloud for PromptLab functionality.

3. **NEXT_PUBLIC variables are build-time.** Changing `NEXT_PUBLIC_API_BASE_URL` requires a redeploy on Vercel. It cannot be changed at runtime.

4. **CORS must match exactly.** The `PROMPTLAB_CORS_ORIGINS` value on Railway must include the exact Vercel domain (with `https://` and no trailing slash).

5. **No persistent storage.** Railway's filesystem is ephemeral. PromptLab doesn't need storage (everything is in-memory/deterministic), but LLMMap CLI scan runs would be lost on redeploy.
