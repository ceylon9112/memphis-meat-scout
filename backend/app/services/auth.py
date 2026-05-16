from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import os

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)


def create_access_token(username: str) -> str:
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    expire_hours = int(os.getenv("ACCESS_TOKEN_EXPIRE_HOURS", "24"))
    payload = {
        "sub": username,
        "exp": datetime.utcnow() + timedelta(hours=expire_hours),
    }
    return jwt.encode(payload, secret, algorithm=algorithm)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    secret = os.getenv("JWT_SECRET_KEY", "dev-secret-key")
    algorithm = os.getenv("JWT_ALGORITHM", "HS256")
    try:
        payload = jwt.decode(credentials.credentials, secret, algorithms=[algorithm])
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return username
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")
