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

# MONGO_URI = uri
# client = AsyncIOMotorClient(MONGO_URI)
# db = client["Polling"]
# users = db["voters"]
# polls = db['polls']

async def open_db() -> AsyncIOMotorClient:
    app.state.mongodb = AsyncIOMotorClient(uri)
    app.state.polls = app.state.mongodb['Polling']['polls']

async def close_db():
    app.state.mongodb.close()

app.add_event_handler('startup', open_db)
app.add_event_handler('shutdown', close_db)

@app.post("/polls/",status_code=201)
async def create_poll(request:Request,poll: Poll):
    try:
        poll_data = poll.dict()

        slug = slugify.slugify(poll_data['title'])

        existing_poll = await request.app.state.polls.find_one({'slug': slug})
        counter = 1
        new_slug = None
        while existing_poll:
            new_slug = f"{slug}-{counter}"
            existing_poll = await request.app.state.polls.find_one({'slug': new_slug})
            counter += 1
        if new_slug:
            slug = new_slug
        poll_data['slug'] = slug
        print(poll_data)
        result = await request.app.state.polls.insert_one(poll_data)
        print(result)
        return {"message": "Poll created", "poll_slug": (poll_data['slug'])}
    except Exception as e:
        print(e.args)
        raise HTTPException(status_code=500, detail="Failed to create the poll")

@app.get("/polls/")
async def get_poll(poll_id: str,request:Request):
    try:
        poll_id = ObjectId(poll_id)
        poll_data = await request.app.state.polls.find_one({'_id': poll_id})
        if poll_data:
            poll_data['_id'] = str(poll_data['_id'])
        return poll_data
    except Exception as e:
        print(e.args)
        raise HTTPException(status_code=500, detail="Failed to fetch poll")

@app.get("/polls/{poll_slug}")
async def get_poll(poll_slug: str,request:Request):
    try:
        poll_data = await request.app.state.polls.find_one({'slug': poll_slug})
        if poll_data:
            poll_data['_id'] = str(poll_data['_id'])
        return templates.TemplateResponse("poll_view.html", {"request":request,"poll": poll_data})
    except Exception as e:
        print(e.args)
        raise HTTPException(status_code=500, detail="Failed to fetch poll")

@app.get("/", response_class=HTMLResponse)
async def get_homepage(request:Request):
    return templates.TemplateResponse("index.html",{"request":request})
