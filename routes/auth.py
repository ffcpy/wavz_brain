from fastapi import Request
import os
from dotenv import load_dotenv
import requests
from fastapi import APIRouter
from urllib.parse import urlencode
from services.db_service import save_user, conn
from services.config import *
import secrets


router = APIRouter()
load_dotenv()

"""CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID")
CLIENT_SECRET = os.getenv("SPOTIFY_SECRET")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI")
"""
#ACESS_TOKEN = None

SCOPES = [
    "user-read-currently-playing",
    "user-read-playback-state",
    "user-read-recently-played",
]

@router.get("/login")

def login(redirect: str = None):
    state = secrets.token_urlsafe(16)
    
    # usa o redirect do app mobile se vier, senão usa o padrão
    redirect_uri = redirect if redirect else REDIRECT_URI
    
    params = {
        "client_id": CLIENT_ID,
        "response_type": "code",
        "redirect_uri": redirect_uri,
        "scope": " ".join(SCOPES),
        "state": state,
        "show_dialog": "true",
    }

    auth_url = f"https://accounts.spotify.com/authorize?{urlencode(params)}"
    return {"login_url": auth_url}

@router.get("/callback")
def callback(request: Request):
   

   #vou tentar colar esse bloco em cada funcao separadamente - esquece, resolvido amem
    code = request.query_params.get("code")
    error = request.query_params.get("error")
    if error:
        return{"erro": "Nenhum codigo recebido"}
    if not code:
        return {"erro": "Nenhum código recebido"}
    token_url = "https://accounts.spotify.com/api/token"
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": REDIRECT_URI,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET

    }



    response = requests.post(token_url, data=payload)
    if response.status_code != 200:
        return {"erro": "Falha no exchange do token", "status": response.status_code, "body": response.text}


    token_data = response.json()
    if "error" in token_data:
        return {"erro": token_data["error"], "descricao": token_data.get("error_description")}
    access_token = token_data["access_token"]
    refresh_token = token_data["refresh_token"]
    if not access_token:
        return { "erro": "access_token ausente na response", "resposta_completa": token_data}
    
    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    user_response = requests.get("https://api.spotify.com/v1/me", headers=headers)
    if user_response.status_code != 200:
        return {"erro": "Falha ao buscar user no spotify", "status": user_response.status_code, "body": user_response.text}
    
    user_data = user_response.json()
    spotify_id = user_data["id"]
    nome = user_data["display_name"]

    # Verifica se já existe e atualiza ou insere novo
    db_cursor = conn.cursor()
    db_cursor.execute("SELECT spotify_id FROM users WHERE spotify_id = %s", (spotify_id,))
    existing = db_cursor.fetchone()

    if existing:
        db_cursor.execute(
            "UPDATE users SET access_token = %s, refresh_token = %s,is_active = TRUE WHERE spotify_id = %s",
            (access_token, refresh_token, spotify_id)
        )
        conn.commit()
    else:
        save_user(spotify_id=spotify_id, nome=nome, access_token=access_token, refresh_token=refresh_token)

    db_cursor.close()
    
    #teste

    return {
        #SE UM DIA FRONT PRECISAR EU CHAMO SPOTIFY ID AQUI
        "spotify_id": spotify_id,
        "access_token": access_token,
        "user": nome
        }
    
        #return {"message": "Usuário já existe"}