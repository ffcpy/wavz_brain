from fastapi import APIRouter
from services.db_service import conn

router = APIRouter()

# --- Perfil completo 
@router.get("/users/{spotify_id}/profile")
def get_profile(spotify_id: str):
    cursor = conn.cursor()
    
    # Dados do usuário
    cursor.execute("""
        SELECT nome, foto_url, cidade, is_active
        FROM users WHERE spotify_id = %s
    """, (spotify_id,))
    user = cursor.fetchone()
    if not user:
        return {"erro": "Usuário não encontrado"}

    # Total de lugares visitados
    cursor.execute("""
        SELECT COUNT(DISTINCT territory_id) FROM stats s
        JOIN waves w ON w.id = s.wave_id
        WHERE s.spotify_id = %s
    """, (spotify_id,))
    lugares = cursor.fetchone()[0]

    # Total ouvindo (plays totais)
    cursor.execute("""
        SELECT COUNT(*) FROM stats WHERE spotify_id = %s
    """, (spotify_id,))
    total_plays = cursor.fetchone()[0]

    # Amigos
    cursor.execute("""
        SELECT COUNT(*) FROM friends
        WHERE (spotify_id = %s OR friend_id = %s) AND status = 'aceito'
    """, (spotify_id, spotify_id))
    total_amigos = cursor.fetchone()[0]

    # Lugares favoritos (top 3 territórios mais frequentados)
    cursor.execute("""
        SELECT t.nome, COUNT(*) as visitas
        FROM stats s
        JOIN waves w ON w.id = s.wave_id
        JOIN territories t ON t.id = w.territory_id
        WHERE s.spotify_id = %s
        GROUP BY t.nome
        ORDER BY visitas DESC
        LIMIT 3
    """, (spotify_id,))
    lugares_favoritos = [{"territorio": r[0], "visitas": r[1]} for r in cursor.fetchall()]

    # Artistas em alta pro usuário (top 3 mais ouvidos)
    cursor.execute("""
        SELECT artista, COUNT(*) as plays
        FROM stats WHERE spotify_id = %s
        GROUP BY artista
        ORDER BY plays DESC
        LIMIT 3
    """, (spotify_id,))
    artistas = [{"artista": r[0], "plays": r[1]} for r in cursor.fetchall()]

    cursor.close()
    return {
        "nome": user[0],
        "foto_url": user[1],
        "cidade": user[2],
        "is_active": user[3],
        "total_amigos": total_amigos,
        "total_plays": total_plays,
        "total_lugares": lugares,
        "lugares_favoritos": lugares_favoritos,
        "artistas_em_alta": artistas
    }


# --- Feed global 
@router.get("/feed")
def get_feed():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT 
            s.spotify_id,
            u.nome,
            u.foto_url,
            s.musica,
            s.artista,
            t.nome AS territorio,
            s.timestamp
        FROM stats s
        JOIN users u ON u.spotify_id = s.spotify_id
        LEFT JOIN waves w ON w.id = s.wave_id
        LEFT JOIN territories t ON t.id = w.territory_id
        WHERE s.timestamp >= NOW() - INTERVAL 5 MINUTE
        GROUP BY s.spotify_id
        ORDER BY s.timestamp DESC
        LIMIT 20
    """)
    results = cursor.fetchall()
    cursor.close()

    return [{
        "spotify_id": r[0],
        "nome": r[1],
        "foto_url": r[2],
        "musica": r[3],
        "artista": r[4],
        "territorio": r[5],
        "timestamp": r[6].strftime("%d/%m/%Y %H:%M:%S")
    } for r in results]


# --- Em alta perto de você
@router.get("/em-alta")
def em_alta(spotify_id: str):
    cursor = conn.cursor()

    # Pega localização 
    cursor.execute("""
        SELECT latitude, longitude FROM users WHERE spotify_id = %s
    """, (spotify_id,))
    user_loc = cursor.fetchone()
    if not user_loc or not user_loc[0]:
        return {"erro": "Localização do usuário não disponível"}

    # Artistas mais ouvidos nas waves do territorio nos ultimos 30 minutos
    cursor.execute("""
        SELECT w.artista, SUM(w.score) as total_score, t.nome as territorio
        FROM waves w
        JOIN territories t ON t.id = w.territory_id
        WHERE w.ativa = TRUE
        AND w.last_activity >= NOW() - INTERVAL 30 MINUTE
        GROUP BY w.artista, t.nome
        ORDER BY total_score DESC
        LIMIT 5
    """)
    results = cursor.fetchall()
    cursor.close()

    return [{
        "artista": r[0],
        "ouvindo": int(r[1]),
        "territorio": r[2]
    } for r in results]


# --- Ao vivo agora 
@router.get("/ao-vivo")
def ao_vivo():
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM users WHERE is_active = TRUE")
    total = cursor.fetchone()[0]
    cursor.close()
    return {"ao_vivo_agora": total}


# --- Adicionar amigo 
from pydantic import BaseModel

class FriendRequest(BaseModel):
    spotify_id: str
    friend_id: str

@router.post("/friends/add")
def add_friend(data: FriendRequest):
    cursor = conn.cursor()

    # Verifica se já existe
    cursor.execute("""
        SELECT id FROM friends
        WHERE (spotify_id = %s AND friend_id = %s)
        OR (spotify_id = %s AND friend_id = %s)
    """, (data.spotify_id, data.friend_id, data.friend_id, data.spotify_id))
    existing = cursor.fetchone()

    if existing:
        cursor.close()
        return {"erro": "Solicitação já existe"}

    cursor.execute("""
        INSERT INTO friends (spotify_id, friend_id, status)
        VALUES (%s, %s, 'pendente')
    """, (data.spotify_id, data.friend_id))
    conn.commit()
    cursor.close()
    return {"status": "Solicitação enviada"}


# --- Sugestões de amigos 
@router.get("/friends/sugestoes")
def sugestoes_amigos(spotify_id: str):
    cursor = conn.cursor()

    # Usuários que ouvem artistas em comum mas ainda não são amigos
    cursor.execute("""
        SELECT DISTINCT u.spotify_id, u.nome, u.foto_url, COUNT(*) as artistas_em_comum
        FROM stats s1
        JOIN stats s2 ON s1.artista = s2.artista
        JOIN users u ON u.spotify_id = s2.spotify_id
        WHERE s1.spotify_id = %s
        AND s2.spotify_id != %s
        AND s2.spotify_id NOT IN (
            SELECT friend_id FROM friends WHERE spotify_id = %s AND status = 'aceito'
            UNION
            SELECT spotify_id FROM friends WHERE friend_id = %s AND status = 'aceito'
        )
        GROUP BY u.spotify_id, u.nome, u.foto_url
        ORDER BY artistas_em_comum DESC
        LIMIT 5
    """, (spotify_id, spotify_id, spotify_id, spotify_id))
    results = cursor.fetchall()
    cursor.close()

    return [{
        "spotify_id": r[0],
        "nome": r[1],
        "foto_url": r[2],
        "artistas_em_comum": r[3]
    } for r in results]