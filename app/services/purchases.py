from decimal import ROUND_HALF_UP, Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.errors import AppError
from app.models import Product, Purchase, User
from app.schemas import PurchaseCreatedOut

CENT = Decimal("0.01")


def _lock(db: Session, model, row_id: int):
    stmt = (select(model)
            .where(model.id == row_id)
            .with_for_update()
            .execution_options(populate_existing=True))
    return db.scalar(stmt)


def create_purchase(
    db: Session, user_id: int, product_id: int, litres: Decimal) -> PurchaseCreatedOut:
    try:
        product = _lock(db, Product, product_id)
        if product is None:
            raise AppError(404, "Product not found.")
        user = _lock(db, User, user_id)

        if user is None:
            raise AppError(404, "User not found.")

        if product.available_litres < litres:
            raise AppError(400, "Not enough fuel available.")

        total_price = (product.price_per_litre * litres).quantize(CENT, rounding=ROUND_HALF_UP)
        if user.account_balance < total_price:
            raise AppError(400, "Insufficient balance.")

        user.account_balance -= total_price
        product.available_litres -= litres
        purchase = Purchase(user_id=user.id,
                            product_id=product.id,
                            litres=litres,
                            price_per_litre=product.price_per_litre,
                            total_price=total_price)
        db.add(purchase)
        db.commit()
    except Exception:
        db.rollback()
        raise

    db.refresh(purchase)
    db.refresh(user)
    db.refresh(product)
    return PurchaseCreatedOut(id=purchase.id,
                              product=product.name,
                              litres=purchase.litres,
                              total_price=purchase.total_price,
                              remaining_balance=user.account_balance,
                              remaining_stock_litres=product.available_litres)
