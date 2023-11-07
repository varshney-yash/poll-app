from fastapi import FastAPI, HTTPException, Request, WebSocket, Depends, Response, WebSocketDisconnect
from motor.motor_asyncio import AsyncIOMotorClient
from db import uri
from models import Poll
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import slugify
import asyncio
from typing import List
from pydantic import BaseModel
from uuid import UUID, uuid4
from fastapi_sessions.backends.implementations import InMemoryBackend
from fastapi_sessions.session_verifier import SessionVerifier
from fastapi_sessions.frontends.implementations import SessionCookie, CookieParameters



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
    except WebSocketDisconnect as e:
        print(e)


class SessionData(BaseModel):
    username: str


cookie_params = CookieParameters()

# Uses UUID
cookie = SessionCookie(
    cookie_name="cookie",
    identifier="general_verifier",
    auto_error=True,
    secret_key="DONOTUSE",
    cookie_params=cookie_params,
)
backend = InMemoryBackend[UUID, SessionData]()


class BasicVerifier(SessionVerifier[UUID, SessionData]):
    def __init__(
        self,
        *,
        identifier: str,
        auto_error: bool,
        backend: InMemoryBackend[UUID, SessionData],
        auth_http_exception: HTTPException,
    ):
        self._identifier = identifier
        self._auto_error = auto_error
        self._backend = backend
        self._auth_http_exception = auth_http_exception

    @property
    def identifier(self):
        return self._identifier

    @property
    def backend(self):
        return self._backend

    @property
    def auto_error(self):
        return self._auto_error

    @property
    def auth_http_exception(self):
        return self._auth_http_exception

    def verify_session(self, model: SessionData) -> bool:
        """If the session exists, it is valid"""
        return True


verifier = BasicVerifier(
    identifier="general_verifier",
    auto_error=True,
    backend=backend,
    auth_http_exception=HTTPException(status_code=403, detail="invalid session"),
)


@app.post("/create_session/{name}")
async def create_session(name: str, response: Response):

    session = uuid4()
    data = SessionData(username=name)

    await backend.create(session, data)
    cookie.attach_to_response(response, session)

    return f"created session for {name}"


@app.get("/whoami", dependencies=[Depends(cookie)])
async def whoami(session_data: SessionData = Depends(verifier)):
    return session_data


@app.post("/delete_session")
async def del_session(response: Response, session_id: UUID = Depends(cookie)):
    await backend.delete(session_id)
    cookie.delete_from_response(response)
    return "deleted session"