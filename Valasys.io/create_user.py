from pymongo import MongoClient
from pwdlib import PasswordHash


MONGO_URI = "mongodb://localhost:27017"

client = MongoClient(MONGO_URI)

db = client["Valasys"]

collection = db["credential"]


password_hash = PasswordHash.recommended()


email = "akash@valasys.io"
name = "Akash Rathore"
password = "Akash@123"


hashed_password = password_hash.hash(
    password
)


collection.update_one(
    {
        "email": email
    },
    {
        "$set": {
            "email": email,
            "name": name,
            "password": hashed_password
        }
    },
    upsert=True
)


print("User created successfully.")
print("Name:", name)
print("Email:", email)
print("Password:", password)