from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import math
import json
import google.generativeai as genai

# ─── Gemini AI Configuration ────────────────────────────────────────────────
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

app = FastAPI(title="Virasat-Namma Excellence API", version="1.6.0")

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

class RouteRequest(BaseModel):
    origin_lat: float
    origin_lon: float
    dest_lat: float
    dest_lon: float

@app.post("/api/route/distance")
async def get_road_distance(request: RouteRequest):
    """
    Estimates road distance using a multiplier (1.4x) on the Haversine distance.
    In production, this would call OSRM or Google Distance Matrix.
    """
    def haversine(lat1, lon1, lat2, lon2):
        R = 6371.0
        dlat = math.radians(lat2 - lat1)
        dlon = math.radians(lon2 - lon1)
        a = math.sin(dlat / 2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    straight_line = haversine(request.origin_lat, request.origin_lon, request.dest_lat, request.dest_lon)
    # Applying road coefficient multiplier (1.4x)
    return {"road_distance": straight_line * 1.4}

@app.get("/api/heritage/hidden")
async def get_hidden_heritage(lat: float, lon: float, radius: float = 30.0):
    """
    Uses Gemini to discover 'Hidden Heritage' sites near the user.
    """
    if not model: return {"sites": []}
    
    prompt = (
        f"Find 3 hidden or lesser-known heritage sites within {radius}km of latitude {lat}, longitude {lon} (Bangalore area). "
        "Return exactly a JSON list of objects with: "
        "'id', 'name', 'description', 'latitude', 'longitude', 'hint' (where to find QR), 'image_hint'."
        "Ensure valid JSON output."
    )
    
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        
        sites = json.loads(text)
        return {"sites": sites}
    except Exception as e:
        return {"sites": []}

@app.get("/api/heritage/{site_id}")
async def get_site_history(site_id: str):
    if not model: raise HTTPException(status_code=503, detail="AI Storyteller Offline")
    site_name = SITES_METADATA.get(site_id, "this heritage site")
    prompt = (
        f"Generate a historical summary for {site_name}. "
        "Return exactly a JSON object with: 'history_en' and 'history_kn'. "
        "Strictly scholarly tone."
    )
    try:
        response = model.generate_content(prompt)
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        history_data = json.loads(text)
        return {
            "site_id": site_id,
            "site_name": site_name,
            "history_en": history_data.get("history_en", ""),
            "history_kn": history_data.get("history_kn", "")
        }
    except Exception as e:
        return {"history_en": "Data indexed.", "history_kn": "ಮಾಹಿತಿ ಲಭ್ಯವಿದೆ."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v} for k, v in SITES_METADATA.items()]}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
