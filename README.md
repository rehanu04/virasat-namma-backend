# Virasat-Namma Guide — Python Backend

A production-ready FastAPI backend for the Virasat-Namma heritage guide application.

## Setup & Run Locally

```bash
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

API docs will be available at: `http://localhost:8000/docs`

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/api/heritage` | List all heritage sites |
| POST | `/api/unlock` | Unlock a site (saves stamp to Supabase) |
| GET | `/api/stamps/{user_email}` | Get a user's passport stamps |

## Supabase Table Required

Create the `user_passport` table in your Supabase project:

```sql
CREATE TABLE user_passport (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_email TEXT NOT NULL,
  site_id TEXT NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## Deploy to Render

1. Push this folder to a GitHub repository.
2. Create a new **Web Service** on [render.com](https://render.com).
3. Build Command: `pip install -r requirements.txt`
4. Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`
