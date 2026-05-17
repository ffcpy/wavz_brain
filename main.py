
from fastapi import FastAPI
import requests
from fastapi import Request
from routes.auth import router as auth_router
from routes.stats import router as stats_router



app = FastAPI()
app.include_router(auth_router)
app.include_router(stats_router)