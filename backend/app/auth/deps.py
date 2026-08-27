"""Auth dependencies: JWT verification + RBAC. Invalid credentials fail closed (401/403)."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.auth.security import decode_token
from app.database import get_db
from app.models import User

bearer = HTTPBearer(auto_error=True)

ROLE_RANK = {"FIELD_RESPONDER": 1, "OPERATOR": 2, "COMMANDER": 3, "ADMIN": 4, "AUDITOR": 5}


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: Session = Depends(get_db),
) -> User:
    try:
        payload = decode_token(credentials.credentials)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_ERROR", "message": "Invalid or expired token"},
        )
    user = db.get(User, int(payload.get("sub", 0)))
    if user is None or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "AUTHENTICATION_ERROR", "message": "User not found or deactivated"},
        )
    return user


def require_role(*roles: str):
    def checker(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail={"code": "AUTHORIZATION_ERROR", "message": f"Requires role: {', '.join(roles)}"},
            )
        return user

    return checker