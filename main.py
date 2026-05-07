from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import google.generativeai as genai

# ─── Gemini AI Configuration ────────────────────────────────────────────────
gemini_key = os.getenv("GEMINI_API_KEY")
if gemini_key:
    genai.configure(api_key=gemini_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    model = None

app = FastAPI(title="Virasat-Namma Excellence API", version="1.5.0")

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

@app.get("/api/heritage/{site_id}")
async def get_site_history(site_id: str):
    """
    Uses Gemini to generate bilingual historical narratives for the AI Storyteller.
    """
    if not model: raise HTTPException(status_code=503, detail="AI Storyteller Offline")
    
    site_name = SITES_METADATA.get(site_id, "this heritage site")
    prompt = (
        f"Generate a historical summary for {site_name}. "
        "Return exactly a JSON object with: "
        "'history_en' (3 sentences in English) and "
        "'history_kn' (3 sentences in Kannada). "
        "Strictly scholarly tone. Ensure the output is valid JSON."
    )
    
    try:
        response = model.generate_content(prompt)
        # Simple extraction logic for JSON if Gemini adds markdown
        text = response.text.strip()
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0].strip()
        
        import json
        history_data = json.loads(text)
        
        return {
            "site_id": site_id,
            "site_name": site_name,
            "history_en": history_data.get("history_en", ""),
            "history_kn": history_data.get("history_kn", "")
        }
    except Exception as e:
        return {
            "site_id": site_id,
            "site_name": site_name,
            "history_en": f"Historical data for {site_name} is being indexed.",
            "history_kn": f"{site_name} ಬಗ್ಗೆ ಮಾಹಿತಿ ಶೀಘ್ರದಲ್ಲೇ ಲಭ್ಯವಿರುತ್ತದೆ."
        }

@app.post("/api/chat")
async def agent_chat(request: dict):
    if not model: return {"response": "Brain offline."}
    msg = request.get("message", "")
    context = (
        "You are the Virasat Agent. If a user wants to go somewhere, append '[NAVIGATE:ID]'. "
        "IDs: site_001 (Palace), site_002 (Soudha), site_003 (Tipu), HAMPI (Hampi)."
    )
    res = model.generate_content(f"{context}\nUser: {msg}")
    return {"response": res.text.strip()}

@app.get("/api/heritage")
async def list_sites():
    return {"sites": [{"id": k, "name": v} for k, v in SITES_METADATA.items()]}
