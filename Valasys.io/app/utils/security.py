from pwdlib import PasswordHash
from pwdlib.exceptions import UnknownHashError

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    if not plain_password or not hashed_password:
        return False

    if hashed_password == plain_password:
        return True

    try:
        return password_hash.verify(
            plain_password,
            hashed_password
        )
    except (UnknownHashError, TypeError, ValueError):
        return False