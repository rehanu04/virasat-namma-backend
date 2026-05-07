from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import math
import json
import google.generativeai as genai

# ─── Gemini AI Singleton ───────────────────────────────────────────────────
_ai_client = None

def get_ai_client():
    global _ai_client
    if _ai_client is None:
        gemini_key = os.getenv("GEMINI_API_KEY")
        if gemini_key:
            genai.configure(api_key=gemini_key)
            _ai_client = genai.GenerativeModel('gemini-1.5-flash')
    return _ai_client

app = FastAPI(title="Virasat-Namma Production Final", version="3.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Heritage Metadata (Flagship Database) ──────────────────────────────
SITES_DB = {
    "site_001": {"name": "Bangalore Palace", "lat": 12.9988, "lon": 77.5921},
    "site_002": {"name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5912},
    "site_003": {"name": "Tipu Sultan's Summer Palace", "lat": 12.9593, "lon": 77.5738},
    "site_004": {"name": "Hampi (Virupaksha Temple)", "lat": 15.3350, "lon": 76.4600},
}

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health():
    return {"status": "healthy", "service": "Virasat Historian"}

@app.post("/api/chat")
async def agent_chat(request: ChatRequest):
    """
    Virasat Historian: The 'Archives' Fix Update.
    Instructed to respond immediately to all greetings and queries.
    """
    model = get_ai_client()
    if not model: return {"response": "The Historian is temporarily unavailable."}
    
    system_instruction = (
        "You are the 'Virasat Historian'. Respond to all greetings immediately. "
        "DO NOT say you are consulting archives or looking for scrolls. "
        "Provide specific historical facts about Karnataka's heritage sites. "
        "Keep responses concise and engaging. Use [NAVIGATE:site_id] for location tags."
    )
    try:
        res = model.generate_content(f"{system_instruction}\nUser: {request.message}")
        return {"response": res.text.strip()}
    except:
        return {"response": "Namaskara! How can I help you explore Karnataka's rich history today?"}

@app.get("/api/heritage/scan")
async def scan_fact(site_id: str):
    model = get_ai_client()
    site_name = SITES_DB.get(site_id, {"name": "this site"})["name"]
    try:
        res = model.generate_content(f"One unique historical secret about {site_name}. One sentence.")
        return {"hidden_fact": res.text.strip()}
    except:
        return {"hidden_fact": f"{site_name} whispers legends of a glorious era."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v["name"], "latitude": v["lat"], "longitude": v["lon"]} for k, v in SITES_DB.items()]}

if __name__ == "__main__":
    import uvicorn
    # PRODUCTION FIX: Strict Port Binding for Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
