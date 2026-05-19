# FinTrack Technical Report

## Project Overview

FinTrack is an AI-powered finance and expense tracking platform built with a modern full-stack architecture. The application enables users to track income and expenses, set budgets, and receive AI-powered financial insights.

## Technology Stack

### Frontend
- **Framework**: Next.js 14 (App Router)
- **Language**: TypeScript
- **Styling**: TailwindCSS
- **UI Components**: shadcn/ui (Radix UI primitives)
- **State Management**: TanStack Query (React Query)
- **Charts**: Recharts
- **Notifications**: Sonner (toast)
- **Deployment**: Vercel

### Backend
- **Framework**: FastAPI
- **Language**: Python 3.11
- **Database**: MongoDB (Atlas)
- **ODM**: Beanie (async MongoDB driver)
- **Authentication**: JWT (access + refresh tokens)
- **AI**: Groq API (llama-3.3-70b-versatile) with OpenAI fallback
- **Logging**: Structlog (JSON logs)
- **Rate Limiting**: slowapi
- **Deployment**: Render/Fly

## Architecture

### Design Pattern: Hexagonal (Clean Architecture)

The backend follows a hexagonal architecture pattern with clear separation of concerns:

```
app/
├── core/                    # Cross-cutting concerns
│   ├── config.py           # Configuration management
│   ├── logging.py          # Structured logging setup
│   ├── middleware.py       # Request ID middleware
│   ├── rate_limit.py       # Rate limiting
│   ├── security.py         # JWT token operations
│   └── errors.py           # Domain exceptions
├── modules/                 # Feature modules
│   ├── auth/
│   │   ├── domain/         # Protocols (not used in this pragmatic implementation)
│   │   ├── application/    # Services and DTOs
│   │   ├── infrastructure/ # Beanie models and repositories
│   │   └── interfaces/http/# FastAPI routers and deps
│   ├── users/
│   ├── categories/
│   ├── transactions/
│   ├── budgets/
│   ├── analytics/
│   └── chat/
├── db.py                    # Database initialization
└── main.py                  # Composition root
```

### Layer Responsibilities

**Core Layer**
- Configuration management with Pydantic Settings
- Structured JSON logging with request correlation
- JWT token generation and validation
- Rate limiting per endpoint
- Domain exception to HTTP error translation

**Module Layers**

1. **Domain** (`domain/`): Defines protocols/interfaces (repository contracts)
2. **Application** (`application/`): Business logic, DTOs, service orchestration
3. **Infrastructure** (`infrastructure/`): Beanie ODM models, MongoDB repository implementations
4. **Interfaces** (`interfaces/http/`): FastAPI routers, dependency injection factories

### Data Flow

```
HTTP Request → Router → Service → Repository → MongoDB
                    ↓
                 DTOs (validation)
                    ↓
                 Domain Exceptions → Error Handler → HTTP Response
```

## Database Schema

### Collections

**users**
```python
{
  "email": str (unique),
  "password_hash": str,
  "name": str,
  "role": "user" | "admin",
  "is_active": bool,
  "created_at": datetime
}
Indexes: email (unique)
```

**categories**
```python
{
  "user_id": ObjectId,
  "name": str,
  "type": "income" | "expense",
  "icon": str,
  "color": str,
  "is_default": bool,
  "created_at": datetime
}
Indexes: user_id+name (unique), user_id+type
```

**transactions**
```python
{
  "user_id": ObjectId,
  "type": "income" | "expense",
  "amount": float,
  "currency": str,
  "category_id": ObjectId,
  "category_name": str,  # denormalized
  "note": str | null,
  "date": datetime,
  "created_at": datetime
}
Indexes: user_id+date, user_id+category_id+date, user_id+type+date
```

**budgets**
```python
{
  "user_id": ObjectId,
  "category_id": ObjectId,
  "month": str (YYYY-MM),
  "limit": float,
  "created_at": datetime
}
Indexes: user_id+month+category_id (unique)
```

## API Endpoints

### Authentication
- `POST /auth/register` — User registration with default category seeding
- `POST /auth/login` — Login with email/password, returns JWT tokens
- `POST /auth/refresh` — Refresh access token
- `POST /auth/logout` — Logout (client-side token deletion)

### Categories
- `GET /categories?type=income|expense` — List user's categories
- `POST /categories` — Create custom category
- `PATCH /categories/{id}` — Update category
- `DELETE /categories/{id}` — Delete (rejects if transactions reference it)

### Transactions
- `GET /transactions?type=&category_id=&date_from=&date_to=&limit=&skip=` — List with filters and pagination
- `POST /transactions` — Create transaction with category validation and denormalization
- `POST /transactions/suggest-category` — **AI-powered category suggestion** from a note + type
- `GET /transactions/{id}` — Fetch single transaction
- `PATCH /transactions/{id}` — Update transaction
- `DELETE /transactions/{id}` — Delete transaction

