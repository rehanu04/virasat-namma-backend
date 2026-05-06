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
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

app = FastAPI(title="Virasat-Namma Guide API", version="1.3.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Narrative Content (Strictly No Music) ──────────────────────────────────
HERITAGE_SITES = [
    {
        "id": "site_001",
        "name": "Bangalore Palace",
        "description": "Inspired by Windsor Castle, this Tudor-style palace features fortified towers, wood carvings, and floral motifs. It represents the royal grandeur of the Wodeyar dynasty.",
        "latitude": 12.9988,
        "longitude": 77.5921,
        "qr_code_value": "BNG_PALACE_001", # Demo ID
        "audio_url": "https://storage.googleapis.com/gtv-videos-bucket/sample/BigBuckBunny.mp4", # Narrative placeholder
        "image_hint": "palace",
    },
    {
        "id": "site_002",
        "name": "Vidhana Soudha",
        "description": "Built in the Neo-Dravidian style, this is the largest legislative building in India. Its majestic dome and granite architecture symbolize Karnataka's democratic pride.",
        "latitude": 12.9793,
        "longitude": 77.5909,
        "qr_code_value": "BNG_SOUDHA_002", # Demo ID
        "audio_url": "https://www.learningcontainer.com/wp-content/uploads/2020/02/Kalimba.mp3", # Narrative placeholder
        "image_hint": "government",
    },
    {
        "id": "site_003",
        "name": "Tipu Sultan's Summer Palace",
        "description": "Known as 'Rash-e-Jannat' (Envy of Heaven), this teak-wood palace is a masterpiece of Indo-Islamic architecture with exquisite carvings and frescos.",
        "latitude": 12.9601,
        "longitude": 77.5736,
        "qr_code_value": "BNG_TIPU_003", # Demo ID
        "audio_url": "https://file-examples.com/wp-content/storage/2017/11/file_example_MP3_700KB.mp3", # Narrative placeholder
        "image_hint": "historical",
    },
]

class UnlockRequest(BaseModel):
    user_email: str
    site_id: str

class InsightRequest(BaseModel):
    site_name: str

@app.get("/")
async def root(): return {"status": "online", "version": "1.3.0"}

@app.get("/api/heritage")
async def get_heritage_sites():
    return {"sites": HERITAGE_SITES}

@app.post("/api/unlock")
async def unlock_site(request: UnlockRequest):
    try:
        supabase.table("user_passport").insert({"user_email": request.user_email, "site_id": request.site_id}).execute()
        return {"success": True, "message": f"Site {request.site_id} unlocked!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/stamps/{user_email}")
async def get_stamps(user_email: str):
    result = supabase.table("user_passport").select("*").eq("user_email", user_email).execute()
    stamps = []
    site_map = {site["id"]: site for site in HERITAGE_SITES}
    for item in result.data:
        site = site_map.get(item["site_id"], {})
        stamps.append({
            "site_id": item["site_id"],
            "site_name": site.get("name", "Unknown"),
            "unlocked_at": item["created_at"]
        })
    return {"stamps": stamps}

@app.post("/api/insights")
async def get_insight(request: InsightRequest):
    if not model: return {"insight": "AI Guide offline."}
    prompt = f"Fascinating historical fact about {request.site_name} in Bangalore. 2 short sentences."
    response = model.generate_content(prompt)
    return {"insight": response.text.strip()}
