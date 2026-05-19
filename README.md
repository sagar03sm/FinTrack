# FinTrack — AI-Powered Finance & Expense Tracking Platform

> EdgeFleet.AI Full-Stack Engineering Assessment submission.

A modern finance tracker with authentication, expense/income management, analytics, AI-generated financial summaries, and an AI chatbot assistant.

## Stack

- **Frontend**: Next.js 14 (App Router) + TypeScript + TailwindCSS + TanStack Query
- **Backend**: FastAPI (Python 3.11) + Beanie ODM + Motor (async MongoDB)
- **Database**: MongoDB (local `mongod` or **MongoDB Atlas** free tier)
- **AI**: Groq (`llama-3.3-70b-versatile`) with tool/function calling for the chatbot. OpenAI supported as fallback.
- **Deploy**: Vercel (web) + Render/Fly (api) + MongoDB Atlas (db)

## Repository Layout

```
Fintrack/
├── apps/
│   ├── api/          # FastAPI service
│   └── web/          # Next.js app
├── .env.example
└── README.md
```

## Prerequisites

- **Node.js 20+** — https://nodejs.org/ (or `brew install node`)
- **Python 3.11+** — https://www.python.org/ (or `brew install python@3.11`)
- **MongoDB** — pick one:
  - **MongoDB Atlas (recommended, no install)** — free M0 cluster at https://www.mongodb.com/atlas
  - **Local** — `brew install mongodb-community` then `brew services start mongodb-community`

## Setup

```bash
# 1. Configure environment
cp .env.example .env
# Edit .env and set MONGO_URI (Atlas connection string or local) and GROQ_API_KEY
```

### Backend (FastAPI)
```bash
cd apps/api
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
uvicorn app.main:app --reload
```
- API: http://localhost:8000
- Swagger docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

### Frontend (Next.js)
```bash
cd apps/web
npm install
npm run dev
```
- Web: http://localhost:3000

## Environment Variables

See [`.env.example`](.env.example). Required for full functionality:
- `MONGO_URI` — Mongo connection string (local or Atlas `mongodb+srv://...`)
- `JWT_SECRET` — random secret for signing tokens
- `GROQ_API_KEY` — for AI summary + chatbot features (free at https://console.groq.com). `OPENAI_API_KEY` works as fallback.

## Tests

```bash
# Backend
cd apps/api && pytest -q

# Frontend
cd apps/web && npm run lint && npm run typecheck && npm run build
```

## Deployment

- **Web** → Vercel (import the `apps/web` directory; set `NEXT_PUBLIC_API_URL` to the deployed API URL)
- **API** → Render / Fly.io / Railway (point to `apps/api`, run `uvicorn app.main:app --host 0.0.0.0 --port $PORT`)
- **DB** → MongoDB Atlas (free M0 cluster; whitelist API host or use `0.0.0.0/0` for assessment)

## Features

- ✅ JWT auth (access + refresh tokens) with role-based access control
- ✅ Transactions / Categories / Budgets CRUD with validation
- ✅ Analytics dashboard with Recharts (pie + bar + monthly trend)
- ✅ Search + filter on transactions
- ✅ Dark/Light theme toggle
- ✅ AI Financial Summary Generator (weekly/monthly)
- ✅ AI Chatbot Assistant with tool calling (Groq)
- ✅ **Bonus**: AI-powered category suggestion from transaction notes
- ✅ **Bonus**: Real-time budget threshold notifications (toast warnings at 80%, errors at 100%)
- ✅ Rate limiting (slowapi, 120 req/min)
- ✅ OpenAPI / Swagger docs at `/docs`
- ✅ Structured JSON logging
- ✅ INR (₹) currency formatting throughout

## License
For assessment purposes only.
