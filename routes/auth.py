from fastapi import Request
import os
from dotenv import load_dotenv
import requests
from fastapi import APIRouter
from urllib.parse import urlencode
from services.db_service import save_user

router = APIRouter()
load_dotenv()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
#ACESS_TOKEN = None

SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-read-recently-played",
]

@router.get("/login")

def login():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
    }

    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return {"login_url": auth_url}

@router.get("/callback")
def callback(request: Request):
    from routes import state 
    code = request.query_params.get("code")
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET

    }
    response = requests.post(token_url, data=payload)
    token_data = response.json()
    state.ACESS_TOKEN = token_data["access_token"]
    #ACESS_TOKEN = token_data["access_token"]
    headers = {
        "Authorization": f"Bearer {state.ACESS_TOKEN}"
    }
    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    user_data = user_response.json()
    save_user(
        spotify_id=user_data["id"],
        nome=user_data["display_name"],
        acess_token=state.ACESS_TOKEN
    )
    return token_data
