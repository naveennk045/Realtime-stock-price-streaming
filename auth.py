from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import json
import os
from datetime import datetime, timedelta
import uvicorn
from pydantic import BaseModel
from typing import List, Optional
import pathlib
from dotenv import load_dotenv, set_key

load_dotenv()

app = FastAPI(title="Upstox API Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

API_KEY = os.environ.get('API_KEY')
API_SECRET = os.environ.get('API_SECRET')

if not API_KEY or not API_SECRET:
    raise ValueError("API_KEY and API_SECRET environment variables must be set")

REDIRECT_URI = "http://localhost:8000/exchange-token"

TOKENS_DIR = pathlib.Path("./tokens")
TOKENS_DIR.mkdir(exist_ok=True)


ENV_FILE = pathlib.Path("./.env")
if not ENV_FILE.exists():
    with open(ENV_FILE, "w") as f:
        f.write("UPSTOX_ACCESS_TOKEN=\"\"\n")

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

def update_env_file(access_token: str):
    """Update the .env file with the new access token"""
    set_key("./.env", "UPSTOX_ACCESS_TOKEN", access_token)

@app.get("/")
async def root():
    return {"message": "Upstox API Backend is running."}

@app.get("/authorize")
async def authorize():
    auth_url = f"https://api.upstox.com/v2/login/authorization/dialog?response_type=code&client_id={API_KEY}&redirect_uri={REDIRECT_URI}"
    return {"auth_url": auth_url}

@app.get("/exchange-token")
async def exchange_token(code: str = None):
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
        access_token = result.get("access_token")
        
        if user_id and access_token:
            expiry = datetime.now() + timedelta(days=1)
            token_data = {
                "access_token": access_token,
                "expires_at": expiry.isoformat(),
                "user_name": result.get("user_name"),
                "email": result.get("email"),
                "user_id": user_id
            }
            token_store[user_id] = token_data
            save_token_to_file(user_id, token_data)
            
            # Update the .env file with the new access token
            update_env_file(access_token)
            
            # After successful token exchange, redirect to your SPA with the user_id
            frontend_url = f"http://localhost:3000/auth-success?user_id={user_id}"
            return {"status": "success", "redirect_to": frontend_url, "user_id": user_id, "access_token": access_token}
        
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/token/{user_id}")
async def get_token(user_id: str):
    token_data = token_store.get(user_id) or load_token_from_file(user_id)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    return token_data

@app.get("/user-profile/{user_id}")
async def get_user_profile(user_id: str):
    token_data = token_store.get(user_id) or load_token_from_file(user_id)
    if not token_data:
        raise HTTPException(status_code=404, detail="Token not found")
    
    access_token = token_data.get("access_token")
    headers = {
        "Accept": "application/json",
        "Authorization": f"Bearer {access_token}"
    }
    
    try:
        response = requests.get("https://api.upstox.com/v2/user/profile", headers=headers)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)