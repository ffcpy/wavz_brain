from fastapi import APIRouter
from pydantic import BaseModel
from services.db_service import conn

router = APIRouter()

class LocationUpdate(BaseModel):
    spotify_id: str
    latitude: float
    longitude: float

@router.post("/users/location")
def update_location(data: LocationUpdate):
    cursor = conn.cursor()
    query = "UPDATE users SET latitude = %s, longitude = %s WHERE spotify_id = %s"
    values = (data.latitude, data.longitude, data.spotify_id)
    cursor.execute(query, values)
    conn.commit()
    cursor.close()
    return {"stats": "Location updated !"}