from fastapi import Depends, Header
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models import Admin, User
from app.security import verify_api_key


def require_admin(x_admin_key: str | None = Header(default=None), db: Session = Depends(get_db)) -> Admin:
    key = (x_admin_key or "").strip()
    if not key:
        raise AppError(401, "Missing X-Admin-Key header.")

    for admin in db.scalars(select(Admin)):
        if verify_api_key(key, admin.api_key_hash):
            return admin

    raise AppError(403, "Invalid admin API key.")


def get_current_user(x_username: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    username = (x_username or "").strip()
    if not username:
        raise AppError(401, "Missing X-Username header.")

    user = db.scalar(select(User).where(User.username == username))
    if user is None:
        raise AppError(404, "User not found.")

    return user
