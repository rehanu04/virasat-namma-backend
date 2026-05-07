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

app = FastAPI(title="Virasat-Namma Production API", version="2.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Flagship Heritage Database ──────────────────────────────────────────
SITES_DB = {
    "site_001": {"name": "Bangalore Palace", "lat": 12.9988, "lon": 77.5921},
    "site_002": {"name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5912},
    "site_003": {"name": "Tipu Sultan's Summer Palace", "lat": 12.9593, "lon": 77.5738},
    "site_004": {"name": "Hampi (Virupaksha Temple)", "lat": 15.3350, "lon": 76.4600},
    "site_005": {"name": "Mysore Palace", "lat": 12.3051, "lon": 76.6551},
    "site_006": {"name": "Belur Chennakesava Temple", "lat": 13.1623, "lon": 75.8596},
    "site_007": {"name": "Halebidu Hoysaleswara", "lat": 13.2120, "lon": 75.9942},
    "site_008": {"name": "Pattadakal Monuments", "lat": 15.9490, "lon": 75.8164},
    "site_009": {"name": "Gol Gumbaz (Vijayapura)", "lat": 16.8301, "lon": 75.7360},
    "site_010": {"name": "Shravanabelagola (Gommateshwara)", "lat": 12.8573, "lon": 76.4819},
}

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health_check():
    """Satisfies Render's health check requirement."""
    return {"status": "healthy", "service": "Virasat Historian AI"}

@app.post("/api/chat")
async def agent_chat(request: ChatRequest):
    """
    AI Historian Recovery: Responds to greetings and provides heritage insights.
    """
    model = get_ai_client()
    if not model: return {"response": "Brain offline (API Key Missing)."}
    
    system_instruction = (
        "You are the 'Virasat Historian'. You respond warmly to all greetings. "
        "You provide deep historical context about Karnataka's heritage. "
        "If a user wants to visit a site, include [NAVIGATE:site_id] in your response. "
        "Sites: site_001 to site_010."
    )
    try:
        res = model.generate_content(f"{system_instruction}\nUser: {request.message}")
        return {"response": res.text.strip()}
    except:
        return {"response": "Namaskara! I am currently consulting the archives. Please ask again in a moment."}

@app.get("/api/heritage/scan")
async def scan_heritage(site_id: str):
    model = get_ai_client()
    site_info = SITES_DB.get(site_id, {"name": "this monument"})
    site_name = site_info["name"]
    try:
        res = model.generate_content(f"One non-obvious historical fact about {site_name}. One sentence.")
        return {"hidden_fact": res.text.strip()}
    except:
        return {"hidden_fact": f"{site_name} is a cornerstone of Namma Bengaluru's history."}

@app.get("/api/heritage/{site_id}")
async def get_site_history(site_id: str):
    model = get_ai_client()
    site_info = SITES_DB.get(site_id, {"name": "this site"})
    try:
        response = model.generate_content(f"History of {site_info['name']}. Return JSON: 'history_en', 'history_kn'.")
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except:
        return {"history_en": "Data indexed.", "history_kn": "ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v["name"], "latitude": v["lat"], "longitude": v["lon"]} for k, v in SITES_DB.items()]}

if __name__ == "__main__":
    import uvicorn
    # Flagship Fix: Explicit Port Binding for Render Deployment
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
