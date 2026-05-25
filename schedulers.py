from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime, timedelta
from services.db_service import conn, get_valid_access_token
import requests
import math

#aqui foi 100% AI fodase kkkk

def haversine(lat1, lng1, lat2, lng2):
    R = 6371000
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def get_territory(lat, lng):
    cursor = conn.cursor()
    cursor.execute("SELECT id, lat_centro, long_centro, raio_metros FROM territories")
    territories = cursor.fetchall()
    cursor.close()
    for t in territories:
        tid, tlat, tlng, raio = t
        if haversine(lat, lng, tlat, tlng) <= raio:
            return tid
    return None
    
def get_or_create_wave(territory_id, artista):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id FROM waves
        WHERE territory_id = %s AND artista = %s AND ativa = TRUE
    """, (territory_id, artista))
    wave = cursor.fetchone()
    if wave:
        cursor.close()
        return wave[0]
    cursor.execute("""
    SELECT COUNT(DISTINCT spotify_id) FROM stats
    WHERE artist = %s
    AND latitude IS NOT NULL
    AND timestampp >= %s
""", (artista, datetime.now() - timedelta(minutes=1))) #ARTISTA
    count = cursor.fetchone()[0]
    if count >= 2:
        cursor.execute("""
            INSERT INTO waves (territory_id, artista, total_users, score, last_activity, ativa)
            VALUES (%s, %s, 0, 0, %s, TRUE)
        """, (territory_id, artista, datetime.now()))
        conn.commit()
        wave_id = cursor.lastrowid
        cursor.close()
        notify_wave_em_alta(wave_id, territory_id, artista)  # ← adiciona aqui
        return wave_id



def upsert_wave_member(wave_id, spotify_id):
    cursor = conn.cursor()
    cursor.execute("""
    SELECT id FROM wave_members WHERE wave_id = %s AND spotify_id = %s
    """, (wave_id, spotify_id))
    member = cursor.fetchone()

    if member :
        cursor.execute("""
        UPDATE wave_members SET last_seen = %s WHERE wave_id = %s AND spotify_id = %s
        """, (datetime.now(), wave_id, spotify_id))
    else:
        cursor.execute("""
        INSERT INTO wave_members (wave_id, spotify_id, joined_at, last_seen)
            VALUES (%s, %s, %s, %s)
        """, (wave_id, spotify_id, datetime.now(), datetime.now()))

    cursor.execute("""
        UPDATE waves SET
            total_users = (
                SELECT COUNT(*) FROM wave_members
                WHERE wave_id = %s AND last_seen >= %s
            ),
            score = (
                SELECT COUNT(*) FROM wave_members
                WHERE wave_id = %s AND last_seen >= %s
            ),
            last_activity = %s
        WHERE id = %s
    """, (wave_id, datetime.now() - timedelta(minutes=1),
          wave_id, datetime.now() - timedelta(minutes=1),
          datetime.now(), wave_id))
        
    conn.commit()
    cursor.close()
                       

def kill_inactive_waves():
    cursor = conn.cursor()
    cursor.execute(""" 
                   UPDATE waves SET ativa = FALSE
                   WHERE ativa = TRUE AND last_activity < %s
                   """, (datetime.now() - timedelta(minutes=5),))
    conn.commit()
    cursor.close()


# --- Job principal: roda a cada 30s ---
def job_collect():
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Rodando coleta...")
    cursor = conn.cursor()
    cursor.execute("SELECT spotify_id FROM users WHERE is_active = TRUE")
    users = cursor.fetchall()
    cursor.close()

    for (spotify_id,) in users:
        try:
            access_token = get_valid_access_token(spotify_id)
            headers = {"Authorization": f"Bearer {access_token}"}

            response = requests.get(
                "https://api.spotify.com/v1/me/player/currently-playing",
                headers=headers
            )

            if response.status_code != 200:
                continue

            data = response.json()
            if not data or "item" not in data:
                continue

            musica = data["item"]["name"]
            artista = data["item"]["artists"][0]["name"]

            # Por enquanto latitude/longitude fixas — virão do front futuramente
            lat, lng = -23.5611, -46.6558

            # Salva em stats
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO stats (spotify_id, music, artist, latitude, longitude)
                VALUES (%s, %s, %s, %s, %s)
            """, (spotify_id, musica, artista, lat, lng))
            conn.commit()
            cursor.close()

            # Verifica território e wave
            territory_id = get_territory(lat, lng)
            if territory_id:
                wave_id = get_or_create_wave(territory_id, artista)
                if wave_id:
                    upsert_wave_member(wave_id, spotify_id)

        except Exception as e:
            print(f"Erro no usuário {spotify_id}: {e}")

    kill_inactive_waves()
    kill_users()
    print(f"[{datetime.now().strftime('%H:%M:%S')}] Coleta finalizada.")


def start_scheduler():
    scheduler = BackgroundScheduler()
    scheduler.add_job(job_collect, "interval", seconds=60)
    scheduler.start()
    print("Scheduler Iniciado")

    
        
def kill_users(): #nao matar ususarios literalmente pfvr
    cursor = conn.cursor()
    cursor.execute(""" 
        UPDATE users SET is_active = FALSE
        WHERE spotify_id NOT IN (
            SELECT DISTINCT spotify_id FROM stats
            WHERE timestampp >= %s
                )
    """, (datetime.now() - timedelta(minutes=10),))
    conn.commit()
    cursor.close()


    def get_lastfm_c_playing(username, session_key):
        params = {
            "method": "user.getrecenttracks",
            "user": username,
            "api_key": LASTFM_KEY,
            "format": "json",
            "limit": 1
        }
        response = requests.get("https://ws.audioscrobbler.com/2.0/", params=params)
        data = response.json()

        try:
            track = data["recenttracks"]["track"][0]
            # Verifica se está tocando agora
            if track.get("@attr", {}).get("nowplaying") == "true":
                return {
                    "musica": track["name"],
                    "artista": track["artist"]["#text"]
                }
        except:
            pass
        return None


def notify_wave_em_alta(wave_id, territory_id, artista):
    cursor = conn.cursor()

    # Busca usuários ativos no território que não estão na wave
    cursor.execute("""
        SELECT u.spotify_id FROM users u
        WHERE u.is_active = TRUE
        AND u.spotify_id NOT IN (
            SELECT spotify_id FROM wave_members WHERE wave_id = %s
        )
    """, (wave_id,))
    users = cursor.fetchall()

    for (spotify_id,) in users:
        # Evita notificar mais de uma vez por wave
        cursor.execute("""
            SELECT id FROM notifications
            WHERE spotify_id = %s
            AND tipo = 'wave_alta'
            AND mensagem LIKE %s
            AND created_at >= NOW() - INTERVAL 30 MINUTE
        """, (spotify_id, f"%{artista}%"))
        ja_notificado = cursor.fetchone()

        if not ja_notificado:
            cursor.execute("""
                INSERT INTO notifications (spotify_id, tipo, titulo, mensagem)
                VALUES (%s, 'wave_alta', %s, %s)
            """, (
                spotify_id,
                f"{artista} está em alta agora!",
                f"Uma wave de {artista} está rolando perto de você. Deseja entrar?"
            ))

    conn.commit()
    cursor.close()


            

