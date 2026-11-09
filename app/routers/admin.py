from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import require_admin
from app.errors import AppError
from app.models import Product, User
from app.schemas import ProductCreate, ProductOut, ProductUpdate, UserCreate, UserOut, UserUpdate

router = APIRouter(prefix="/api/admin",
                   tags=["admin"],
                   dependencies=[Depends(require_admin)])


def _commit_or_conflict(db: Session, message: str) -> None:
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise AppError(409, message)


def _lock_row(db: Session, model, row_id: int):
    stmt = (select(model)
            .where(model.id == row_id)
            .with_for_update()
            .execution_options(populate_existing=True))
    return db.scalar(stmt)


@router.post("/products/", response_model=ProductOut, status_code=201)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    if db.scalar(select(Product).where(Product.name == payload.name)):
        raise AppError(409, "A product with this name already exists.")

    product = Product(**payload.model_dump())
    db.add(product)
    _commit_or_conflict(db, "A product with this name already exists.")
    db.refresh(product)
    return product


@router.patch("/products/{product_id}/", response_model=ProductOut)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = _lock_row(db, Product, product_id)
    if product is None:
        raise AppError(404, "Product not found.")

    changes = payload.model_dump(exclude_unset=True)
    new_name = changes.get("name")
    if new_name is not None and new_name != product.name:
        if db.scalar(select(Product).where(Product.name == new_name)):
            raise AppError(409, "A product with this name already exists.")

    for field, value in changes.items():
        setattr(product, field, value)

    _commit_or_conflict(db, "A product with this name already exists.")
    db.refresh(product)
    return product


@router.post("/users/", response_model=UserOut, status_code=201)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    if db.scalar(select(User).where(User.username == payload.username)):
        raise AppError(409, "A user with this username already exists.")

    user = User(**payload.model_dump())
    db.add(user)
    _commit_or_conflict(db, "A user with this username already exists.")
    db.refresh(user)
    return user


@router.patch("/users/{user_id}/", response_model=UserOut)
def update_user(user_id: int, payload: UserUpdate, db: Session = Depends(get_db)):
    user = _lock_row(db, User, user_id)
    if user is None:
        raise AppError(404, "User not found.")

    changes = payload.model_dump(exclude_unset=True)
    new_username = changes.get("username")
    if new_username is not None and new_username != user.username:
        if db.scalar(select(User).where(User.username == new_username)):
            raise AppError(409, "A user with this username already exists.")

    for field, value in changes.items():
        setattr(user, field, value)

    _commit_or_conflict(db, "A user with this username already exists.")
    db.refresh(user)
    return user
