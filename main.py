
from contextlib import asynccontextmanager
from fastapi import FastAPI
from schedulers import start_scheduler
from routes import auth, stats, users_loc, waves, social, lastfm_auth, notifi #  routers 
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware


@asynccontextmanager
async def lifespan(app):
    start_scheduler()
    yield


app = FastAPI(lifespan=lifespan)
@app.get("/app")
def serve_app():
    return FileResponse("wavz2.html")


app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(users_loc.router)
app.include_router(waves.router)
app.include_router(social.router)
app.include_router(lastfm_auth.router)
app.include_router(notifi.router)


from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


#ignorar 
"""from fastapi import FastAPI
import requests
from fastapi import Request
from routes.auth import router as auth_router
from routes.stats import router as stats_router
from scheduler import start_scheduler



app = FastAPI()
app.include_router(auth_router)
app.include_router(stats_router)

@app.route("startup")
def startup():
    start_scheduler()

    """