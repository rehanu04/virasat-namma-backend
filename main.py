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

app = FastAPI(title="Virasat-Namma Explorer API", version="2.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Flagship Heritage Database (10 Major Sites) ──────────────────────────
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

@app.post("/api/chat")
async def agent_chat(request: ChatRequest):
    """
    Virasat Historian: Recovery Update.
    The AI is now instructed to be welcoming and provide deep insights.
    """
    model = get_ai_client()
    if not model: return {"response": "The archives are currently unreachable (API Key Missing)."}
    
    system_instruction = (
        "You are the 'Virasat Historian', a wise and welcoming guide to Karnataka's heritage. "
        "You have full access to Karnataka's historical database including sites like "
        "Hampi, Mysore Palace, and Bangalore's monuments. "
        "Respond warmly to greetings. Provide deep, scholarly insights but keep them engaging. "
        "If a user asks to go to a site, use [NAVIGATE:site_id] where site_id is site_001 to site_010."
    )
    
    try:
        res = model.generate_content(f"{system_instruction}\nUser: {request.message}")
        return {"response": res.text.strip()}
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"response": "I am currently meditating on the scrolls of history. Please try again in a moment."}

@app.get("/api/heritage/scan")
async def scan_heritage(site_id: str):
    model = get_ai_client()
    site_info = SITES_DB.get(site_id, {"name": "this monument"})
    site_name = site_info["name"]
    
    prompt = f"Provide one surprising, non-obvious historical fact about {site_name}. One sentence only."
    try:
        res = model.generate_content(prompt)
        return {"hidden_fact": res.text.strip()}
    except:
        return {"hidden_fact": f"The stones of {site_name} whisper secrets of a golden age."}

@app.get("/api/heritage/{site_id}")
async def get_site_history(site_id: str):
    model = get_ai_client()
    site_info = SITES_DB.get(site_id, {"name": "this site"})
    site_name = site_info["name"]
    try:
        response = model.generate_content(f"Deep history of {site_name}. Return JSON: 'history_en', 'history_kn'.")
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except:
        return {"history_en": "History is being indexed.", "history_kn": "ಮಾಹಿತಿ ಪ್ರಕ್ರಿಯೆಯಲ್ಲಿದೆ."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v["name"], "latitude": v["lat"], "longitude": v["lon"]} for k, v in SITES_DB.items()]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
