import os
from pymongo import MongoClient
import bcrypt

# 🔐 Mongo URI (best: env variable use kar)
MONGO_URI = os.getenv("MONGO_URI")

# fallback (agar env set nahi hai)
if not MONGO_URI:
    MONGO_URI = "mongodb+srv://harshitgupta241005_db_user:k9DjQ1ho4gJEclbL@cluster0.z7evgik.mongodb.net/"

client = MongoClient(MONGO_URI)
db = client["bullspire"]
# collection = db["users"]

print(client.list_database_names())