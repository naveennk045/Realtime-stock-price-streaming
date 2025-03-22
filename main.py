from fastapi import FastAPI, Request, Response, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import requests
import json
import os
from datetime import datetime, timedelta
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import pathlib

# Create template and static directories if they don't exist
templates_dir = pathlib.Path("./templates")
templates_dir.mkdir(exist_ok=True)

app = FastAPI(title="Upstox API Backend")

# Set up templates
templates = Jinja2Templates(directory="templates")

API_KEY = "c177dfe3-4000-454e-9cff-c04a05b1cee7"
API_SECRET = "rckqhjoetw"
REDIRECT_URI = "http://localhost:8000/callback"
TOKENS_DIR = pathlib.Path("./tokens")
TOKENS_DIR.mkdir(exist_ok=True)
token_store = {}

class TokenResponse(BaseModel):
    email: str
    exchanges: List[str]
    products: List[str]
    broker: str
    user_id: str
    user_name: str
    order_types: List[str]
    user_type: str
    poa: bool
    is_active: bool
    access_token: str
    extended_token: Optional[str] = None

def save_token_to_file(user_id: str, token_data: dict):
    file_path = TOKENS_DIR / f"{user_id}.json"
    with open(file_path, "w") as f:
        json.dump(token_data, f, indent=2)
    return file_path

def load_token_from_file(user_id: str):
    file_path = TOKENS_DIR / f"{user_id}.json"
    if not file_path.exists():
        return None
    with open(file_path, "r") as f:
        return json.load(f)

@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request):
    return templates.TemplateResponse("dashboard.html", {"request": request})

@app.get("/authorize")
async def authorize():
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    return {"auth_url": auth_url}

@app.get("/callback")
async def callback(request: Request, code: str = None):
    if not code:
        raise HTTPException(status_code=400, detail="Authorization Code Missing")
    
    TOKEN_URL = "https://api.upstox.com/v2/login/authorization/token"
    payload = {
        "code": code,
        "client_id": API_KEY,
        "client_secret": API_SECRET,
        "redirect_uri": REDIRECT_URI,
        "grant_type": "authorization_code"
    }
    
    headers = {"Content-Type": "application/x-www-form-urlencoded", "Accept": "application/json"}
    
    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers)
        response.raise_for_status()
        result = response.json()
        
        user_id = result.get("user_id")
        if user_id:
            expiry = datetime.now() + timedelta(days=1)
            token_data = {
                "access_token": result.get("access_token"),
                "expires_at": expiry.isoformat(),
                "user_name": result.get("user_name"),
                "email": result.get("email"),
                "user_id": user_id
            }
            token_store[user_id] = token_data
            save_token_to_file(user_id, token_data)
            return {"status": "success", "access_token": result.get("access_token"), "expires_at": expiry.isoformat()}
        
    except requests.exceptions.RequestException as e:
        return HTTPException(status_code=500, detail=str(e))

@app.get("/token/{user_id}")
async def get_token(user_id: str):
    token_data = token_store.get(user_id) or load_token_from_file(user_id)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_data

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)