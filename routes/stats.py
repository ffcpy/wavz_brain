
import os
from dotenv import load_dotenv
import requests
from routes import users
from datetime import datetime
from routes import state
from fastapi import APIRouter
from services.db_service import save_stats

load_dotenv()
router = APIRouter()

def get_user_info():
    headers = {
        "Authorization": f"Bearer {state.ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    data = response.json()
    return {
        "nome": data["display_name"],
        "spotify_id": data["id"]
    }


@router.get("/wavz_status")
def wavz_status():
    user = get_user_info()
    track = musica_atual()
    save_stats(
        spotify_id=user["spotify_id"],
        music=track["musica"],
        artist=track["artista"],
        latitude= -23.5611,
        longitude= -46.6558
    )
    return {
        "usuario": user["nome"],
        "spotify_id": user["spotify_id"],
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "musica_atual": track["musica"],
        "artista": track["artista"],
        "album": track["album"]
    }

@router.get("/musica_atual")
def musica_atual():
    from routes import state
    headers = {
        "Authorization": f"Bearer {state.ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me/player/currently-playing", headers=headers)
    
    data = response.json()
    musica = data["item"]["name"] if data and "item" in data else "Nenhuma música tocando"
    artista = data["item"]["artists"][0]["name"] if data and "item" in data else "Desconecido"
    album = data["item"]["album"]["name"] if data and "item" in data else "Desconecido"


    return {"musica": musica, "artista": artista, "album": album}
