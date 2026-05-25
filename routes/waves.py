from fastapi import APIRouter
from services.db_service import conn

router = APIRouter()

@router.get("/waves/ativas")
def get_waves_ativa():
    cursor = conn.cursor()
    cursor.execute("""
        SELECT w.id, 
            w.artista,
            w.total_users,
            w.score,
            w.started_at,
            w.last_activity,
                   t.nome AS territorio
        FROM waves w
        JOIN territories t ON w.territory_id = t.id
        WHERE w.ativa = TRUE
        ORDER BY w.last_activity DESC
    """)
    results = cursor.fetchall()
    cursor.close()

    waves = []
    for row in results:
        waves.append({
            "id": row[0],
            "artista": row[1],
            "total_users": row[2],
            "score": row[3],
            "started_at": row[4].strftime("%d/%m/%Y %H:%M:%S"),
            "last_activity": row[5].strftime("%d/%m/%Y %H:%M:%S"),
            "territorio": row[6]
        })
        return waves
    
