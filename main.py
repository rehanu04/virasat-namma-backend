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

app = FastAPI(title="Virasat-Namma Excellence API", version="1.7.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Heritage Metadata ──────────────────────────────────────────────────────
SITES_METADATA = {
    "site_001": "Bangalore Palace",
    "site_002": "Vidhana Soudha",
    "site_003": "Tipu Sultan's Summer Palace",
    "hampi": "Hampi Group of Monuments"
}

class ChatRequest(BaseModel):
    message: str

@app.post("/api/chat")
async def agent_chat(request: ChatRequest):
    model = get_ai_client()
    if not model: return {"response": "Brain offline."}
    
    context = (
        "You are the Virasat Historian. Provide concise info about Bangalore heritage. "
        "If the user wants to visit a place, append '[NAVIGATE:ID]'. "
        "IDs: site_001 (Palace), site_002 (Soudha), site_003 (Tipu), HAMPI (Hampi)."
    )
    try:
        res = model.generate_content(f"{context}\nUser: {request.message}")
        return {"response": res.text.strip()}
    except:
        return {"response": "I cannot access the historical records right now."}

@app.get("/api/heritage/scan")
async def scan_heritage(site_id: str):
    """
    Generates a 'Hidden Fact' reward when a user scans a monument QR.
    """
    model = get_ai_client()
    site_name = SITES_METADATA.get(site_id, "this monument")
    
    if not model:
        return {"hidden_fact": f"{site_name} is a cornerstone of Namma Bengaluru's history."}
        
    prompt = f"Provide one surprising, non-obvious historical fact about {site_name}. One sentence only."
    try:
        res = model.generate_content(prompt)
        return {"hidden_fact": res.text.strip()}
    except:
        return {"hidden_fact": f"Legend says {site_name} holds secrets yet to be uncovered."}

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float

@app.post("/api/route/distance")
async def get_road_distance(request: RouteRequest):
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c
    straight_line = haversine(request.origin_lat, request.origin_lon, request.dest_lat, request.dest_lon)
    return {"road_distance": straight_line * 1.4}

@app.get("/api/heritage/hidden")
async def get_hidden_heritage(lat: float, lon: float, radius: float = 30.0):
    model = get_ai_client()
    if not model: return {"sites": []}
    prompt = (
        f"Find 3 hidden heritage sites within {radius}km of {lat}, {lon}. "
        "Return exactly JSON: 'id', 'name', 'description', 'latitude', 'longitude', 'hint', 'image_hint'."
    )
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        return {"sites": json.loads(text)}
    except: return {"sites": []}

@app.get("/api/heritage/{site_id}")
async def get_site_history(site_id: str):
    model = get_ai_client()
    if not model: raise HTTPException(status_code=503, detail="AI Offline")
    site_name = SITES_METADATA.get(site_id, "this site")
    try:
        response = model.generate_content(f"History of {site_name}. Return JSON: 'history_en', 'history_kn'.")
        text = response.text.strip()
        if "```json" in text: text = text.split("```json")[1].split("```")[0].strip()
        return json.loads(text)
    except: return {"history_en": "Data indexed.", "history_kn": "ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v} for k, v in SITES_METADATA.items()]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
