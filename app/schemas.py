from datetime import date, datetime
from decimal import Decimal
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator, model_validator

NonNegativeMoney = Annotated[Decimal, Field(ge=0, max_digits=12, decimal_places=2, allow_inf_nan=False)]
PositiveLitres = Annotated[Decimal, Field(gt=0, max_digits=12, decimal_places=2, allow_inf_nan=False)]
ProductName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
PersonName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]
Username = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=50)]


def _birthdate_not_in_future(value: date | None) -> date | None:
    if value is not None and value > date.today():
        raise ValueError("birthdate cannot be in the future.")
    return value


class StrictInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class UpdateInput(StrictInput):
    @model_validator(mode="after")
    def reject_empty_and_nulls(self):
        if not self.model_fields_set:
            raise ValueError("At least one field must be provided.")

        for field in self.model_fields_set:
            if getattr(self, field) is None:
                raise ValueError(f"{field} cannot be null.")

        return self


class ProductCreate(StrictInput):
    name: ProductName
    price_per_litre: NonNegativeMoney
    available_litres: NonNegativeMoney = Decimal("0.00")


class ProductUpdate(UpdateInput):
    name: ProductName | None = None
    price_per_litre: NonNegativeMoney | None = None
    available_litres: NonNegativeMoney | None = None


class ProductOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    price_per_litre: Decimal
    available_litres: Decimal


class UserCreate(StrictInput):
    first_name: PersonName
    last_name: PersonName
    username: Username
    birthdate: date
    account_balance: NonNegativeMoney = Decimal("0.00")

    _check_birthdate = field_validator("birthdate")(_birthdate_not_in_future)


class UserUpdate(UpdateInput):
    first_name: PersonName | None = None
    last_name: PersonName | None = None
    username: Username | None = None
    birthdate: date | None = None
    account_balance: NonNegativeMoney | None = None

    _check_birthdate = field_validator("birthdate")(_birthdate_not_in_future)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    first_name: str
    last_name: str
    username: str
    birthdate: date
    account_balance: Decimal


class PurchaseCreate(StrictInput):
    product_id: int = Field(gt=0)
    litres: PositiveLitres


class PurchaseCreatedOut(BaseModel):
    id: int
    product: str
    litres: Decimal
    total_price: Decimal
    remaining_balance: Decimal
    remaining_stock_litres: Decimal


class PurchaseOut(BaseModel):
    id: int
    product: str
    litres: Decimal
    total_price: Decimal
    created_at: datetime
