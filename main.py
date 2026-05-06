from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client
import os
import google.generativeai as genai

# ─── Supabase Configuration ─────────────────────────────────────────────────
SUPABASE_URL = "https://dvhsmxtcuxvmaiaqmxww.supabase.co"
SUPABASE_ANON_KEY = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImR2aHNteHRjdXh2bWFpYXFteHd3Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzgwNjczNTEsImV4cCI6MjA5MzY0MzM1MX0."
    "Goptbzxwb7Q6XScuuBGpenN1KYcgPHQc4UwG3evFZtg"
)

supabase: Client = create_client(SUPABASE_URL, SUPABASE_ANON_KEY)

# ─── Gemini AI Configuration ────────────────────────────────────────────────
# CRITICAL: Client initialized using environment variable for security
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

# ─── FastAPI App ─────────────────────────────────────────────────────────────
app = FastAPI(
    title="Virasat-Namma Guide API",
    description="Backend API for the Virasat-Namma heritage guide application.",
    version="1.1.0",
)

# ─── CORS Middleware ─────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Hardcoded Heritage Sites Data ──────────────────────────────────────────
HERITAGE_SITES = [
    {
        "id": "site_001",
        "name": "Bangalore Palace",
        "description": (
            "A stunning Tudor-style palace built in 1887, inspired by England's Windsor Castle. "
            "The palace boasts fortified towers, wood carvings, and a serene sprawling estate."
        ),
        "latitude": 12.9988,
        "longitude": 77.5921,
        "qr_code_value": "VIRASAT_SITE_001",
        "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3",
        "image_hint": "palace architecture",
    },
    {
        "id": "site_002",
        "name": "Vidhana Soudha",
        "description": (
            "The seat of Karnataka's state legislature, Vidhana Soudha is a monumental "
            "Neo-Dravidian granite structure completed in 1956. An icon of modern Karnataka."
        ),
        "latitude": 12.9793,
        "longitude": 77.5909,
        "qr_code_value": "VIRASAT_SITE_002",
        "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-2.mp3",
        "image_hint": "government building",
    },
    {
        "id": "site_003",
        "name": "Tipu Sultan's Summer Palace",
        "description": (
            "An exquisite example of Indo-Islamic architecture, this teak-wood palace served as "
            "the summer retreat of the legendary ruler Tipu Sultan in the 18th century."
        ),
        "latitude": 12.9601,
        "longitude": 77.5736,
        "qr_code_value": "VIRASAT_SITE_003",
        "audio_url": "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-3.mp3",
        "image_hint": "historical palace",
    },
]

# ─── Pydantic Models ─────────────────────────────────────────────────────────
class UnlockRequest(BaseModel):
    user_email: str
    site_id: str

class InsightRequest(BaseModel):
    site_name: str


# ─── Routes ─────────────────────────────────────────────────────────────────
@app.get("/", tags=["Health"])
async def root():
    return {"status": "online", "message": "Virasat-Namma Guide API is running."}


@app.get("/api/heritage", tags=["Heritage"])
async def get_heritage_sites():
    """Returns a list of all heritage sites in the guide."""
    return {"sites": HERITAGE_SITES}


@app.post("/api/unlock", tags=["Passport"])
async def unlock_site(request: UnlockRequest):
    """
    Records a heritage site unlock for a given user.
    Inserts a record into the 'user_passport' table in Supabase.
    """
    try:
        # Check if already unlocked to avoid duplicates
        existing = (
            supabase.table("user_passport")
            .select("id")
            .eq("user_email", request.user_email)
            .eq("site_id", request.site_id)
            .execute()
        )
        if existing.data:
            return {
                "success": True,
                "message": "Site already unlocked.",
                "already_existed": True,
            }

        # Insert new passport stamp
        result = (
            supabase.table("user_passport")
            .insert({"user_email": request.user_email, "site_id": request.site_id})
            .execute()
        )
        return {
            "success": True,
            "message": f"Site '{request.site_id}' successfully unlocked for {request.user_email}!",
            "data": result.data,
            "already_existed": False,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/api/stamps/{user_email}", tags=["Passport"])
async def get_stamps(user_email: str):
    """
    Fetches all unlocked passport stamps for a given user email.
    """
    try:
        result = (
            supabase.table("user_passport")
            .select("*")
            .eq("user_email", user_email)
            .execute()
        )
        stamps_raw = result.data or []

        # Enrich stamps with site details
        site_map = {site["id"]: site for site in HERITAGE_SITES}
        enriched = []
        for stamp in stamps_raw:
            site_info = site_map.get(stamp.get("site_id"), {})
            enriched.append({
                "stamp_id": stamp.get("id"),
                "site_id": stamp.get("site_id"),
                "unlocked_at": stamp.get("created_at"),
                "site_name": site_info.get("name", "Unknown Site"),
                "site_description": site_info.get("description", ""),
                "image_hint": site_info.get("image_hint", "heritage"),
            })

        return {"user_email": user_email, "stamps": enriched}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/api/insights", tags=["AI"])
async def get_heritage_insight(request: InsightRequest):
    """
    Uses Gemini AI to generate a short, fascinating historical fact about a site.
    """
    if not model:
        return {"insight": "AI Insights are currently unavailable. Please check backend configuration."}
    
    try:
        prompt = f"Provide a fascinating, short (maximum 2 sentences) historical fact about {request.site_name} in Bangalore. Make it engaging for a tourist."
        response = model.generate_content(prompt)
        return {"insight": response.text.strip()}
    except Exception as e:
        return {"insight": f"Unable to generate insight at this moment."}
