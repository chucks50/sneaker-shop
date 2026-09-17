from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config import settings

jwt_secret_key = settings.jwt_secret_key
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
ALGORITHM = settings.jwt_algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes
RESET_TOKEN_EXPIRE_MINUTES = 15


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return pwd_context.verify(password, hashed_password)


def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, jwt_secret_key, algorithm=ALGORITHM)


def create_reset_token(email: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=RESET_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": email, "purpose": "password_reset", "exp": expire}
    return jwt.encode(payload, jwt_secret_key, algorithm=ALGORITHM)


def decode_access_token(token: str):
    try:
        return jwt.decode(token, jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None


def decode_reset_token(token: str):
    try:
        payload = jwt.decode(token, jwt_secret_key, algorithms=[ALGORITHM])
    except JWTError:
        return None

    if payload.get("purpose") != "password_reset":
        return None
    return payload


def get_current_user_from_token(token: str):
    payload = decode_access_token(token)
    if payload is None:
        return None

    user_id = payload.get("sub")
    if user_id is None:
        return None
    return user_id