from pymongo import MongoClient
from dotenv import load_dotenv
import os

load_dotenv()

def get_database():
    cliente = MongoClient(os.getenv("MONGO_URL"))
    db = cliente["biblioteca"]
    return db
