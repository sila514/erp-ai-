from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    credentials_error = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Kimlik doğrulama başarısız",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = decode_access_token(token)
        username = payload.get("sub")
        if username is None:
            raise credentials_error
    except JWTError:
        raise credentials_error

    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise credentials_error
    return user


def require_role(*allowed_roles: str):
    """Belirli rollere sahip kullanıcılarla sınırlı endpoint'ler için dependency üretici."""

    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in allowed_roles:
            raise HTTPException(status_code=403, detail="Bu işlem için yetkiniz yok")
        return user

    return checker
