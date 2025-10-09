import bcrypt
from datetime import datetime
from .db import db

class User:
    collection = db.users

    @classmethod
    def create(cls, username, email, password, role="patient"):
        if cls.collection.find_one({"$or": [{"username": username}, {"email": email}]}):
            return None
        hashed = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        user = {
            "username": username,
            "email": email,
            "password": hashed,
            "role": role,
            "created_at": datetime.utcnow(),
            "emergency_contacts": [],
            "profile": {
                "language": "en",
                "phone": "",
                "address": ""
            },
            "health_data": {
                "allergies": [],
                "chronic_conditions": []
            }
        }
        result = cls.collection.insert_one(user)
        user["_id"] = result.inserted_id
        return user

    @classmethod
    def find_by_username(cls, username):
        return cls.collection.find_one({"username": username})

    @classmethod
    def verify_password(cls, hashed, plain):
        return bcrypt.checkpw(plain.encode('utf-8'), hashed)