### Budgets
- `GET /budgets?month=YYYY-MM` — List budgets for month
- `POST /budgets` — Upsert by (month, category_id)
- `DELETE /budgets/{id}` — Delete budget

### Analytics
- `GET /analytics/summary?date_from=&date_to=` — Total income/expense/net/tx count
- `GET /analytics/by-category?date_from=&date_to=` — Breakdown per category
- `GET /analytics/monthly-trend?months=` — Last N months income/expense/net
- `GET /analytics/budget-progress?month=` — Budget progress per category

### Chat (AI)
- `POST /chat` — Conversational AI with tool-calling for financial data
- `POST /chat/summary` — AI-generated financial summary (week/month/quarter/year)

### Meta
- `GET /health` — Application health with version
- `GET /ready` — Dependency health (database, AI provider)

## Security

### Authentication
- Password hashing with bcrypt (pinned <4.1 for compatibility)
- JWT access tokens (15min TTL) and refresh tokens (7 days TTL)
- Token type validation in JWT payload
- Auto-refresh on 401 responses

### Authorization
- All protected routes require valid JWT via `get_current_user` dependency
- User-scoped queries (all operations filtered by user_id)
- Category ownership validation before transaction creation/update

### Rate Limiting
- slowapi with default limits
- Per-endpoint configuration available
- 429 response on rate limit exceeded

### CORS
- Configured whitelist via `CORS_ORIGINS`
- Methods: GET, POST, PATCH, DELETE, OPTIONS
- Headers: Content-Type, Authorization, X-Request-ID
- Credentials: enabled for JWT cookies (if used)

### Input Validation
- Pydantic models with field validators
- Amount limits (transaction: 10M INR, budget: 100M INR)
- Currency: 3-char validation
- Note: max 500 chars
- Month format: YYYY-MM regex validation

## Performance

### Database Indexing
- All frequently queried fields have compound indexes
- Unique indexes prevent duplicates (email, category name, budget keys)
- Date fields indexed descending for time-series queries

### Pagination
- Transaction list: limit (1-200), skip (>=0)
- Prevents large result sets from overloading memory

### Caching
- TanStack Query caches API responses in frontend
- Configurable stale time and cache time

### Denormalization
- `category_name` stored in transactions for fast reads without $lookup
- Trade-off: requires update on category rename (not implemented)

## Observability

### Logging
- Structlog with JSON output
- Request ID middleware for correlation
- Contextual logging in services (user_id, transaction_id, etc.)
- Log levels: INFO (default), configurable via LOG_LEVEL

### Health Checks
- `/health` — Basic health with version
- `/ready` — Dependency health (database ping, OpenAI key check)

### Error Handling
- Domain exceptions (NotFoundError, ValidationError, ConflictError)
- Global exception handler translates to HTTP responses
- Error codes included in response for client handling

## AI Integration

### Tool-Calling
The chat service uses Groq's (OpenAI-compatible) function calling to access real financial data:

**Available Tools**
1. `get_transactions_summary` — Fetch transaction totals for date range
2. `get_category_breakdown` — Spending by category
3. `get_budget_progress` — Budget status for month

**Flow**
1. User sends message via `/chat` endpoint
2. Groq LLM (llama-3.3-70b-versatile) decides which tools to call
3. Backend executes tools against MongoDB (user-scoped queries)
4. Tool results returned with INR (₹) formatted amounts
5. AI generates natural language response in INR

### Provider Selection
- Service prefers `GROQ_API_KEY` if present (free, fast inference)
- Falls back to `OPENAI_API_KEY` if Groq not configured
- Uses AsyncOpenAI client with Groq's OpenAI-compatible endpoint

### Summary Generation
- Period-based summaries (week, month, quarter, year)
- `date_from` set to midnight to include first-of-month transactions
- Aggregates summary, category breakdown, and budget progress
- System prompt enforces INR currency and current date awareness
- Returns concise recommendations (<200 words)

### AI-Powered Categorization (Bonus)
- Endpoint: `POST /transactions/suggest-category`
- Fetches the user's categories filtered by transaction type
- Sends the note + candidate category names to Groq with temperature 0
- Matches LLM response back to a category (exact → partial → none)
- Returns `{category_id, category_name, confidence}` where confidence is `high|medium|low`
- Frontend exposes this via a "Suggest" button beside the Note field; toast confirms the choice

### Real-Time Budget Notifications (Bonus)
- After every expense creation, the frontend re-queries `/analytics/budget-progress` for that month
- Toast warning (yellow) at ≥80% of budget; toast error (red) at ≥100%
- Implemented with Sonner; non-blocking and best-effort (failures swallowed silently)
- No websockets required — leverages existing analytics endpoint for simplicity and zero added infra

