from fastapi import FastAPI, HTTPException, Request, WebSocket, Depends, status, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from db import uri
from models import Poll,Voters,Votes
from bson import ObjectId
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import slugify
import asyncio
from typing import List
from pydantic import BaseModel


app = FastAPI()

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

MONGO_URI = uri
client = AsyncIOMotorClient(MONGO_URI)
db = client["Polling"]
users = db["voters"]
polls = db['polls']
votes = db["votes"]

client.get_io_loop = asyncio.get_event_loop

@app.get("/", response_class=HTMLResponse)
async def get_homepage(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})


@app.post("/polls/",status_code=201)
async def create_poll(poll: Poll):
    try:
        poll_data = poll.dict()

        slug = slugify.slugify(poll_data['title'])

        existing_poll = await polls.find_one({'slug': slug})
        counter = 1
        new_slug = None
        while existing_poll:
            new_slug = f"{slug}-{counter}"
            existing_poll = await polls.find_one({'slug': new_slug})
            counter += 1
        if new_slug:
            slug = new_slug
        poll_data['slug'] = slug
        print(poll_data)
        result = await polls.insert_one(poll_data)
        print(result)
        return {"message": "Poll created", "poll_slug": (poll_data['slug'])}
    except Exception as e:
        print(e.args)
        raise HTTPException(status_code=500, detail="Failed to create the poll")

@app.get("/polls/{poll_slug}")
async def get_poll(poll_slug: str,request:Request):
    try:
        poll_data = await polls.find_one({'slug': poll_slug})
        if poll_data:
            poll_data['_id'] = str(poll_data['_id'])
        return templates.TemplateResponse("poll_view.html", {"request":request,"poll": poll_data})
    except Exception as e:
        print(e.args)
        raise HTTPException(status_code=500, detail="Failed to fetch poll")

# click_count = 0

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_to_all(self, message):
        for connection in self.active_connections:
            await connection.send_text(message)

# manager = ConnectionManager()

# @app.websocket("/ws/")
# async def websocket_endpoint(websocket: WebSocket):
#     await manager.connect(websocket)
#     try:
#         while True:
#             data = await websocket.receive_text()
#             if data == "click":
#                 global click_count
#                 db["click_count"] += 1
#                 await manager.send_to_all(str(db["click_count"]))
#     except Exception as e:
#         print(f"Error: {e}")
#     finally:
#         manager.disconnect(websocket)

@app.get("/test-ws",response_class=HTMLResponse)
async def test_websocket(request: Request):
    return templates.TemplateResponse("websocket.html", {"request": request})


class ClickUpdate(BaseModel):
    count: int

manager = ConnectionManager()
@app.websocket("/wss/")
async def websocket_endpoint(websocket: WebSocket):
    # await websocket.accept() 
    await manager.connect(websocket)
    # Fetch the initial count from MongoDB
    initial_count_doc = await votes.find_one({}, projection={"_id": False})
    if initial_count_doc:
        count = initial_count_doc.get("clicks", 0)
    else:
        count = 0

    try:
        while True:
            data = await websocket.receive_text()
            if data == "click":
                count += 1
                # Update the count in the "votes" collection
                await votes.update_one({}, {"$set": {"clicks": count}}, upsert=True)

            # Send the updated count to all connected clients
            await manager.send_to_all(str(count))
    except WebSocketDisconnect:
        pass 