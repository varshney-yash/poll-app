from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import urllib.parse

from dotenv import load_dotenv
load_dotenv()                 

import os 

username = os.environ.get('mongo_username')
passw = os.environ.get('mongo_password')


username_bytes = username.encode('utf-8')
passw_bytes = passw.encode('utf-8')

username_encoded = urllib.parse.quote_plus(username_bytes)
passw_encoded = urllib.parse.quote_plus(passw_bytes)

uri = f"mongodb+srv://{username}:{passw}@cluster0.wvqfpmi.mongodb.net/?retryWrites=true&w=majority"
