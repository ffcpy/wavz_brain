
import os
from dotenv import load_dotenv
import requests
from routes import users
from datetime import datetime
from routes import state
from fastapi import APIRouter
from services.db_service import save_stats, get_nearby_users, conn, refresh_access_token, get_valid_access_token
#from routes.auth import callback
from services.config import *

load_dotenv()
router = APIRouter()

def get_user_info(spotify_id):
    acess_token = get_valid_access_token(spotify_id)
    headers = {
        "Authorization": f"Bearer {acess_token}"
    }
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    data = response.json()
    return {
        "nome": data["display_name"],
        "spotify_id": data["id"]
    }


@router.get("/wavz_status")
def wavz_status(spotify_id: str):

    user = get_user_info(spotify_id)
    track = musica_atual_data(spotify_id) # FUNCAO E NAO A ROTAAA CARALHO

    if "erro" not in track and track["musica"] != "Nenhuma música tocando":
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



def musica_atual_data(spotify_id: str):

    access_token = get_valid_access_token(spotify_id)
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://api.spotify.com/v1/me/player/currently-playing",
        headers=headers
    )

    if response.status_code == 204:
        return {
            "musica": "Nenhuma música tocando"
        }
    if response.status_code != 200:
        return {"erro": f"Erro da Bosta da API do Spotify ((eles precisam contratar o Lukao do SENAI): {response.status_code}"}
    


    data = response.json()

    return {
        "musica": data["item"]["name"],
        "artista": data["item"]["artists"][0]["name"],
        "album": data["item"]["album"]["name"]
    }

@router.get("/musica_atual")
def musica_atual(spotify_id: str):
    return musica_atual_data(spotify_id)


@router.get("/nearby_users")
def nearby_users(spotify_id: str):
    latitude= -23.5611 #localizacao fix AQUIIIII!!!
    longitude= -46.6558 #LOCALIZACAO AUI !!!

    
    nearby = get_nearby_users(float(latitude), float(longitude), spotify_id)
    
    return [
        {
            "spotify_id": item[0],
            "name": item[1],
            "artist": item[2],
            "created_at": item[3].strftime("%d/%m/%Y %H:%M:%S")
        }
        for item in nearby
    ]

    #eturn nearby