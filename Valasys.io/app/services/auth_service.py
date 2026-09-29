from app.database.mongodb import get_credentials_collection
from app.utils.security import verify_password


def authenticate_user(
    email: str,
    password: str
):
    collection = get_credentials_collection()

    user = collection.find_one(
        {
            "email": email.lower().strip()
        }
    )

    if not user:
        return None

    stored_password = user.get("password")

    if not stored_password:
        return None

    if not verify_password(password, stored_password):
        return None

    return user