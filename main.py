from fastapi import FastAPI, Request, Response, HTTPException
import requests
import json
import os
from datetime import datetime, timedelta
import uvicorn
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Upstox API Integration")

# Replace with your actual Upstox API Key and API Secret
API_KEY = "6ccc357d-b48a-45fa-9b88-0fc099f6abfe"
API_SECRET = "bivi79bnui"
REDIRECT_URI = "http://localhost:8000/callback"

# Session storage (replace with database in production)
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

@app.get("/")
async def root():
    """Displays a simple page with link to start OAuth flow"""
    auth_url = f"https://api.upstox.com/v2/login/authorization?client_id={API_KEY}&redirect_uri={REDIRECT_URI}&response_type=code"
    html_content = f"""
    <html>
        <head>
            <title>Upstox API Integration</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .container {{ max-width: 800px; margin: 0 auto; }}
                .btn {{ display: inline-block; background: #0066cc; color: white; padding: 10px 20px; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>Upstox API Integration</h1>
                <p>Click the button below to authorize with Upstox:</p>
                <a href="{auth_url}" class="btn">Login with Upstox</a>
            </div>
        </body>
    </html>
    """
    return Response(content=html_content, media_type="text/html")

@app.get("/callback")
async def callback(request: Request, code: str = None):
    """Handle OAuth callback from Upstox"""
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
    
    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json"
    }
    
    try:
        response = requests.post(TOKEN_URL, data=payload, headers=headers) # Raise exception for non-200 responses
        
        result = response.json()
        
        # Store token for later use (in a real app, store in database)
        user_id = result.get("user_id")
        if user_id:
            # Calculate token expiry - 3:30 AM next day
            now = datetime.now()
            if now.hour < 3 or (now.hour == 3 and now.minute < 30):
                # Expires today at 3:30 AM
                expiry = now.replace(hour=3, minute=30, second=0, microsecond=0)
            else:
                # Expires tomorrow at 3:30 AM
                tomorrow = now + timedelta(days=1)
                expiry = tomorrow.replace(hour=3, minute=30, second=0, microsecond=0)
                
            token_store[user_id] = {
                "access_token": result.get("access_token"),
                "extended_token": result.get("extended_token"),
                "expires_at": expiry.isoformat()
            }
        
        # Return success response with HTML for better UX
        html_response = f"""
        <html>
            <head>
                <title>Authentication Successful</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    .container {{ max-width: 800px; margin: 0 auto; }}
                    .success {{ color: green; }}
                    .data {{ background: #f5f5f5; padding: 15px; border-radius: 5px; }}
                    .token {{ word-break: break-all; font-family: monospace; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <h1 class="success">Authentication Successful</h1>
                    <p>You have successfully authenticated with Upstox!</p>
                    <div class="data">
                        <p><strong>User ID:</strong> {result.get("user_id")}</p>
                        <p><strong>User Name:</strong> {result.get("user_name")}</p>
                        <p><strong>Email:</strong> {result.get("email")}</p>
                        <p><strong>Exchanges:</strong> {", ".join(result.get("exchanges", []))}</p>
                        <p><strong>Products:</strong> {", ".join(result.get("products", []))}</p>
                        <p><strong>Token Expires:</strong> 3:30 AM {expiry.strftime("%Y-%m-%d")}</p>
                        <p><strong>Access Token:</strong> <span class="token">{result.get("access_token")}</span></p>
                    </div>
                </div>
            </body>
        </html>
        """
        return Response(content=html_response, media_type="text/html")
        
    except requests.exceptions.RequestException as e:
        error_detail = "Unknown error"
        if hasattr(e, 'response') and e.response is not None:
            try:
                error_detail = e.response.json()
            except:
                error_detail = e.response.text
                
        raise HTTPException(status_code=500, detail=f"Failed to get access token: {error_detail}")

@app.get("/token/{user_id}")
async def get_token(user_id: str):
    """Get stored token for a user"""
    if user_id not in token_store:
        raise HTTPException(status_code=404, detail="Token not found for this user")
        
    token_data = token_store[user_id]
    expiry = datetime.fromisoformat(token_data["expires_at"])
    
    if datetime.now() > expiry:
        # Token expired
        token_store.pop(user_id)
        raise HTTPException(status_code=401, detail="Token expired")
        
    return {
        "access_token": token_data["access_token"],
        "extended_token": token_data.get("extended_token"),
        "expires_at": token_data["expires_at"]
    }

@app.get("/market-data-test")
async def test_market_data(token: str):
    """Test endpoint to verify market data access with a given token"""
    headers = {"Authorization": f"Bearer {token}"}
    response = requests.get("https://api.upstox.com/v3/feed/market-data-feed/authorize", headers=headers)
    
    if response.status_code == 200:
        return {
            "status": "success",
            "message": "Market data access verified",
            "websocket_url": response.json().get("authorized_redirect_uri")
        }
    else:
        return {
            "status": "error",
            "message": "Market data access failed",
            "details": response.json()
        }

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)