from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import urllib.parse

from dotenv import load_dotenv
load_dotenv()                 

import os 

username = os.environ.get('mongo-username')
passw = os.environ.get('mongo-password')


username = urllib.parse.quote_plus(username)
passw = urllib.parse.quote_plus(passw)

uri = f"mongodb+srv://{username}:{passw}@cluster0.wvqfpmi.mongodb.net/?retryWrites=true&w=majority"

client = MongoClient(uri, server_api=ServerApi('1'))

try:
    client.admin.command('ping')
    print("Pinged your deployment. You successfully connected to MongoDB!")
except Exception as e:
    print(e.args)db.py
