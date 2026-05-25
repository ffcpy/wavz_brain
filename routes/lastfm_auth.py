from fastapi import APIRouter, Request
from urllib.parse import urlencode
import requests
import hashlib
import os
from dotenv import load_dotenv
from services.db_service import conn

load_dotenv()

router = APIRouter()
LASTFM_KEY = os.getenv("LASTFM_KEY")
LASTFM_SECRET = os.getenv("LASTFM_SECRET")
LASTFM_CALLBACK = "HTTP://127.0.0.1:8000/lastfm/callback"

def gerar_assinatura(params: dict) -> str:
    # last.fm exige uma assinatura MD5 de todos os parâmetros
    string = "".join(f"{k}{v}" for k, v in sorted(params.items()))
    string += LASTFM_SECRET
    return hashlib.md5(string.encode()).hexdigest()

@router.get("/lastfm/login")
def lastfm_login():
    params = {
        "api_key": LASTFM_KEY,
        "cb": LASTFM_CALLBACK,
    }
    auth_url = f"https://www.last.fm/api/auth?{urlencode(params)}"
    return {"login_url": auth_url}

@router.get("/lastfm/callback")
def lastfm_callback(request: Request):
    token = request.query_params.get("token")
    if not token:
        return {"error": "Nenhum token recebido"}
    
    params = {
        "method": "auth.getSession",
        "api_key": LASTFM_KEY,
        "token": token,
    }
    params["api_sig"] = gerar_assinatura(params)
    params["format"] = "json"

    response = requests.get("https://ws.audioscrobbler.com/2.0/", params=params)
    data = response.json()

    if "error" in data:
        return {"error":  data["message"]}
    
    session_key = data["session"]["key"]
    username = data["session"]["name"]

    #save ou atz db 
    cursor = conn.cursor()
    cursor.execute("SELECT spotify_id FROM users WHERE spotify_id = %s", (username,))
    existing = cursor.fetchone()

    if existing:
        cursor.execute("""
            UPDATE users SET access_token = %s, is_active = TRUE
            WHERE spotify_id = %s
        """, (session_key, username))
    else:
        cursor.execute("""
            INSERT INTO users (spotify_id, nome, access_token, refresh_token, is_active)
            VALUES (%s, %s, %s, '', TRUE)
        """, (username, username, session_key))
        conn.commit()
        cursor.close()

        return {
            "spotify_id": username,
            "nome": username,
            "session_key": session_key
        }
    
    