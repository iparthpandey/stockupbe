from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class Product(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    sku: str = Field(index=True)
    price: float
    quantity: int
    items: List["OrderItem"] = Relationship(back_populates="product")


class Customer(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    full_name: str
    email: str = Field(index=True)
    phone: str
    orders: List["Order"] = Relationship(back_populates="customer")


class Order(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    customer_id: int = Field(foreign_key="customer.id")
    total_amount: float
    items: List["OrderItem"] = Relationship(back_populates="order")
    customer: Optional[Customer] = Relationship(back_populates="orders")


class OrderItem(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(foreign_key="order.id")
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    unit_price: float
    subtotal: float
    order: Optional[Order] = Relationship(back_populates="items")
    product: Optional[Product] = Relationship(back_populates="items")
