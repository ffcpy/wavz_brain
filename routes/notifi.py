from fastapi import APIRouter
from pydantic import BaseModel
from services.db_service import conn
from datetime import datetime

router = APIRouter()

# --- Busca notificações do usuário ---
@router.get("/notifications/{spotify_id}")
def get_notifications(spotify_id: str):
    cursor = conn.cursor()
    cursor.execute("""
        SELECT id, tipo, titulo, mensagem, lida, created_at
        FROM notifications
        WHERE spotify_id = %s
        ORDER BY created_at DESC
        LIMIT 20
    """, (spotify_id,))
    results = cursor.fetchall()
    cursor.close()

    return [{
        "id": r[0],
        "tipo": r[1],
        "titulo": r[2],
        "mensagem": r[3],
        "lida": r[4],
        "created_at": r[5].strftime("%d/%m/%Y %H:%M:%S")
    } for r in results]


# --- Marca notificação como lida ---
@router.patch("/notifications/{notification_id}/lida")
def marcar_lida(notification_id: int):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET lida = TRUE WHERE id = %s
    """, (notification_id,))
    conn.commit()
    cursor.close()
    return {"status": "ok"}


# --- Marca todas como lidas ---
@router.patch("/notifications/{spotify_id}/todas-lidas")
def marcar_todas_lidas(spotify_id: str):
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE notifications SET lida = TRUE WHERE spotify_id = %s
    """, (spotify_id,))
    conn.commit()
    cursor.close()
    return {"status": "ok"}


# --- Convite para ouvir junto ---
class ConviteRequest(BaseModel):
    de: str        # spotify_id de quem convida
    para: str      # spotify_id de quem recebe
    musica: str
    artista: str

@router.post("/notifications/convite-ouvir")
def convite_ouvir(data: ConviteRequest):
    cursor = conn.cursor()

    # Busca nome de quem está convidando
    cursor.execute("SELECT nome FROM users WHERE spotify_id = %s", (data.de,))
    user = cursor.fetchone()
    if not user:
        cursor.close()
        return {"erro": "Usuário não encontrado"}

    nome = user[0]

    cursor.execute("""
        INSERT INTO notifications (spotify_id, tipo, titulo, mensagem)
        VALUES (%s, 'amigo_convite', %s, %s)
    """, (
        data.para,
        f"{nome} te chamou pra ouvir junto",
        f"{nome} está ouvindo {data.musica} de {data.artista}. Bora?"
    ))
    conn.commit()
    cursor.close()
    return {"status": "Convite enviado"}