from sqlmodel import SQLModel, Field
from typing import Optional, List


class ProductBase(SQLModel):
    name: str
    sku: str
    price: float
    quantity: int


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    id: int


class ProductUpdate(SQLModel):
    name: Optional[str] = None
    sku: Optional[str] = None
    price: Optional[float] = None
    quantity: Optional[int] = None


class CustomerBase(SQLModel):
    full_name: str
    email: str
    phone: str


class CustomerCreate(CustomerBase):
    pass


class CustomerRead(CustomerBase):
    id: int


class OrderItemCreate(SQLModel):
    product_id: int
    quantity: int


class OrderCreate(SQLModel):
    customer_id: int
    items: List[OrderItemCreate]


class OrderItemRead(SQLModel):
    id: int
    product_id: int
    quantity: int
    unit_price: float
    subtotal: float


class OrderRead(SQLModel):
    id: int
    customer_id: int
    total_amount: float
    items: List[OrderItemRead] = []
