import uuid
import random
from typing import List, Dict
import pytest

class User:
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email

class Customer(User):
    def __init__(self, user_id: str, name: str, email: str, is_bulk_buyer: bool):
        super().__init__(user_id, name, email)
        self.is_bulk_buyer = is_bulk_buyer
        self.cart = []
        self.orders = []

class Product:
    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

class CartItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

class Order:
    def __init__(self, order_id: str, customer: Customer, items: List[CartItem], discount: float = 0.0):
        self.order_id = order_id
        self.customer = customer
        self.items = items
        self.discount = discount
        self.total_price = sum(item.product.price * item.quantity for item in items) * (1 - discount)
        self.status = "Processing"

    def update_status(self, new_status: str):
        self.status = new_status

class Store:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.load_sample_data()

    def load_sample_data(self):
        sample_products = [
            Product(str(uuid.uuid4()), "Laptop", "Electronics", 1000, 10),
            Product(str(uuid.uuid4()), "Shampoo", "Personal Care", 10, 50),
            Product(str(uuid.uuid4()), "Rice", "Grocery", 5, 100),
        ]
        for product in sample_products:
            self.products[product.product_id] = product

    def search_product(self, name: str):
        return [p for p in self.products.values() if name.lower() in p.name.lower()]

    def add_to_cart(self, customer_id: str, product_id: str, quantity: int):
        customer = self.customers.get(customer_id)
        product = self.products.get(product_id)
        if not customer or not product:
            return "Customer or Product not found."
        if product.stock < quantity:
            return "Insufficient stock."
        customer.cart.append(CartItem(product, quantity))
        return "Added to cart."

    def checkout(self, customer_id: str):
        customer = self.customers.get(customer_id)
        if not customer or not customer.cart:
            return "Cart is empty."
        discount = 0.1 if customer.is_bulk_buyer else 0.0
        order = Order(str(uuid.uuid4()), customer, customer.cart, discount)
        self.orders[order.order_id] = order
        customer.orders.append(order)
        customer.cart = []
        return f"Order placed successfully! Order ID: {order.order_id}"

# PyTest Unit Tests
@pytest.fixture
def store():
    return Store()

@pytest.fixture
def customer(store):
    customer = Customer("cust123", "Alice", "alice@example.com", False)
    store.customers[customer.user_id] = customer
    return customer

@pytest.fixture
def bulk_customer(store):
    customer = Customer("cust456", "Bob", "bob@example.com", True)
    store.customers[customer.user_id] = customer
    return customer

@pytest.fixture
def product(store):
    return next(iter(store.products.values()))
import uuid
import random
from typing import List, Dict
import pytest

class User:
    def __init__(self, user_id: str, name: str, email: str):
        self.user_id = user_id
        self.name = name
        self.email = email

class Customer(User):
    def __init__(self, user_id: str, name: str, email: str, is_bulk_buyer: bool):
        super().__init__(user_id, name, email)
        self.is_bulk_buyer = is_bulk_buyer
        self.cart = []
        self.orders = []

class Product:
    def __init__(self, product_id: str, name: str, category: str, price: float, stock: int):
        self.product_id = product_id
        self.name = name
        self.category = category
        self.price = price
        self.stock = stock

class CartItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

class Order:
    def __init__(self, order_id: str, customer: Customer, items: List[CartItem], discount: float = 0.0):
        self.order_id = order_id
        self.customer = customer
        self.items = items
        self.discount = discount
        self.total_price = sum(item.product.price * item.quantity for item in items) * (1 - discount)
        self.status = "Processing"

    def update_status(self, new_status: str):
        self.status = new_status

class Store:
    def __init__(self):
        self.products: Dict[str, Product] = {}
        self.orders: Dict[str, Order] = {}
        self.customers: Dict[str, Customer] = {}
        self.load_sample_data()

    def load_sample_data(self):
        sample_products = [
            Product(str(uuid.uuid4()), "Laptop", "Electronics", 1000, 10),
            Product(str(uuid.uuid4()), "Shampoo", "Personal Care", 10, 50),
            Product(str(uuid.uuid4()), "Rice", "Grocery", 5, 100),
        ]
        for product in sample_products:
            self.products[product.product_id] = product

    def search_product(self, name: str):
        return [p for p in self.products.values() if name.lower() in p.name.lower()]

    def add_to_cart(self, customer_id: str, product_id: str, quantity: int):
        customer = self.customers.get(customer_id)
        product = self.products.get(product_id)
        if not customer or not product:
            return "Customer or Product not found."
        if product.stock < quantity:
            return "Insufficient stock."
        customer.cart.append(CartItem(product, quantity))
        return "Added to cart."

    def checkout(self, customer_id: str):
        customer = self.customers.get(customer_id)
        if not customer or not customer.cart:
            return "Cart is empty."
        discount = 0.1 if customer.is_bulk_buyer else 0.0
        order = Order(str(uuid.uuid4()), customer, customer.cart, discount)
        self.orders[order.order_id] = order
        customer.orders.append(order)
        customer.cart = []
        return f"Order placed successfully! Order ID: {order.order_id}"

# PyTest Unit Tests
@pytest.fixture
def store():
    return Store()

@pytest.fixture
def customer(store):
    customer = Customer("cust123", "Alice", "alice@example.com", False)
    store.customers[customer.user_id] = customer
    return customer

@pytest.fixture
def bulk_customer(store):
    customer = Customer("cust456", "Bob", "bob@example.com", True)
    store.customers[customer.user_id] = customer
    return customer

@pytest.fixture
def product(store):
    return next(iter(store.products.values()))

def test_search_product(store):
    results = store.search_product("Laptop")
    assert len(results) > 0
    assert results[0].name == "Laptop"

def test_add_to_cart(store, customer, product):
    response = store.add_to_cart(customer.user_id, product.product_id, 1)
    assert response == "Added to cart."
    assert len(customer.cart) == 1

def test_checkout(store, customer, product):
    store.add_to_cart(customer.user_id, product.product_id, 1)
    response = store.checkout(customer.user_id)
    assert "Order placed successfully!" in response
    assert len(customer.orders) == 1

def test_bulk_order_discount(store, bulk_customer, product):
    store.add_to_cart(bulk_customer.user_id, product.product_id, 1)
    store.checkout(bulk_customer.user_id)
    assert bulk_customer.orders[0].discount == 0.1

def test_search_product(store):
    results = store.search_product("Laptop")
    assert len(results) > 0
    assert results[0].name == "Laptop"

def test_add_to_cart(store, customer, product):
    response = store.add_to_cart(customer.user_id, product.product_id, 1)
    assert response == "Added to cart."
    assert len(customer.cart) == 1

def test_checkout(store, customer, product):
    store.add_to_cart(customer.user_id, product.product_id, 1)
    response = store.checkout(customer.user_id)
    assert "Order placed successfully!" in response
    assert len(customer.orders) == 1

def test_bulk_order_discount(store, bulk_customer, product):
    store.add_to_cart(bulk_customer.user_id, product.product_id, 1)
    store.checkout(bulk_customer.user_id)
    assert bulk_customer.orders[0].discount == 0.1