## Testing

### Backend Tests
- Unit tests for security (JWT hashing, token generation)
- Health check tests
- Located in `tests/` directory

### E2E Tests
- Playwright configuration
- Auth flow tests (register, login, redirect)
- Transaction flow tests (create, list, delete)
- Run with `npm run test:e2e` in `apps/web`

## Deployment

### Backend (Render/Fly)
- Build: `pip install -e .`
- Start: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- Environment variables: MongoDB URI, JWT secret, Groq/OpenAI key, CORS origins

### Frontend (Vercel)
- Root directory: `apps/web`
- Build: `npm run build`
- Environment variable: `NEXT_PUBLIC_API_URL`

### Database
- MongoDB Atlas free tier
- IP whitelisting for backend host
- Connection string with retry writes

## Future Improvements

### Security
- Add refresh token rotation
- Implement password reset flow
- Add 2FA support
- Expand admin RBAC endpoints (role infrastructure already in place via `require_admin`)

### Features
- Category rename with transaction denormalization update
- Recurring transactions
- File attachment support (receipts)
- Export to CSV/PDF
- Multi-currency support with conversion

### Performance
- Add Redis caching for frequently accessed data
- Implement read replicas for MongoDB
- Add CDN for static assets
- Optimize analytics aggregations

### Monitoring
- Add error tracking (Sentry)
- Implement metrics collection (Prometheus)
- Add distributed tracing
- Set up alerting

## Cost Summary (Free Tier)

- **MongoDB Atlas**: Free (512MB storage)
- **Render**: Free (750 hours/month)
- **Vercel**: Free (100GB bandwidth/month)
- **Groq**: Free tier (generous rate limits)
- **OpenAI** (optional fallback): Pay-as-you-go (~$0.15/1M tokens)

Total: $0/month with Groq

## Product Decisions and Tradeoffs

### Why Groq over OpenAI?
Groq offers an OpenAI-compatible API with the open-source `llama-3.3-70b-versatile` model at zero cost and faster inference than gpt-4o-mini. The service is implemented with fallback to OpenAI to keep flexibility.

### Why MongoDB?
Financial data is naturally document-oriented (transactions, budgets per user). Beanie ODM provides Pydantic-native models that flow cleanly through validation, business logic, and serialization without translation layers.

### Denormalization of `category_name`
Stored on each transaction to avoid `$lookup` joins for list views. Tradeoff: a category rename requires fan-out update (not implemented; acceptable as categories are rarely renamed).

### Hexagonal Architecture
Clear separation of `domain` / `application` / `infrastructure` / `interfaces` allows testing services with in-memory fakes (see `tests/`). Tradeoff: more boilerplate per module, but pays off as the codebase grows.

### Date Handling in AI Tools
Tool schemas accept `YYYY-MM-DD` (Groq's preferred format). Backend normalizes both `YYYY-MM-DD` and ISO 8601. The summary endpoint resets `date_from` to midnight so transactions on the first of the month are not excluded — a bug discovered and fixed during testing.

## Challenges Faced

1. **Groq date format mismatch**: Tool schemas originally specified `date-time` format; Groq returned `YYYY-MM-DD`. Resolved by accepting both formats in backend parsing.
2. **Date filter exclusion bug**: Monthly summary used `now.replace(day=1)` which kept the current time, accidentally excluding transactions dated `2026-05-01 00:00:00`. Fixed by setting time to midnight.
3. **AI currency display**: LLM defaulted to dollars despite system prompt. Fixed by explicitly formatting tool return values with `₹` prefix.
4. **Double submission on Enter**: Form's native submit + custom `onKeyDown` triggered the handler twice. Resolved by relying on form submit only and adding an `isSubmitting` guard.
5. **Stale closure in summary mutation**: `onSuccess` referenced an old `conversation` snapshot. Fixed with functional `setConversation((prev) => ...)`.

## Future Scalability Considerations

- **Read replicas** for MongoDB once query volume grows
- **Redis** for caching analytics aggregations and AI tool results
- **Background jobs** (e.g., Arq/Celery) for periodic summary precomputation
- **CDN** for static assets via Vercel/Cloudflare
- **Sharding** by `user_id` if user count scales horizontally
- **Event sourcing** for transaction audit trail

## Conclusion

FinTrack demonstrates a production-ready full-stack application with:
- Clean hexagonal architecture
- Comprehensive security (JWT, RBAC, rate limiting, CORS, input validation)
- AI-powered insights via Groq with tool calling
- Bonus: AI-powered category suggestion + real-time budget threshold notifications
- Modern UI with shadcn/ui, dark/light theme, search + filtering
- E2E testing with Playwright
- Deployment-ready configuration (Vercel + Render + MongoDB Atlas)

The application is ready for deployment to production environments.
