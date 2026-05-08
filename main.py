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

app = FastAPI(title="Virasat-Namma Stabilized API", version="3.5.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Heritage Metadata ────────────────────────────────────────────────────
SITES_DB = {
    "site_001": {"name": "Bangalore Palace", "lat": 12.9988, "lon": 77.5921},
    "site_002": {"name": "Vidhana Soudha", "lat": 12.9796, "lon": 77.5912},
    "site_003": {"name": "Tipu Sultan's Palace", "lat": 12.9593, "lon": 77.5738},
    "site_004": {"name": "Hampi", "lat": 15.3350, "lon": 76.4600},
    "site_005": {"name": "Belur Chennakesava", "lat": 13.1625, "lon": 75.8596},
    "site_006": {"name": "Mysore Palace", "lat": 12.3052, "lon": 76.6552},
    "site_007": {"name": "Halebidu", "lat": 13.2119, "lon": 75.9926},
    "site_008": {"name": "Pattadakal", "lat": 15.9485, "lon": 75.8166},
    "site_009": {"name": "Gol Gumbaz", "lat": 16.8301, "lon": 75.7360},
    "site_010": {"name": "Shravanabelagola", "lat": 12.8550, "lon": 76.4850},
}

class ChatRequest(BaseModel):
    message: str

@app.get("/")
async def health():
    return {"status": "healthy", "service": "Virasat Historian Stabilized"}

@app.post("/api/chat")
async def agent_chat(request: ChatRequest):
    """
    Virasat Historian: Recovery Update.
    Resolved repetitive greeting loops and generic 'archives' refusals.
    """
    model = get_ai_client()
    if not model: return {"response": "The archives are currently under preservation."}
    
    system_instruction = (
        "You are the 'Virasat Historian', a master of Karnataka's history. "
        "Respond to greetings and questions immediately using the provided heritage context. "
        "Do not use fallbacks unless the API is physically disconnected. "
        "Provide specific, deep heritage facts based on user queries. "
        "Be concise, respectful, and scholarly. "
        "If the user asks about locations, mention relevant sites like Bangalore Palace, Hampi, Mysore Palace, or Belur."
    )
    try:
        res = model.generate_content(f"{system_instruction}\nUser: {request.message}")
        return {"response": res.text.strip()}
    except Exception as e:
        print(f"Gemini Error: {e}")
        return {"response": "I am currently meditating on a rare inscription. Please ask again in a moment."}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v["name"], "latitude": v["lat"], "longitude": v["lon"]} for k, v in SITES_DB.items()]}

if __name__ == "__main__":
    import uvicorn
    # PRODUCTION FIX: Explicit port binding for Render
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
