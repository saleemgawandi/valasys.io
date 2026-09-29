import os

from dotenv import load_dotenv
from pymongo import MongoClient


load_dotenv()


MONGO_URI = os.getenv(
    "MONGO_URI",
    "mongodb://localhost:27017"
)

DATABASE_NAME = os.getenv(
    "MONGO_DATABASE",
    "Valasys"
)

CREDENTIAL_COLLECTION = os.getenv(
    "MONGO_COLLECTION",
    "credential"
)

client = MongoClient(MONGO_URI)

database = client[DATABASE_NAME]

credentials_collection = database[
    CREDENTIAL_COLLECTION
]

company_collection = database["Company_db"]
company_csv_filter_collection = database["Company_CSV_Filters"]


def get_credentials_collection():
    return credentials_collection


def get_company_collection():
    return company_collection


def get_company_csv_filter_collection():
    return company_csv_filter_collection