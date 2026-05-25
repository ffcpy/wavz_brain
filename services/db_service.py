import mysql.connector
from dotenv import load_dotenv
import os 
from .config import *
import requests

load_dotenv()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="wavz"
)
cursor = conn.cursor()

def refresh_access_token(refresh_token):

    token_url = "https://accounts.spotify.com/api/token"

    payload = {
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET
    }

    response = requests.post(token_url, data=payload)

    return response.json()

def save_user(spotify_id, nome, access_token, refresh_token):
    cursor = conn.cursor()
    query = "INSERT INTO users (spotify_id, nome, access_token, refresh_token, is_active) VALUES (%s, %s, %s, %s, TRUE)"
    values = (spotify_id, nome, access_token, refresh_token)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()

def save_stats(spotify_id, music, artist, latitude, longitude):
    cursor = conn.cursor()
    query = "INSERT INTO stats (spotify_id, music, artist, latitude, longitude) VALUES (%s, %s, %s, %s, %s)"
    values = (
       spotify_id, music, artist, latitude, longitude
    )
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    

def get_nearby_users(latitude, longitude, spotify_id):
    cursor = conn.cursor()
    query = """
    SELECT s.spotify_id, s.music, s.artist, s.timestampp
    FROM stats s
    INNER JOIN (
        SELECT spotify_id, MAX(timestampp) as ultimo
        FROM stats
        WHERE latitude = %s AND longitude = %s AND spotify_id != %s
        GROUP BY spotify_id
    ) recente ON s.spotify_id = recente.spotify_id AND s.timestampp = recente.ultimo
    ORDER BY s.timestampp DESC
    LIMIT 20
    """
    """query = "
    SELECT 
        spotify_id,
        music,
        artist,
        latitude,
        longitude,
        timestampp
    FROM stats
    WHERE
        latitude = %s
        AND longitude = %s
        AND spotify_id != %s
    ORDER BY timestampp 
    LIMIT 20 
    """
    
    cursor.execute(query, (latitude, longitude, spotify_id))
    results = cursor.fetchall()
    cursor.close()
    return results


def get_valid_access_token(spotify_id: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT access_token, refresh_token
        FROM users
        WHERE spotify_id = %s
    """, (spotify_id,))

    result = cursor.fetchone()
    cursor.close()
    if not result:
        raise ValueError(f"Usuário {spotify_id} não encontrado no banco")

    access_token = result[0]
    refresh_token = result[1]

    headers = {
        "Authorization": f"Bearer {access_token}"
    }

    response = requests.get(
        "https://api.spotify.com/v1/me",
        headers=headers
    )

    # se expirou, renova
    if response.status_code == 401:
        cursor = conn.cursor()
        new_token = refresh_access_token(refresh_token)
        access_token = new_token["access_token"]

        cursor.execute("""
            UPDATE users
            SET access_token = %s
            WHERE spotify_id = %s
        """, (access_token, spotify_id))

        conn.commit()
        cursor.close()
        

    return access_token

