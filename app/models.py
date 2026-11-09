from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import CheckConstraint, Date, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class Admin(Base):
    __tablename__ = "admins"

    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    api_key_hash: Mapped[str] = mapped_column(String(255), unique=True)


class User(Base):
    __tablename__ = "users"
    __table_args__ = (CheckConstraint("account_balance >= 0", name="ck_users_balance_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    first_name: Mapped[str] = mapped_column(String(100))
    last_name: Mapped[str] = mapped_column(String(100))
    username: Mapped[str] = mapped_column(String(50), unique=True)
    birthdate: Mapped[date] = mapped_column(Date)
    account_balance: Mapped[Decimal] = mapped_column(Numeric(12, 2),
                                                     default=Decimal("0.00"),
                                                     server_default="0.00")


class Product(Base):
    __tablename__ = "products"
    __table_args__ = (
        CheckConstraint("price_per_litre >= 0", name="ck_products_price_non_negative"),
        CheckConstraint("available_litres >= 0", name="ck_products_stock_non_negative"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True)
    price_per_litre: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    available_litres: Mapped[Decimal] = mapped_column(Numeric(12, 2),
                                                      default=Decimal("0.00"),
                                                      server_default="0.00")


class Purchase(Base):
    __tablename__ = "purchases"
    __table_args__ = (CheckConstraint("litres > 0", name="ck_purchases_litres_positive"),
                      Index("ix_purchases_user_created", "user_id", "created_at"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"))
    litres: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    price_per_litre: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    total_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    product: Mapped["Product"] = relationship()
