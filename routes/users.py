
import os
from dotenv import load_dotenv
import requests
from routes import state
from fastapi import APIRouter

load_dotenv()
router = APIRouter()

@router.get("/me")
def user_info(ACESS_TOKEN):

    headers = {
        "Authorization": f"Bearer {ACESS_TOKEN}"
    }
    response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if response.status_code != 200:
        return {
        "error": "spotify error",
        "status": response.status_code,
        "body": response.text
    }
    data = response.json()

    return {
        "nome": data["display_name"],
        "spotify_id": data["id"],
        "perfil": data["external_urls"]["spotify"]
    }




