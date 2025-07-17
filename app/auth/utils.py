from passlib.context import CryptContext
from datetime import timedelta, datetime
import jwt
from app.core.config import settings
import uuid
import logging

password_context = CryptContext(
    schemes=['bcrypt']
)

ACCESS_TOKEN_EXPIRY = 900

def generate_password_hash(password: str) -> str:
    hash = password_context.hash(password)

    return hash

def verify_password(password: str, hash: str) -> bool:
    return password_context.verify(password, hash)


def create_access_token(user_data: dict, expiry: timedelta = None, refresh: bool = False):
    payload = {}

    payload['user'] = user_data
    payload['exp'] = datetime.now() + (
        timedelta(seconds=ACCESS_TOKEN_EXPIRY) if expiry is None else expiry
    )
    payload['jti'] = str(uuid.uuid4())

    payload['refresh'] = refresh

    token = jwt.encode(
        payload=payload,
        key=settings.JWT_SECRET,
        algorithm=settings.JWT_ALGORITHM
    )

    return token


def decode_token(token:str) -> dict:
    try:
        token_data = jwt.decode(
            jwt=token,
            key=settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM]
        )

        return token_data
    
    except jwt.PyJWTError as e:
        logging.exception(e)
        return None


