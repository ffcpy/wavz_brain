import mysql.connector
from dotenv import load_dotenv
import os 

load_dotenv()

conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("MYSQL_PASSWORD"),
    database="wavz"
)
cursor = conn.cursor()


def save_user(spotify_id, nome, acess_token):
    query = "INSERT INTO users (spotify_id, nome, access_token) VALUES (%s, %s, %s)"
    values = (spotify_id, nome, acess_token)
    cursor.execute(query, values)
    conn.commit()

def save_stats(spotify_id, music, artist, latitude, longitude):
    query = "INSERT INTO stats (spotify_id, music, artist, latitude, longitude) VALUES (%s, %s, %s, %s, %s)"
    values = (
       spotify_id, music, artist, latitude, longitude
    )
    cursor.execute(query, values)
    conn.commit()


