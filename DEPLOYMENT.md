# Deployment Guide

FinTrack deployment guide for production environments.

## Architecture Overview

- **Frontend**: Next.js 14 (Vercel)
- **Backend**: FastAPI (Render/Fly)
- **Database**: MongoDB Atlas
- **AI**: Groq API (llama-3.3-70b-versatile) — free, fast inference. Falls back to OpenAI if configured.

## Prerequisites

1. MongoDB Atlas account with a free-tier cluster
2. Groq API key (free at https://console.groq.com) — or OpenAI API key
3. Vercel account (for frontend)
4. Render or Fly account (for backend)

## Environment Variables

### Backend (.env)

```bash
# Database
MONGO_URI=mongodb+srv://<user>:<password>@<cluster>.mongodb.net/fintrack?retryWrites=true&w=majority
MONGO_DB=fintrack

# Security
JWT_SECRET=<strong-random-string>
JWT_ACCESS_TTL_SECONDS=900
JWT_REFRESH_TTL_SECONDS=604800

# AI (Groq preferred — free)
GROQ_API_KEY=gsk_...
GROQ_MODEL=llama-3.3-70b-versatile
GROQ_BASE_URL=https://api.groq.com/openai/v1

# OpenAI fallback (optional)
OPENAI_API_KEY=
OPENAI_MODEL=gpt-4o-mini

# CORS
CORS_ORIGINS=https://your-frontend-domain.vercel.app

# Config
LOG_LEVEL=INFO
ENV=production
```

### Frontend (.env.local / Vercel Environment Variables)

```bash
NEXT_PUBLIC_API_URL=https://your-backend-domain.onrender.com
```

## Backend Deployment (Render)

### 1. Prepare Backend

The backend is already configured for production with:
- Structured logging (JSON)
- Health check endpoints (`/health`, `/ready`)
- Rate limiting
- CORS configuration
- Database indexes

### 2. Deploy to Render

1. Create a new Web Service on Render
2. Connect to GitHub repository
3. Configure build settings:
   - **Build Command**: `pip install -e .`
   - **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
4. Add environment variables (see above)
5. Deploy

### Alternative: Fly.io

```bash
# Install Fly CLI
curl -L https://fly.io/install.sh | sh

# Login
fly auth login

# Initialize
fly launch

# Set environment variables
fly secrets set MONGO_URI="..." JWT_SECRET="..." GROQ_API_KEY="..."

# Deploy
fly deploy
```

## Frontend Deployment (Vercel)

### 1. Prepare Frontend

The frontend is already configured with:
- TypeScript
- TailwindCSS
- Environment variable support
- Production build optimization

### 2. Deploy to Vercel

1. Connect GitHub repository to Vercel
2. Import the `apps/web` directory
3. Configure root directory: `apps/web`
4. Add environment variable:
   - `NEXT_PUBLIC_API_URL`: Your backend URL
5. Deploy

### Vercel Configuration

Create `apps/web/vercel.json` if needed:

```json
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "framework": "nextjs"
}
```

## MongoDB Atlas Setup

1. Create a free-tier cluster
2. Create database user with read/write permissions
3. Get connection string
4. Whitelist IP addresses (0.0.0.0/0 for Render/Fly, or use VPC peering)

## Post-Deployment Checklist

- [ ] Backend health check returns 200: `https://<backend>/health`
- [ ] Backend ready check shows dependencies: `https://<backend>/ready`
- [ ] Frontend loads and redirects to login if not authenticated
- [ ] User can register and login
- [ ] Transactions can be created and listed
- [ ] Budgets can be set up
- [ ] Analytics charts render correctly
- [ ] AI chat responds (if Groq/OpenAI API key configured)
- [ ] AI "Suggest" button on transaction form returns a category
- [ ] Budget threshold toast appears when an expense crosses 80% / 100% of its budget

## Monitoring

### Backend Logs

- **Render**: Dashboard → Logs
- **Fly**: `fly logs`

### Frontend Logs

- **Vercel**: Dashboard → Logs

### Health Checks

Set up uptime monitoring for:
- `GET /health` - Application health
- `GET /ready` - Dependency health

## Scaling Considerations

### Backend
- Render: Scale CPU/RAM based on traffic
- Fly: Scale regions and instances

### Database
- MongoDB Atlas: Scale cluster size based on data size
- Consider read replicas for high traffic

### Frontend
- Vercel: Automatic scaling with edge network
- Consider CDN for static assets

## Security Notes

1. **JWT Secret**: Use a strong, random string in production
2. **CORS**: Whitelist only your frontend domain
3. **Rate Limiting**: Configured with slowapi (adjust limits as needed)
4. **Database**: Use strong password for MongoDB user
5. **API Keys**: Never commit secrets to git

## Troubleshooting

### Backend won't start
- Check environment variables are set
- Verify MongoDB connection string is correct
- Check logs for startup errors

### Frontend can't connect to backend
- Verify `NEXT_PUBLIC_API_URL` is correct
- Check CORS configuration
- Ensure backend is accessible

### MongoDB connection fails
- Verify IP whitelist includes backend host
- Check database user permissions
- Verify connection string format

## Cost Estimate (Free Tier)

- **MongoDB Atlas**: Free (512MB storage)
- **Render**: Free (750 hours/month, limited RAM)
- **Vercel**: Free (100GB bandwidth/month)
- **Groq**: Free tier with generous rate limits
- **OpenAI** (optional fallback): Pay-as-you-go (~$0.15/1M tokens for gpt-4o-mini)

Total: $0/month for small-scale usage with Groq.
