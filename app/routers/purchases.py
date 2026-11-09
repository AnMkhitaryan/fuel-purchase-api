from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.database import get_db
from app.dependencies import get_current_user
from app.models import Purchase, User
from app.schemas import PurchaseCreate, PurchaseCreatedOut, PurchaseOut
from app.services.purchases import create_purchase

router = APIRouter(prefix="/api/purchases", tags=["purchases"])


@router.post("/", response_model=PurchaseCreatedOut, status_code=201)
def purchase_fuel(
    payload: PurchaseCreate,
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    return create_purchase(db, user.id, payload.product_id, payload.litres)


@router.get("/", response_model=list[PurchaseOut])
def purchase_history(
    user: User = Depends(get_current_user),
    db: Session = Depends(get_db)):
    stmt = (select(Purchase)
            .options(joinedload(Purchase.product))
            .where(Purchase.user_id == user.id)
            .order_by(Purchase.created_at.desc(), Purchase.id.desc()))
    purchases = db.scalars(stmt).all()
    return [PurchaseOut(id=p.id, product=p.product.name, litres=p.litres, total_price=p.total_price,
                        created_at=p.created_at) for p in purchases]
