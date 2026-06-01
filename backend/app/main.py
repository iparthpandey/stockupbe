from fastapi import FastAPI, HTTPException, status, Depends
from sqlmodel import Session, select
from . import models, database, schemas

app = FastAPI(title="Inventory & Order Management - Backend")


@app.on_event("startup")
def on_startup():
    database.init_db()


def get_session():
    with Session(database.engine) as session:
        yield session


### Products
@app.post("/products", response_model=schemas.ProductRead, status_code=status.HTTP_201_CREATED)
def create_product(payload: schemas.ProductCreate, session: Session = Depends(get_session)):
    # uniqueness check SKU
    existing = session.exec(select(models.Product).where(models.Product.sku == payload.sku)).first()
    if existing:
        raise HTTPException(status_code=400, detail="SKU must be unique")
    if payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    product = models.Product.from_orm(payload)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.get("/products", response_model=list[schemas.ProductRead])
def list_products(session: Session = Depends(get_session)):
    products = session.exec(select(models.Product)).all()
    return products


@app.get("/products/{product_id}", response_model=schemas.ProductRead)
def get_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/products/{product_id}", response_model=schemas.ProductRead)
def update_product(product_id: int, payload: schemas.ProductUpdate, session: Session = Depends(get_session)):
    product = session.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if payload.sku and payload.sku != product.sku:
        existing = session.exec(select(models.Product).where(models.Product.sku == payload.sku)).first()
        if existing:
            raise HTTPException(status_code=400, detail="SKU must be unique")
    if payload.quantity is not None and payload.quantity < 0:
        raise HTTPException(status_code=400, detail="Quantity cannot be negative")
    product_data = payload.dict(exclude_unset=True)
    for key, value in product_data.items():
        setattr(product, key, value)
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@app.delete("/products/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_product(product_id: int, session: Session = Depends(get_session)):
    product = session.get(models.Product, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    session.delete(product)
    session.commit()
    return None


### Customers
@app.post("/customers", response_model=schemas.CustomerRead, status_code=status.HTTP_201_CREATED)
def create_customer(payload: schemas.CustomerCreate, session: Session = Depends(get_session)):
    existing = session.exec(select(models.Customer).where(models.Customer.email == payload.email)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Customer email must be unique")
    customer = models.Customer.from_orm(payload)
    session.add(customer)
    session.commit()
    session.refresh(customer)
    return customer


@app.get("/customers", response_model=list[schemas.CustomerRead])
def list_customers(session: Session = Depends(get_session)):
    return session.exec(select(models.Customer)).all()


@app.get("/customers/{customer_id}", response_model=schemas.CustomerRead)
def get_customer(customer_id: int, session: Session = Depends(get_session)):
    customer = session.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@app.delete("/customers/{customer_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_customer(customer_id: int, session: Session = Depends(get_session)):
    customer = session.get(models.Customer, customer_id)
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    session.delete(customer)
    session.commit()
    return None


### Orders
@app.post("/orders", response_model=schemas.OrderRead, status_code=status.HTTP_201_CREATED)
def create_order(payload: schemas.OrderCreate, session: Session = Depends(get_session)):
    # check customer exists
    customer = session.get(models.Customer, payload.customer_id)
    if not customer:
        raise HTTPException(status_code=400, detail="Customer does not exist")

    # prepare items, check stock
    items = []
    total = 0.0
    for it in payload.items:
        product = session.get(models.Product, it.product_id)
        if not product:
            raise HTTPException(status_code=400, detail=f"Product {it.product_id} does not exist")
        if product.quantity < it.quantity:
            raise HTTPException(status_code=400, detail=f"Insufficient stock for product {product.id}")
        if it.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be positive")
        unit_price = product.price
        subtotal = unit_price * it.quantity
        total += subtotal
        items.append((product, it.quantity, unit_price, subtotal))

    # create order
    order = models.Order(customer_id=payload.customer_id, total_amount=round(total, 2))
    session.add(order)
    session.commit()
    session.refresh(order)

    # create items and reduce stock
    for product, qty, unit_price, subtotal in items:
        order_item = models.OrderItem(order_id=order.id, product_id=product.id, quantity=qty, unit_price=unit_price, subtotal=subtotal)
        session.add(order_item)
        product.quantity = product.quantity - qty
        session.add(product)

    session.commit()
    session.refresh(order)
    return schemas.OrderRead.from_orm(order)


@app.get("/orders", response_model=list[schemas.OrderRead])
def list_orders(session: Session = Depends(get_session)):
    return session.exec(select(models.Order)).all()


@app.get("/orders/{order_id}", response_model=schemas.OrderRead)
def get_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(models.Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@app.delete("/orders/{order_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_order(order_id: int, session: Session = Depends(get_session)):
    order = session.get(models.Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    # restore stock
    for item in order.items:
        product = session.get(models.Product, item.product_id)
        if product:
            product.quantity += item.quantity
            session.add(product)
    # delete items and order
    for item in order.items:
        session.delete(item)
    session.delete(order)
    session.commit()
    return None
