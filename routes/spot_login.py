from fastapi import FastAPI
import requests
from fastapi import Request
import os 
from dotenv import load_dotenv
from urllib.parse import urlencode
from datetime import datetime


load_dotenv()

app = FastAPI()

CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
ACESS_TOKEN = None



SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-read-recently-played",
]

@app.get("/login")

def login():
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": REDIRECT_URI,
        "scope": " ".join(SCOPES),
    }

    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return {"login_url": auth_url}

@app.get("/callback")
def callback(request: Request):
    global ACESS_TOKEN
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
    ACESS_TOKEN = token_data["access_token"]

    return token_data

def get_user_info():
    headers = {
        "Authorization": f"Bearer {ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    data = response.json()
    return {
        "nome": data["display_name"],
        "spotify_id": data["id"]
    }

@app.get("/musica_atual")
def musica_atual():
    headers = {
        "Authorization": f"Bearer {ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    
    data = response.json()
    musica = data["item"]["name"] if data and "item" in data else "Nenhuma música tocando"
    artista = data["item"]["artists"][0]["name"] if data and "item" in data else "Desconecido"
    album = data["item"]["album"]["name"] if data and "item" in data else "Desconecido"


    return {"musica": musica, "artista": artista, "album": album}

@app.get("/me")
def user_info():
    headers = {
        "Authorization": f"Bearer {ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    data = response.json()

    return {
        "nome": data["display_name"],
        "spotify_id": data["id"],
        "perfil": data["external_urls"]["spotify"]
    }

@app.get("/wavz_status")
def wavz_status():

    user = get_user_info()
    track = musica_atual()
    return {
        "usuario": user["nome"],
        "spotify_id": user["spotify_id"],
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "musica_atual": track["musica"],
        "artista": track["artista"],
        "album": track["album"]
    }
