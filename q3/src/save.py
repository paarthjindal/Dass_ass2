import os
import json
import uuid
import datetime
import random
from abc import ABC, abstractmethod
from typing import List, Dict, Optional, Union

# ----- Model Classes -----

class User(ABC):
    def __init__(self, user_id: str, name: str, email: str, address: str, phone: str):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.address = address
        self.phone = phone
        self.loyalty_points = 0

    @abstractmethod
    def get_discount_rate(self) -> float:
        pass


class IndividualCustomer(User):
    def __init__(self, user_id: str, name: str, email: str, address: str, phone: str):
        super().__init__(user_id, name, email, address, phone)

    def get_discount_rate(self) -> float:
        # Base discount based on loyalty points
        if self.loyalty_points >= 1000:
            return 0.10  # 10% discount
        elif self.loyalty_points >= 500:
            return 0.05  # 5% discount
        return 0.0  # No discount


class RetailStore(User):
    def __init__(self, user_id: str, name: str, email: str, address: str, phone: str,
                 business_license: str, monthly_purchase_volume: float):
        super().__init__(user_id, name, email, address, phone)
        self.business_license = business_license
        self.monthly_purchase_volume = monthly_purchase_volume

    def get_discount_rate(self) -> float:
        # Bulk discount based on monthly purchase volume
        if self.monthly_purchase_volume >= 10000:
            return 0.20  # 20% discount
        elif self.monthly_purchase_volume >= 5000:
            return 0.15  # 15% discount
        elif self.monthly_purchase_volume >= 1000:
            return 0.10  # 10% discount
        return 0.05  # 5% base discount for all retail stores


class Category:
    def __init__(self, category_id: str, name: str, description: str):
        self.category_id = category_id
        self.name = name
        self.description = description

class Product:
    def __init__(self, product_id: str, name: str, description: str, price: float, category_id: str, stock_quantity: int):
        self.product_id = product_id
        self.name = name
        self.description = description
        self.price = price
        self.category_id = category_id
        self.stock_quantity = stock_quantity


class CartItem:
    def __init__(self, product: Product, quantity: int):
        self.product = product
        self.quantity = quantity

    def get_subtotal(self, user: User) -> float:
        unit_price = self.product.price

        # Apply bulk discount for retail stores based on monthly purchase volume
        if isinstance(user, RetailStore):
            unit_price *= (1 - user.get_discount_rate())

        # Apply user-specific discount (loyalty-based for individuals)
        return unit_price * self.quantity


class ShoppingCart:
    def __init__(self, user, datastore):
        self.user = user
        self.datastore = datastore  # Added datastore reference
        self.items = []
        self.file_path = "carts.json"
        self.load_cart()

    def add_item(self, product: Product, quantity: int):
        # Check if product already in cart
        for item in self.items:
            if item.product.product_id == product.product_id:
                item.quantity += quantity
                return

        # Add new item to cart
        self.items.append(CartItem(product, quantity))
        self.save_cart()

    def remove_item(self, product_id: str):
        self.items = [item for item in self.items if item.product.product_id != product_id]
        self.save_cart()

    def save_cart(self):
        cart_data = {
            "user_id": self.user.user_id,
            "items": [
                {"product_id": item.product.product_id, "quantity": item.quantity} for item in self.items
            ]
        }
        try:
            with open(self.file_path, "w") as f:
                json.dump(cart_data, f, indent=4)
        except Exception as e:
            print(f"Error saving cart: {e}")

    def load_cart(self):
        try:
            with open(self.file_path, "r") as f:
                cart_data = json.load(f)
                if cart_data.get("user_id") == self.user.user_id:
                    for item in cart_data.get("items", []):
                        product_data = self.datastore.get_product(item["product_id"])  # Fetch actual product
                        if product_data:
                            product = Product(
                                product_id=product_data["product_id"],
                                name=product_data["name"],
                                description=product_data["description"],
                                price=product_data["price"],
                                category_id=product_data["category_id"],
                                stock_quantity=product_data["stock_quantity"]
                            )
                            self.items.append(CartItem(product, item["quantity"]))
        except (FileNotFoundError, json.JSONDecodeError):
            pass
    def update_quantity(self, product_id: str, quantity: int):
        for item in self.items:
            if item.product.product_id == product_id:
                if quantity <= 0:
                    self.remove_item(product_id)
                else:
                    item.quantity = quantity
                return

    def get_total(self) -> float:
        discount_rate = self.user.get_discount_rate()
        return sum(item.get_subtotal(discount_rate) for item in self.items)

    def clear(self):
        self.items = []


class OrderStatus:
    CREATED = "created"
    PROCESSING = "processing"
    SHIPPED = "shipped"
    DELIVERED = "delivered"
    CANCELLED = "cancelled"


class DeliveryMethod:
    STANDARD = "standard"
    EXPRESS = "express"
    STORE_PICKUP = "store_pickup"


class Order:
    def __init__(self, order_id: str, user: User, items: List[CartItem],
                 delivery_method: str, delivery_address: str):
        self.order_id = order_id
        self.user = user
        self.items = items.copy()  # Make a copy of the items
        self.order_date = datetime.datetime.now()
        self.status = OrderStatus.CREATED
        self.delivery_method = delivery_method
        self.delivery_address = delivery_address
        self.estimated_delivery_date = self._calculate_delivery_date()
        self.discount_rate = user.get_discount_rate()
        self.total_amount = sum(item.get_subtotal(self.discount_rate) for item in items)

        # Add delivery fee
        if delivery_method == DeliveryMethod.EXPRESS:
            self.delivery_fee = 15.00
        elif delivery_method == DeliveryMethod.STANDARD:
            self.delivery_fee = 5.00
        else:  # Store pickup
            self.delivery_fee = 0.00

        self.total_amount += self.delivery_fee

    def _calculate_delivery_date(self) -> datetime.datetime:
        today = datetime.datetime.now()
        if self.delivery_method == DeliveryMethod.EXPRESS:
            return today + datetime.timedelta(days=1)
        elif self.delivery_method == DeliveryMethod.STANDARD:
            return today + datetime.timedelta(days=3)
        else:  # Store pickup
            return today + datetime.timedelta(hours=2)

    def update_status(self, new_status: str):
        self.status = new_status
        # Award loyalty points when order is delivered
        if new_status == OrderStatus.DELIVERED:
            # Round to nearest integer
            points_to_award = int(self.total_amount)
            self.user.loyalty_points += points_to_award

    def get_delivery_status(self) -> str:
        return self.status

    def mark_as_shipped(self):
        if self.status == OrderStatus.CREATED or self.status == OrderStatus.PROCESSING:
            self.status = OrderStatus.SHIPPED
            print(f"Order {self.order_id} has been shipped.")
        else:
            print(f"Cannot mark order {self.order_id} as shipped. Current status: {self.status}")

    def mark_as_delivered(self):
        if self.status == OrderStatus.SHIPPED:
            self.status = OrderStatus.DELIVERED
            print(f"Order {self.order_id} has been delivered.")
        else:
            print(f"Cannot mark order {self.order_id} as delivered. Current status: {self.status}")

