from fastapi import FastAPI, HTTPException, Request
from motor.motor_asyncio import AsyncIOMotorClient
from db import uri
from models import Poll,Voters,Votes
from bson import ObjectId
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import slugify


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

MONGO_URI = uri
client = AsyncIOMotorClient(MONGO_URI)
db = client["Polling"]
users = db["voters"]
polls = db['polls']

@app.get('/ping')
async def hello():
    return {'res': 'pong', 'version': __version__, "time": time()}
