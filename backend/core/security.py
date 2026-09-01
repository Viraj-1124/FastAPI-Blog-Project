from datetime import datetime, timedelta
from typing import Optional
from jose import jwt


from core.config import settings

def create_access_token(data: dict , expires_delta: Optional[timedelta]=None):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=settings.ACCES_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp":expire})
    encoded_jwt = jwt.encode(to_encode,settings.SECRET_KEY,algorithm=settings.ALGORITHM)
    return encoded_jwt