class Coupon:
    def __init__(self, coupon_id: str, code: str, discount_amount: float,
                 min_purchase_amount: float, expiry_date: datetime.datetime):
        self.coupon_id = coupon_id
        self.code = code
        self.discount_amount = discount_amount  # Flat discount amount
        self.min_purchase_amount = min_purchase_amount
        self.expiry_date = expiry_date
        self.is_used = False

    def is_valid(self, purchase_amount: float) -> bool:
        if self.is_used:
            return False
        if datetime.datetime.now() > self.expiry_date:
            return False
        if purchase_amount < self.min_purchase_amount:
            return False
        return True

    def apply(self, purchase_amount: float) -> float:
        if self.is_valid(purchase_amount):
            self.is_used = True
            return min(self.discount_amount, purchase_amount)
        return 0.0


class DataStore:
    def __init__(self, initialize_with_demo_data=True):
        # File paths
        self.users_file = "users.json"
        self.products_file = "products.json"
        self.categories_file = "categories.json"
        self.orders_file = "orders.json"
        self.coupons_file = "coupons.json"
        self.carts_file = "carts.json"

        # Initialize storage dictionaries
        self.users = {}
        self.products = {}
        self.categories = {}
        self.orders = {}
        self.coupons = {}
        self.carts = {}

        # Load existing data or create demo data
        if initialize_with_demo_data:
            self.initialize_demo_data()
        else:
            self.load_all_data()

    def load_all_data(self):
        """Load all data from JSON files"""
        self.load_data(self.users_file, "users")
        self.load_data(self.products_file, "products")
        self.load_data(self.categories_file, "categories")
        self.load_data(self.orders_file, "orders")
        self.load_data(self.coupons_file, "coupons")
        self.load_data(self.carts_file, "carts")
    def load_data(self, file_path: str, data_type: str):
        """Load data from a specific JSON file"""
        if os.path.exists(file_path):
            try:
                with open(file_path, "r") as f:
                    data = json.load(f)
                    if data_type == "users":
                        self.users = data
                    elif data_type == "products":
                        self.products = data
                    elif data_type == "categories":
                        self.categories = data
                    elif data_type == "orders":
                        self.orders = data
                    elif data_type == "coupons":
                        self.coupons = data
                print(f"Loaded {len(data)} {data_type} from {file_path}")
            except Exception as e:
                print(f"Error loading {data_type} from {file_path}: {e}")
                # If there's an error, initialize with empty data
                self._set_empty_data(data_type)
        else:
            print(f"File {file_path} does not exist. Initializing empty {data_type}.")
            self._set_empty_data(data_type)

    def _set_empty_data(self, data_type: str):
        """Set empty data for a specific data type"""
        if data_type == "users":
            self.users = {}
        elif data_type == "products":
            self.products = {}
        elif data_type == "categories":
            self.categories = {}
        elif data_type == "orders":
            self.orders = {}
        elif data_type == "coupons":
            self.coupons = {}

    def save_all_data(self):
        """Save all data to JSON files"""
        self.save_data(self.users_file, self.users)
        self.save_data(self.products_file, self.products)
        self.save_data(self.categories_file, self.categories)
        self.save_data(self.orders_file, self.orders)
        self.save_data(self.coupons_file, self.coupons)

    def save_data(self, file_path: str, data: Dict):
        """Save data to a specific JSON file"""
        try:
            with open(file_path, "w") as f:
                json.dump(data, f, indent=2, default=self._json_serializer)
            print(f"Saved data to {file_path}")
        except Exception as e:
            print(f"Error saving data to {file_path}: {e}")

    def _json_serializer(self, obj):
        """Custom JSON serializer for handling datetime objects"""
        if isinstance(obj, datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M:%S")
        raise TypeError(f"Type {type(obj)} not serializable")

    # User operations
    def add_user(self, user_id: str, user_data: Dict):
        self.users[user_id] = user_data
        self.save_data(self.users_file, self.users)

    def get_user(self, user_id: str) -> Optional[Dict]:
        return self.users.get(user_id)

    def get_all_users(self) -> Dict:
        return self.users

    def update_user(self, user_id: str, user_data: Dict):
        if user_id in self.users:
            self.users[user_id] = user_data
            self.save_data(self.users_file, self.users)
            return True
        return False

    # Product operations
    def add_product(self, product_id: str, product_data: Dict):
        self.products[product_id] = product_data
        self.save_data(self.products_file, self.products)

    def get_product(self, product_id: str) -> Optional[Dict]:
        return self.products.get(product_id)

    def get_all_products(self) -> Dict:
        return self.products

    def update_product(self, product_id: str, product_data: Dict):
        if product_id in self.products:
            self.products[product_id] = product_data
            self.save_data(self.products_file, self.products)
            return True
        return False

    # Category operations
    def add_category(self, category_id: str, category_data: Dict):
        self.categories[category_id] = category_data
        self.save_data(self.categories_file, self.categories)

    def get_category(self, category_id: str) -> Optional[Dict]:
        return self.categories.get(category_id)

    def get_all_categories(self) -> Dict:
        return self.categories

    # Order operations
    def add_order(self, order_id: str, order_data: Dict):
        self.orders[order_id] = order_data
        self.save_data(self.orders_file, self.orders)

    def get_order(self, order_id: str) -> Optional[Dict]:
        return self.orders.get(order_id)

    def get_all_orders(self) -> Dict:
        return self.orders

    def update_order(self, order_id: str, order_data: dict):
        try:
            with open("orders.json", "r") as f:
                orders = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            orders = {}

        orders[order_id] = order_data  # Overwrite with updated order

        try:
            with open("orders.json", "w") as f:
                json.dump(orders, f, indent=4)
        except Exception as e:
            print(f"Error saving order data: {e}")


    # Coupon operations
    def add_coupon(self, coupon_id: str, coupon_data: Dict):
        self.coupons[coupon_id] = coupon_data
        self.save_data(self.coupons_file, self.coupons)

    def get_coupon(self, coupon_id: str) -> Optional[Dict]:
        return self.coupons.get(coupon_id)

    def get_all_coupons(self) -> Dict:
        return self.coupons

    def update_coupon(self, coupon_id: str, coupon_data: Dict):
        if coupon_id in self.coupons:
            self.coupons[coupon_id] = coupon_data
            self.save_data(self.coupons_file, self.coupons)
            return True
        return False

    # Helper methods for finding data
    def find_products_by_category(self, category_id: str) -> List[Dict]:
        return [product for product_id, product in self.products.items()
                if product.get("category_id") == category_id]

    def find_orders_by_user(self, user_id: str) -> List[Dict]:
        return [order for order_id, order in self.orders.items()
                if order.get("user_id") == user_id]

    def search_products(self, query: str) -> List[Dict]:
        query = query.lower()
        return [product for product_id, product in self.products.items()
                if query in product.get("name", "").lower() or
                query in product.get("description", "").lower()]

    def get_coupon_by_code(self, code: str) -> Optional[Dict]:
        for coupon_id, coupon in self.coupons.items():
            if coupon.get("code") == code:
                return coupon
        return None


    def add_cart(self, user_id: str, cart_data: Dict):
        self.carts[user_id] = cart_data
        self.save_data(self.carts_file, self.carts)

    def get_cart(self, user_id: str) -> Optional[Dict]:
        return self.carts.get(user_id)

    def remove_cart(self, user_id: str):
        if user_id in self.carts:
            del self.carts[user_id]
            self.save_data(self.carts_file, self.carts)

    def save_cart(self, user_id: str, cart: ShoppingCart):
        cart_data = {
            "items": [
                {"product_id": item.product.product_id, "quantity": item.quantity} for item in cart.items
            ]
        }
        self.add_cart(user_id, cart_data)

    def load_cart(self, user_id: str) -> Optional[ShoppingCart]:
        cart_data = self.get_cart(user_id)
        if cart_data:
            user = self.user_service.get_user(user_id)
            if not user:
                return None  # Return None if user does not exist
            cart = ShoppingCart(user)
            for item in cart_data["items"]:
                product = self.get_product(item["product_id"])
                if product:
                    cart.add_item(Product(
                        product_id=product["product_id"],
                        name=product["name"],
                        description=product["description"],
                        price=product["price"],
                        category_id=product["category_id"],
                        stock_quantity=product["stock_quantity"]
                    ), item["quantity"])
            return cart
        return None
    # Demo data initialization
    def initialize_demo_data(self):
        """Initialize the datastore with demo data"""
        # Check if files exist first
        files_exist = all(os.path.exists(file) for file in
                          [self.users_file, self.products_file, self.categories_file,
                           self.orders_file, self.coupons_file])

        if files_exist:
            print("Data files already exist. Loading existing data...")
            self.load_all_data()
            return

        print("Initializing demo data...")

        # Create demo categories
        self._create_demo_categories()

        # Create demo products
        self._create_demo_products()

        # Create demo users
        self._create_demo_users()

        # Create demo coupons
        self._create_demo_coupons()

        # Create demo orders
        self._create_demo_orders()

        # Save all data to files
        self.save_all_data()

        print("Demo data initialization complete.")

    def _create_demo_categories(self):
        """Create demo categories"""
        categories = [
            {"category_id": "cat1", "name": "Groceries", "description": "Food and household items"},
            {"category_id": "cat2", "name": "Electronics", "description": "Electronic devices and accessories"},
            {"category_id": "cat3", "name": "Personal Care", "description": "Health and beauty products"},
            {"category_id": "cat4", "name": "Home & Kitchen", "description": "Home appliances and kitchen supplies"},
            {"category_id": "cat5", "name": "Clothing", "description": "Fashion and apparel"}
        ]

        for category in categories:
            self.categories[category["category_id"]] = category

    def _create_demo_products(self):
        """Create demo products"""
        products = [
            # Groceries
            {"product_id": "p1", "name": "Milk", "description": "1 gallon whole milk",
             "price": 3.99, "category_id": "cat1", "stock_quantity": 100},
            {"product_id": "p2", "name": "Bread", "description": "Whole wheat bread loaf",
             "price": 2.49, "category_id": "cat1", "stock_quantity": 75},
            {"product_id": "p3", "name": "Eggs", "description": "Dozen large eggs",
             "price": 2.99, "category_id": "cat1", "stock_quantity": 50},

            # Electronics
            {"product_id": "p4", "name": "Headphones", "description": "Wireless bluetooth headphones",
             "price": 49.99, "category_id": "cat2", "stock_quantity": 20},
            {"product_id": "p5", "name": "USB Cable", "description": "6ft USB-C charging cable",
             "price": 12.99, "category_id": "cat2", "stock_quantity": 30},
            {"product_id": "p6", "name": "Power Bank", "description": "10000mAh portable charger",
             "price": 29.99, "category_id": "cat2", "stock_quantity": 15},
            {"product_id": "p10", "name": "Smart Speaker", "description": "Voice-controlled smart speaker",
             "price": 89.99, "category_id": "cat2", "stock_quantity": 12},
            {"product_id": "p11", "name": "Webcam", "description": "HD webcam for video calls",
             "price": 59.99, "category_id": "cat2", "stock_quantity": 18},
            {"product_id": "p12", "name": "Mouse", "description": "Wireless ergonomic computer mouse",
             "price": 24.99, "category_id": "cat2", "stock_quantity": 25},

            # Personal Care
            {"product_id": "p13", "name": "Shampoo", "description": "Daily moisturizing shampoo",
             "price": 5.99, "category_id": "cat3", "stock_quantity": 40},
            {"product_id": "p14", "name": "Toothpaste", "description": "Mint flavor toothpaste",
             "price": 3.49, "category_id": "cat3", "stock_quantity": 60},
            {"product_id": "p15", "name": "Soap", "description": "Pack of 4 bath soap bars",
             "price": 4.99, "category_id": "cat3", "stock_quantity": 45},
            {"product_id": "p16", "name": "Face Wash", "description": "Gentle cleansing face wash",
             "price": 7.99, "category_id": "cat3", "stock_quantity": 35},
            {"product_id": "p17", "name": "Hand Sanitizer", "description": "8oz antibacterial hand sanitizer",
             "price": 3.99, "category_id": "cat3", "stock_quantity": 70},
            {"product_id": "p18", "name": "Lotion", "description": "Daily moisturizing body lotion",
             "price": 6.99, "category_id": "cat3", "stock_quantity": 30},

            # Home & Kitchen
            {"product_id": "p19", "name": "Coffee Maker", "description": "12-cup programmable coffee maker",
             "price": 34.99, "category_id": "cat4", "stock_quantity": 15},
            {"product_id": "p20", "name": "Toaster", "description": "2-slice stainless steel toaster",
             "price": 24.99, "category_id": "cat4", "stock_quantity": 20},
            {"product_id": "p21", "name": "Blender", "description": "Countertop blender with multiple speeds",
             "price": 49.99, "category_id": "cat4", "stock_quantity": 12},
            {"product_id": "p22", "name": "Cutting Board", "description": "Bamboo cutting board set",
             "price": 19.99, "category_id": "cat4", "stock_quantity": 25},
            {"product_id": "p23", "name": "Cookware Set", "description": "10-piece non-stick cookware set",
             "price": 79.99, "category_id": "cat4", "stock_quantity": 10},
            {"product_id": "p24", "name": "Utensil Set", "description": "Kitchen utensil set with holder",
             "price": 15.99, "category_id": "cat4", "stock_quantity": 30},
              {"product_id": "p25", "name": "T-Shirt", "description": "Cotton crew neck t-shirt",
             "price": 14.99, "category_id": "cat5", "stock_quantity": 50},
            {"product_id": "p26", "name": "Jeans", "description": "Classic fit denim jeans",
             "price": 29.99, "category_id": "cat5", "stock_quantity": 35},
            {"product_id": "p27", "name": "Socks", "description": "Pack of 6 crew socks",
             "price": 12.99, "category_id": "cat5", "stock_quantity": 60},
            {"product_id": "p28", "name": "Sweater", "description": "Wool-blend pullover sweater",
             "price": 34.99, "category_id": "cat5", "stock_quantity": 25},
            {"product_id": "p29", "name": "Hat", "description": "Adjustable baseball cap",
             "price": 16.99, "category_id": "cat5", "stock_quantity": 40},
            {"product_id": "p30", "name": "Gloves", "description": "Touchscreen compatible winter gloves",
             "price": 14.99, "category_id": "cat5", "stock_quantity": 30}
        ]

        for product in products:
            self.products[product["product_id"]] = product

    def _create_demo_users(self):
        """Create demo users"""
        # Individual customer
        individual = {
            "user_id": "user1",
            "name": "John Doe",
            "email": "john@example.com",
            "address": "123 Main St, City",
            "phone": "555-1234",
            "type": "individual",
            "loyalty_points": 600
        }
        self.users[individual["user_id"]] = individual

        # Retail store
        retail = {
            "user_id": "store1",
            "name": "MyMart Store",
            "email": "contact@mymart.com",
            "address": "456 Commerce Blvd, City",
            "phone": "555-5678",
            "type": "retail",
            "business_license": "BIZ123456",
            "monthly_purchase_volume": 6000.0,
            "loyalty_points": 0
        }
        self.users[retail["user_id"]] = retail

    def _create_demo_coupons(self):
        """Create demo coupons"""
        # Current date
        now = datetime.datetime.now()

        # Create coupon that expires in 30 days
        expiry_date = now + datetime.timedelta(days=30)
        coupon1 = {
            "coupon_id": "coupon1",
            "code": "WELCOME10",
            "discount_amount": 10.0,
            "min_purchase_amount": 50.0,
            "expiry_date": expiry_date,
            "is_used": False
        }
        self.coupons[coupon1["coupon_id"]] = coupon1

        # Create coupon that expires in 15 days
        expiry_date = now + datetime.timedelta(days=15)
        coupon2 = {
            "coupon_id": "coupon2",
            "code": "SPRING25",
            "discount_amount": 25.0,
            "min_purchase_amount": 100.0,
            "expiry_date": expiry_date,
            "is_used": False
        }
        self.coupons[coupon2["coupon_id"]] = coupon2

    def _create_demo_orders(self):
        """Create demo orders"""
        # Get demo users
        individual = self.users["user1"]

        # Create an order for individual customer
        order_date = datetime.datetime.now() - datetime.timedelta(days=3)
        estimated_delivery = order_date + datetime.timedelta(days=3)

        order1 = {
            "order_id": "order1",
            "user_id": individual["user_id"],
            "order_date": order_date,
            "status": "delivered",
            "delivery_method": "standard",
            "delivery_address": individual["address"],
            "estimated_delivery_date": estimated_delivery,
            "discount_rate": 0.05,  # 5% discount
            "delivery_fee": 5.00,
            "items": [
                {
                    "product_id": "p1",
                    "name": "Milk",
                    "price": 3.99,
                    "quantity": 2,
                    "subtotal": 7.98
                },
                {
                    "product_id": "p2",
                    "name": "Bread",
                    "price": 2.49,
                    "quantity": 1,
                    "subtotal": 2.49
                }
            ],
            "total_amount": 15.47  # (7.98 + 2.49) * 0.95 + 5.00 delivery fee
        }
        self.orders[order1["order_id"]] = order1

        # Create another order for individual customer (in progress)
        order_date = datetime.datetime.now() - datetime.timedelta(days=1)
        estimated_delivery = order_date + datetime.timedelta(days=3)

        order2 = {
            "order_id": "order2",
            "user_id": individual["user_id"],
            "order_date": order_date,
            "status": "processing",
            "delivery_method": "standard",
            "delivery_address": individual["address"],
            "estimated_delivery_date": estimated_delivery,
            "discount_rate": 0.05,  # 5% discount
            "delivery_fee": 5.00,
            "items": [
                {
                    "product_id": "p4",
                    "name": "Headphones",
                    "price": 49.99,
                    "quantity": 1,
                    "subtotal": 49.99
                }
            ],
            "total_amount": 52.49  # 49.99 * 0.95 + 5.00 delivery fee
        }
        self.orders[order2["order_id"]] = order2


# ----- Service Classes -----

class UserService:
    def __init__(self, datastore: DataStore):
        self.datastore = datastore


    def create_individual_customer(self, name: str, email: str, address: str, phone: str) -> User:
        user_id = str(uuid.uuid4())
        user = IndividualCustomer(user_id, name, email, address, phone)
        user_data = vars(user)
        user_data["type"] = "individual"  # Ensure type field is set
        self.datastore.add_user(user_id, user_data)
        return user

    def create_retail_store(self, name: str, email: str, address: str, phone: str,
                           business_license: str, monthly_purchase_volume: float) -> User:
        user_id = str(uuid.uuid4())
        user = RetailStore(user_id, name, email, address, phone, business_license, monthly_purchase_volume)
        user_data = vars(user)
        user_data["type"] = "retail"  # Ensure type field is set
        self.datastore.add_user(user_id, user_data)
        return user

    def get_user(self, user_id: str) -> Optional[User]:
        user_data = self.datastore.get_user(user_id)
        if user_data:
            if "type" not in user_data:
                print(f"Warning: User {user_id} is missing 'type' field in data.")
                return None

            if user_data["type"] == "individual":
                return IndividualCustomer(
                    user_id=user_data["user_id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    address=user_data["address"],
                    phone=user_data["phone"]
                )
            else:
                return RetailStore(
                    user_id=user_data["user_id"],
                    name=user_data["name"],
                    email=user_data["email"],
                    address=user_data["address"],
                    phone=user_data["phone"],
                    business_license=user_data["business_license"],
                    monthly_purchase_volume=user_data["monthly_purchase_volume"]
                )
        return None

    def get_all_users(self) -> List[User]:
        return [self.get_user(user_id) for user_id in self.datastore.get_all_users()]

    def update_user(self, user: User) -> bool:
        if self.datastore.get_user(user.user_id):
            self.datastore.update_user(user.user_id, vars(user))
            return True
        return False


class ProductService:
    def __init__(self, datastore: DataStore):
        self.datastore = datastore

    def create_category(self, name: str, description: str) -> Category:
        category_id = str(uuid.uuid4())
        category = Category(category_id, name, description)
        self.datastore.add_category(category_id, vars(category))
        return category

    def create_product(self, name: str, description: str, price: float, category_id: str, stock_quantity: int) -> Product:
        product_id = str(uuid.uuid4())
        product = Product(product_id, name, description, price, category_id, stock_quantity)
        self.datastore.add_product(product_id, vars(product))
        return product

    def get_product(self, product_id: str) -> Optional[Product]:
        product_data = self.datastore.get_product(product_id)
        return Product(**product_data) if product_data else None

    def get_all_products(self) -> List[Product]:
        return [Product(**p) for p in self.datastore.get_all_products().values()]


    def get_products_by_category(self, category_id: str) -> List[Product]:
        products_data = self.datastore.find_products_by_category(category_id)
        return [
            Product(
                product_id=p["product_id"],
                name=p["name"],
                description=p["description"],
                price=p["price"],
                category_id=p["category_id"],
                stock_quantity=p["stock_quantity"]
            ) for p in products_data
        ]
    def get_category(self, category_id: str) -> Optional[Category]:
        category_data = self.datastore.get_category(category_id)
        return Category(**category_data) if category_data else None

    def get_all_categories(self) -> List[Category]:
        return [Category(**c) for c in self.datastore.get_all_categories().values()]

    def search_products(self, query: str) -> List[Product]:
        return [Product(**p) for p in self.datastore.search_products(query)]

    def update_product_stock(self, product_id: str, quantity_change: int) -> bool:
        product = self.get_product(product_id)
        if product:
            new_quantity = product.stock_quantity + quantity_change
            if new_quantity >= 0:
                product.stock_quantity = new_quantity
                self.datastore.update_product(product_id, vars(product))
                return True
        return False

class OrderService:
    def __init__(self, datastore: DataStore, product_service: ProductService, user_service: UserService):
        self.datastore = datastore
        self.product_service = product_service
        self.user_service = user_service

    def create_order(self, user_id: str, cart: ShoppingCart, delivery_method: str, delivery_address: str) -> Optional[Order]:
        print(f"Debug: Attempting to retrieve user {user_id} from DataStore...")
        user = self.user_service.get_user(user_id)
        if not user:
            print(f"Error: User {user_id} not found. Cannot proceed with checkout.")
            return None

        # Check stock availability
        for item in cart.items:
            product = self.product_service.get_product(item.product.product_id)
            if not product or product.stock_quantity < item.quantity:
                print(f"Error: Not enough stock for {item.product.name}. Available: {product.stock_quantity}, Requested: {item.quantity}")
                return None

        # Deduct stock after successful stock check
        for item in cart.items:
            self.product_service.update_product_stock(item.product.product_id, -item.quantity)

        # Create order
        order_id = str(uuid.uuid4())
        order = Order(order_id, user, cart.items, delivery_method, delivery_address)

        # Convert order to savable format
        order_data = {
            "order_id": order.order_id,
            "user_id": user_id,  # Store user_id instead of full user object
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": order.status,
            "delivery_method": order.delivery_method,
            "delivery_address": order.delivery_address,
            "estimated_delivery_date": order.estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S"),
            "discount_rate": order.discount_rate,
            "total_amount": order.total_amount,
            "items": [
                {
                    "product_id": item.product.product_id,
                    "name": item.product.name,
                    "price": item.product.price,
                    "quantity": item.quantity,
                    "subtotal": item.get_subtotal(order.discount_rate)
                } for item in cart.items
            ]
        }

        self.datastore.add_order(order_id, order_data)
        print(f"Success: Order {order_id} created for user {user_id}.")
        return order


    def get_order(self, order_id: str) -> Optional[Order]:
        order_data = self.datastore.get_order(order_id)
        if not order_data:
            return None

        # Retrieve the actual User object
        user = self.user_service.get_user(order_data["user_id"])
        if not user:
            print(f"Error: User {order_data['user_id']} not found.")
            return None

        # Convert order JSON data into Order object
        order = Order(
            order_id=order_data["order_id"],
            user=user,
            items=[
                CartItem(
                    Product(
                        product_id=item["product_id"],
                        name=item["name"],
                        description=item.get("description", ""),
                        price=item["price"],
                        category_id=item.get("category_id", ""),
                        stock_quantity=item.get("stock_quantity", 0)
                    ),
                    item["quantity"]
                ) for item in order_data["items"]
            ],
            delivery_method=order_data["delivery_method"],
            delivery_address=order_data["delivery_address"]
        )

        # Restore additional attributes
        order.order_date = datetime.datetime.strptime(order_data["order_date"], "%Y-%m-%d %H:%M:%S")
        order.status = order_data["status"]
        order.estimated_delivery_date = datetime.datetime.strptime(order_data["estimated_delivery_date"], "%Y-%m-%d %H:%M:%S")
        order.discount_rate = order_data["discount_rate"]
        order.total_amount = order_data["total_amount"]

        return order


    def get_user_orders(self, user_id: str) -> List[Order]:
        orders_data = self.datastore.find_orders_by_user(user_id)
        orders = []
        for order_data in orders_data:
            order = Order(
                order_id=order_data["order_id"],
                user=self.user_service.get_user(order_data["user_id"]),
                items=[
                    CartItem(
                        Product(
                            product_id=item["product_id"],
                            name=item["name"],
                            description=item.get("description", ""),
                            price=item["price"],
                            category_id=item.get("category_id", ""),
                            stock_quantity=item.get("stock_quantity", 0)
                        ),
                        item["quantity"]
                    ) for item in order_data["items"]
                ],
                delivery_method=order_data["delivery_method"],
                delivery_address=order_data["delivery_address"]
            )
            order.order_date = datetime.datetime.strptime(order_data["order_date"], "%Y-%m-%d %H:%M:%S")
            order.status = order_data["status"]
            order.estimated_delivery_date = datetime.datetime.strptime(order_data["estimated_delivery_date"], "%Y-%m-%d %H:%M:%S")
            order.discount_rate = order_data["discount_rate"]
            order.total_amount = order_data["total_amount"]
            orders.append(order)
        return orders
    def update_order_status(self, order_id: str, new_status: str) -> bool:
        order = self.get_order(order_id)
        if order:
            order.update_status(new_status)
            self.datastore.update_order(order_id, vars(order))
            return True
        return False

    def generate_coupon(self, user: User) -> Coupon:
        coupon_id = str(uuid.uuid4())
        code = f"DOLLMART{random.randint(1000, 9999)}"
        discount_amount = 50.0 if isinstance(user, RetailStore) else (25.0 if user.loyalty_points >= 1000 else 10.0)
        min_purchase = 500.0 if isinstance(user, RetailStore) else (100.0 if user.loyalty_points >= 1000 else 50.0)
        expiry_date = datetime.datetime.now() + datetime.timedelta(days=30)
        coupon = Coupon(coupon_id, code, discount_amount, min_purchase, expiry_date)
        self.datastore.add_coupon(coupon_id, vars(coupon))
        return coupon

    def apply_coupon(self, code: str, order_total: float) -> float:
        coupon_data = self.datastore.get_coupon_by_code(code)
        if coupon_data:
            # Extract only the required attributes for the Coupon constructor
            valid_keys = {"coupon_id", "code", "discount_amount", "min_purchase_amount", "expiry_date"}
            filtered_data = {key: coupon_data[key] for key in valid_keys if key in coupon_data}

            # Convert expiry_date back to datetime if it's a string
            if "expiry_date" in filtered_data and isinstance(filtered_data["expiry_date"], str):
                filtered_data["expiry_date"] = datetime.datetime.strptime(filtered_data["expiry_date"], "%Y-%m-%d %H:%M:%S")

            coupon = Coupon(**filtered_data)
            return coupon.apply(order_total) if coupon.is_valid(order_total) else 0.0
        return 0.0

    def mark_order_as_shipped(self, order_id: str) -> bool:
        order = self.get_order(order_id)
        if not order:
            print(f"Error: Order {order_id} not found.")
            return False

        if order.status != OrderStatus.CREATED:
            print(f"Cannot mark order {order_id} as shipped. Current status: {order.status}")
            return False

        order.status = OrderStatus.SHIPPED
        order_data = {
            "order_id": order.order_id,
            "user_id": order.user.user_id,
            "items": [
                {
                    "product_id": item.product.product_id,
                    "name": item.product.name,
                    "price": item.product.price,
                    "quantity": item.quantity
                }
                for item in order.items
            ],
            "delivery_method": order.delivery_method,
            "delivery_address": order.delivery_address,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": order.status,
            "estimated_delivery_date": order.estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S"),
            "discount_rate": order.discount_rate,
            "total_amount": order.total_amount,
        }

        try:
            self.datastore.update_order(order_id, order_data)
            print(f"Order {order_id} marked as shipped.")
            return True
        except Exception as e:
            print(f"Error saving data to orders.json: {e}")
            return False

    def mark_order_as_delivered(self, order_id: str) -> bool:
        order = self.get_order(order_id)
        if not order:
            print(f"Error: Order {order_id} not found.")
            return False

        if order.status not in [OrderStatus.SHIPPED, OrderStatus.PROCESSING,OrderStatus.CREATED]:
            print(f"Cannot mark order {order_id} as delivered. Current status: {order.status}")
            return False

        order.update_status(OrderStatus.DELIVERED)

        # Convert order to a serializable format before saving
        order_data = {
            "order_id": order.order_id,
            "user_id": order.user.user_id,  # Store only user_id instead of full object
            "items": [
                {
                    "product_id": item.product.product_id,
                    "name": item.product.name,
                    "price": item.product.price,
                    "quantity": item.quantity
                }
                for item in order.items
            ],
            "delivery_method": order.delivery_method,
            "delivery_address": order.delivery_address,
            "order_date": order.order_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": order.status,
            "estimated_delivery_date": order.estimated_delivery_date.strftime("%Y-%m-%d %H:%M:%S"),
            "discount_rate": order.discount_rate,
            "total_amount": order.total_amount,
        }

        try:
            self.datastore.update_order(order_id, order_data)
            print(f"Order {order_id} marked as delivered.")
            return True
        except Exception as e:
            print(f"Error saving data to orders.json: {e}")
            return False

# ----- CLI Application -----

class DollmartEMarket:
    def __init__(self):
        self.datastore = DataStore()
        self.user_service = UserService(self.datastore)
        self.product_service = ProductService(self.datastore)
        self.order_service = OrderService(self.datastore, self.product_service, self.user_service)
        self.current_user = None
        self.shopping_cart = None

    def login(self, user_id: str) -> bool:
        user = self.user_service.get_user(user_id)
        if user:
            self.current_user = user
            saved_cart = self.datastore.get_cart(user_id)
            self.shopping_cart = ShoppingCart(user,self.datastore)
            if saved_cart:
                for item in saved_cart["items"]:
                    product = self.product_service.get_product(item["product_id"])
                    if product:
                        self.shopping_cart.add_item(product, item["quantity"])
            return True
        return False

    def register_individual(self, name: str, email: str, address: str, phone: str) -> User:
        user = self.user_service.create_individual_customer(name, email, address, phone)
        self.current_user = user
        self.shopping_cart = ShoppingCart(user,self.datastore)
        return user

    def register_retail_store(self, name: str, email: str, address: str, phone: str,
                           business_license: str, monthly_purchase_volume: float) -> User:
        user = self.user_service.create_retail_store(name, email, address, phone,
                                                   business_license, monthly_purchase_volume)
        self.current_user = user
        self.shopping_cart = ShoppingCart(user,self.datastore)
        return user

    def browse_categories(self) -> List[Category]:
        return self.product_service.get_all_categories()

    def browse_products_by_category(self, category_id: str) -> List[Product]:
        return self.product_service.get_products_by_category(category_id)

    def search_products(self, query: str) -> List[Product]:
        return self.product_service.search_products(query)

    def add_to_cart(self, product_id: str, quantity: int) -> bool:
        if not self.current_user or not self.shopping_cart:
            return False

        product = self.product_service.get_product(product_id)
        if not product or product.stock_quantity < quantity:
            return False

        self.shopping_cart.add_item(product, quantity)
        return True

    def view_cart(self) -> Dict:
        if not self.current_user or not self.shopping_cart:
            return {"items": [], "total": 0.0}

        items = []
        for item in self.shopping_cart.items:
            items.append({
                "product_id": item.product.product_id,
                "name": item.product.name,
                "price": item.product.price,
                "quantity": item.quantity,
                "subtotal": item.get_subtotal(self.current_user.get_discount_rate())
            })

        return {
            "items": items,
            "total": self.shopping_cart.get_total(),
            "discount_rate": self.current_user.get_discount_rate()
        }

    def update_cart_item(self, product_id: str, quantity: int) -> bool:
        if not self.current_user or not self.shopping_cart:
            return False

        product = self.product_service.get_product(product_id)
        if not product or (quantity > 0 and product.stock_quantity < quantity):
            return False

        self.shopping_cart.update_quantity(product_id, quantity)
        return True

    def remove_from_cart(self, product_id: str) -> bool:
        if not self.current_user or not self.shopping_cart:
            return False

        self.shopping_cart.remove_item(product_id)
        return True

    def checkout(self, delivery_method: str, delivery_address: str, coupon_code: str = None) -> Dict:
        if not self.current_user or not self.shopping_cart or not self.shopping_cart.items:
            return {"success": False, "message": "Cart is empty or user not logged in"}

        # Calculate initial total
        total = self.shopping_cart.get_total()

        # Apply coupon if provided
        discount = 0.0
        if coupon_code:
            discount = self.order_service.apply_coupon(coupon_code, total)
            total -= discount

        # Ensure correct user_id is passed, not the full object
        print(f"Debug: Passing user_id {self.current_user.user_id} to create_order()")
        order = self.order_service.create_order(
            self.current_user.user_id,  # FIXED: Pass user_id instead of whole user object
            self.shopping_cart,
            delivery_method,
            delivery_address
        )

        if not order:
            return {"success": False, "message": "Failed to create order. Check stock availability."}

        # Save cart after checkout
        self.datastore.remove_cart(self.current_user.user_id)

        # Generate a new coupon for the customer if eligible
        if self.current_user.loyalty_points >= 500:
            coupon = self.order_service.generate_coupon(self.current_user)
            coupon_info = {
                "code": coupon.code,
                "discount_amount": coupon.discount_amount,
                "min_purchase": coupon.min_purchase_amount,
                "expiry_date": coupon.expiry_date.strftime("%Y-%m-%d")
            }
        else:
            coupon_info = None

        return {
            "success": True,
            "order_id": order.order_id,
            "total": order.total_amount,
            "discount_applied": discount,
            "delivery_method": order.delivery_method,
            "estimated_delivery": order.estimated_delivery_date.strftime("%Y-%m-%d"),
            "new_coupon": coupon_info
        }



    def view_orders(self) -> List[Dict]:
        if not self.current_user:
            return []

        orders = self.order_service.get_user_orders(self.current_user.user_id)
        result = []

        for order in orders:
            order_details = {
                "order_id": order.order_id,
                "date": order.order_date.strftime("%Y-%m-%d %H:%M"),
                "status": order.status,
                "total": order.total_amount,
                "delivery_method": order.delivery_method,
                "estimated_delivery": order.estimated_delivery_date.strftime("%Y-%m-%d"),
                "items": []
            }

            for item in order.items:
                order_details["items"].append({
                    "product_id": item.product.product_id,
                    "name": item.product.name,
                    "quantity": item.quantity,
                    "subtotal": item.get_subtotal(order.discount_rate)
                })

            result.append(order_details)

        return result

    def get_loyalty_status(self) -> Dict:
        if not self.current_user:
            return {"points": 0, "discount_rate": 0.0}

        return {
            "points": self.current_user.loyalty_points,
            "discount_rate": self.current_user.get_discount_rate() * 100  # Convert to percentage
        }
    def view_delivery_status(self, order_id: str) -> Optional[str]:
        order = self.order_service.get_order(order_id)
        if order and order.user.user_id == self.current_user.user_id:
            return order.get_delivery_status()
        return None

    def update_delivery_status(self, order_id: str, new_status: str) -> bool:
        # Only Dollmart can update delivery status
        if isinstance(self.current_user, RetailStore) and self.current_user.name == "Dollmart":
            if new_status == OrderStatus.SHIPPED:
                return self.order_service.mark_order_as_shipped(order_id)
            elif new_status == OrderStatus.DELIVERED:
                return self.order_service.mark_order_as_delivered(order_id)
        return False


# ----- CLI Interface -----

def main():
    """Main CLI interface for Dollmart E-Market"""
    app = DollmartEMarket()

    while True:
        if app.current_user is None:
            print("\n===== DOLLMART E-MARKET =====")
            print("1. Login")
            print("2. Register as Individual Customer")
            print("3. Register as Retail Store")
            print("0. Exit")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                user_id = input("Enter User ID: ")
                if app.login(user_id):
                    print(f"Welcome back, {app.current_user.name}!")
                else:
                    print("Login failed. User not found.")

            elif choice == "2":
                print("\n--- Register as Individual Customer ---")
                name = input("Name: ")
                email = input("Email: ")
                address = input("Address: ")
                phone = input("Phone: ")

                user = app.register_individual(name, email, address, phone)
                print(f"Registration successful! Your User ID is {user.user_id}")

            elif choice == "3":
                print("\n--- Register as Retail Store ---")
                name = input("Business Name: ")
                email = input("Email: ")
                address = input("Address: ")
                phone = input("Phone: ")
                license_num = input("Business License Number: ")

                try:
                    volume = float(input("Monthly Purchase Volume ($): "))
                    user = app.register_retail_store(name, email, address, phone, license_num, volume)
                    print(f"Registration successful! Your User ID is {user.user_id}")
                except ValueError:
                    print("Invalid amount. Please enter a valid number.")

            elif choice == "0":
                print("Thank you for visiting Dollmart E-Market!")
                break

            else:
                print("Invalid choice. Please try again.")

        else:
               # User is logged in
            print(f"\n===== DOLLMART E-MARKET ({app.current_user.name}) =====")
            print("1. Browse Categories")
            print("2. Search Products")
            print("3. View Cart")
            print("4. Checkout")
            print("5. View My Orders")
            print("6. View Delivery Status")
            print("7. Update Delivery Status (Admin Only)")
            print("8. View Loyalty Status")
            print("9. Logout")
            print("0. Exit")

            choice = input("\nEnter your choice: ")

            if choice == "1":
                # Browse categories
                categories = app.browse_categories()

                print("\n--- Product Categories ---")
                for category in categories:
                    print(f"{category.category_id}: {category.name} - {category.description}")

                cat_id = input("\nEnter Category ID to browse products (or press Enter to go back): ")
                if cat_id:
                    products = app.browse_products_by_category(cat_id)

                    if not products:
                        print("No products found in this category.")
                    else:
                        print("\n--- Products ---")
                        for product in products:
                            print(f"{product.product_id}: {product.name} - ${product.price:.2f} ({product.stock_quantity} in stock)")
                            print(f"   {product.description}")

                        # Allow adding products to cart
                        prod_id = input("\nEnter Product ID to add to cart (or press Enter to go back): ")
                        if prod_id:
                            try:
                                quantity = int(input("Enter quantity: "))
                                if app.add_to_cart(prod_id, quantity):
                                    print(f"Added {quantity} item(s) to cart.")
                                else:
                                    print("Failed to add to cart. Check product ID and stock availability.")
                            except ValueError:
                                print("Invalid quantity. Please enter a number.")

            elif choice == "2":
                # Search products
                query = input("Enter search term: ")
                products = app.search_products(query)

                if not products:
                    print("No products found matching your search.")
                else:
                    print(f"\n--- Search Results for '{query}' ---")
                    for product in products:
                        print(f"{product.product_id}: {product.name} - ${product.price:.2f} ({product.stock_quantity} in stock)")
                        print(f"   {product.description}")

                    # Allow adding products to cart
                    prod_id = input("\nEnter Product ID to add to cart (or press Enter to go back): ")
                    if prod_id:
                        try:
                            quantity = int(input("Enter quantity: "))
                            if app.add_to_cart(prod_id, quantity):
                                print(f"Added {quantity} item(s) to cart.")
                            else:
                                print("Failed to add to cart. Check product ID and stock availability.")
                        except ValueError:
                            print("Invalid quantity. Please enter a number.")

            elif choice == "3":
                # View cart
                cart = app.view_cart()

                if not cart["items"]:
                    print("Your cart is empty.")
                else:
                    print("\n--- Your Shopping Cart ---")
                    for item in cart["items"]:
                        print(f"{item['product_id']}: {item['name']} - ${item['price']:.2f} x {item['quantity']} = ${item['subtotal']:.2f}")

                    if cart["discount_rate"] > 0:
                        print(f"\nDiscount Applied: {cart['discount_rate'] * 100:.1f}%")

                    print(f"\nTotal: ${cart['total']:.2f}")

                    # Cart management
                    print("\n1. Update item quantity")
                    print("2. Remove item")
                    print("3. Go back")

                    cart_choice = input("\nEnter your choice: ")

                    if cart_choice == "1":
                        prod_id = input("Enter Product ID to update: ")
                        try:
                            quantity = int(input("Enter new quantity: "))
                            if app.update_cart_item(prod_id, quantity):
                                print("Cart updated.")
                            else:
                                print("Failed to update cart. Check product ID and stock availability.")
                        except ValueError:
                            print("Invalid quantity. Please enter a number.")

                    elif cart_choice == "2":
                        prod_id = input("Enter Product ID to remove: ")
                        if app.remove_from_cart(prod_id):
                            print("Item removed from cart.")
                        else:
                            print("Failed to remove item. Check product ID.")

            elif choice == "4":
                # Checkout
                cart = app.view_cart()

                if not cart["items"]:
                    print("Your cart is empty. Add items before checkout.")
                else:
                    print("\n--- Checkout ---")

                    # Display cart summary
                    print("\n--- Your Shopping Cart ---")
                    for item in cart["items"]:
                        print(f"{item['name']} - ${item['price']:.2f} x {item['quantity']} = ${item['subtotal']:.2f}")

                    print(f"\nSubtotal: ${cart['total']:.2f}")

                    # Delivery method
                    print("\nSelect delivery method:")
                    print("1. Standard Delivery ($5.00, 3 days)")
                    print("2. Express Delivery ($15.00, 1 day)")
                    print("3. Store Pickup (Free, 2 hours)")

                    delivery_choice = input("\nEnter your choice: ")

                    if delivery_choice == "1":
                        delivery_method = DeliveryMethod.STANDARD
                    elif delivery_choice == "2":
                        delivery_method = DeliveryMethod.EXPRESS
                    elif delivery_choice == "3":
                        delivery_method = DeliveryMethod.STORE_PICKUP
                    else:
                        print("Invalid choice. Defaulting to Standard Delivery.")
                        delivery_method = DeliveryMethod.STANDARD

                    # Delivery address
                    if delivery_method != DeliveryMethod.STORE_PICKUP:
                        use_default = input(f"Use default address ({app.current_user.address})? (y/n): ").lower()
                        if use_default == "y" or use_default == "yes":
                            delivery_address = app.current_user.address
                        else:
                            delivery_address = input("Enter delivery address: ")
                    else:
                        delivery_address = "Store Pickup"

                    # Coupon code
                    coupon_code = input("Enter coupon code (or press Enter to skip): ")

                    # Process checkout
                    result = app.checkout(delivery_method, delivery_address, coupon_code)

                    if result["success"]:
                        print("\n=== Order Confirmation ===")
                        print(f"Order ID: {result['order_id']}")
                        print(f"Total: ${result['total']:.2f}")

                        if result["discount_applied"] > 0:
                            print(f"Discount Applied: ${result['discount_applied']:.2f}")

                        print(f"Delivery Method: {result['delivery_method']}")
                        print(f"Estimated Delivery: {result['estimated_delivery']}")

                        if result["new_coupon"]:
                            print("\n=== New Coupon Generated! ===")
                            print(f"Code: {result['new_coupon']['code']}")
                            print(f"Discount: ${result['new_coupon']['discount_amount']:.2f}")
                            print(f"Minimum Purchase: ${result['new_coupon']['min_purchase']:.2f}")
                            print(f"Expires: {result['new_coupon']['expiry_date']}")

                        print("\nThank you for your order!")
                    else:
                        print(f"Checkout failed: {result['message']}")

            elif choice == "5":
                # View orders
                orders = app.view_orders()

                if not orders:
                    print("You have no orders.")
                else:
                    print("\n--- Your Orders ---")
                    for order in orders:
                        print(f"\nOrder ID: {order['order_id']}")
                        print(f"Date: {order['date']}")
                        print(f"Status: {order['status']}")
                        print(f"Total: ${order['total']:.2f}")
                        print(f"Delivery Method: {order['delivery_method']}")
                        print(f"Estimated Delivery: {order['estimated_delivery']}")

                        print("\nItems:")
                        for item in order['items']:
                            print(f"- {item['name']} x {item['quantity']} = ${item['subtotal']:.2f}")
            elif choice =="6":
                 # View delivery status
                order_id = input("Enter Order ID: ")
                status = app.view_delivery_status(order_id)
                if status:
                    print(f"\nDelivery Status for Order {order_id}: {status}")
                else:
                    print("Order not found or you do not have permission to view this order.")
            elif choice == "7":
                 # Update delivery status (Admin Only)
                if isinstance(app.current_user, RetailStore):
                    order_id = input("Enter Order ID: ")
                    print("1. Mark as Shipped")
                    print("2. Mark as Delivered")
                    status_choice = input("Enter your choice: ")
                    if status_choice == "1":
                        if app.update_delivery_status(order_id, OrderStatus.SHIPPED):
                            print(f"Order {order_id} marked as shipped.")
                        else:
                            print("Failed to update status.")
                    elif status_choice == "2":
                        if app.update_delivery_status(order_id, OrderStatus.DELIVERED):
                            print(f"Order {order_id} marked as delivered.")
                        else:
                            print("Failed to update status.")
                    else:
                        print("Invalid choice.")
                else:
                    print("You do not have permission to update delivery status.")


            elif choice == "8":
                # View loyalty status
                loyalty = app.get_loyalty_status()
                print("\n--- Your Loyalty Status ---")
                print(f"Points: {loyalty['points']}")
                print(f"Current Discount Rate: {loyalty['discount_rate']:.1f}%")

                # Show progress to next tier for individual customers
                if isinstance(app.current_user, IndividualCustomer):
                    if loyalty['points'] < 500:
                        points_needed = 500 - loyalty['points']
                        print(f"\nEarn {points_needed} more points to reach Silver tier (5% discount)")
                    elif loyalty['points'] < 1000:
                        points_needed = 1000 - loyalty['points']
                        print(f"\nEarn {points_needed} more points to reach Gold tier (10% discount)")
                    else:
                        print("\nCongratulations! You've reached Gold tier status!")

            elif choice == "9":
                # Logout
                app.current_user = None
                app.shopping_cart = None
                print("Logged out successfully.")

            elif choice == "0":
                print("Thank you for visiting Dollmart E-Market!")
                break

            else:
                print("Invalid choice. Please try again.")


if __name__ == "__main__":
    main()