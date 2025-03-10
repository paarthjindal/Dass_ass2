import json
import os
import uuid
import datetime
import re
from typing import List, Dict, Any, Optional, Union


class DataStore:
    """
    DataStore class for persisting data in JSON format.
    Handles creating, reading, updating, and deleting data.
    """
    def __init__(self, data_dir: str = "data"):
        """
        Initialize the DataStore with a directory for data files.

        Args:
            data_dir: Directory to store JSON files
        """
        self.data_dir = data_dir
        # Create the data directory if it doesn't exist
        if not os.path.exists(data_dir):
            os.makedirs(data_dir)

    def _get_file_path(self, entity_type: str) -> str:
        """
        Get the file path for a specific entity type.

        Args:
            entity_type: Type of entity (e.g., 'users', 'products')

        Returns:
            Path to the JSON file
        """
        return os.path.join(self.data_dir, f"{entity_type}.json")

    def load_data(self, entity_type: str) -> List[Dict]:
        """
        Load data from a JSON file.

        Args:
            entity_type: Type of entity to load

        Returns:
            List of dictionaries containing entity data
        """
        file_path = self._get_file_path(entity_type)
        if not os.path.exists(file_path):
            return []
        try:
            with open(file_path, 'r') as file:
                return json.load(file)
        except json.JSONDecodeError:
            # Return empty list if file is empty or invalid
            return []

    def save_data(self, entity_type: str, data: List[Dict]) -> bool:
        """
        Save data to a JSON file.

        Args:
            entity_type: Type of entity to save
            data: List of dictionaries containing entity data

        Returns:
            True if successful, False otherwise
        """
        file_path = self._get_file_path(entity_type)
        try:
            with open(file_path, 'w') as file:
                json.dump(data, file, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False

    def create_entity(self, entity_type: str, entity_data: Dict) -> Dict:
        """
        Create a new entity in the datastore.

        Args:
            entity_type: Type of entity to create
            entity_data: Dictionary containing entity data

        Returns:
            Created entity with generated ID
        """
        # Load existing data
        entities = self.load_data(entity_type)

        # Generate a unique ID if not provided
        if 'id' not in entity_data:
            entity_data['id'] = str(uuid.uuid4())

        # Add created_at timestamp
        entity_data['created_at'] = datetime.datetime.now().isoformat()

        # Add to entities and save
        entities.append(entity_data)
        self.save_data(entity_type, entities)

        return entity_data

    def get_entity_by_id(self, entity_type: str, entity_id: str) -> Optional[Dict]:
        """
        Get an entity by ID.

        Args:
            entity_type: Type of entity to get
            entity_id: ID of the entity

        Returns:
            Entity dictionary or None if not found
        """
        entities = self.load_data(entity_type)
        for entity in entities:
            if entity.get('id') == entity_id:
                return entity
        return None

    def update_entity(self, entity_type: str, entity_id: str, updated_data: Dict) -> Optional[Dict]:
        """
        Update an entity by ID.

        Args:
            entity_type: Type of entity to update
            entity_id: ID of the entity
            updated_data: New data to update

        Returns:
            Updated entity or None if not found
        """
        entities = self.load_data(entity_type)
        for i, entity in enumerate(entities):
            if entity.get('id') == entity_id:
                # Add updated_at timestamp
                updated_data['updated_at'] = datetime.datetime.now().isoformat()
                # Preserve ID and created_at
                updated_data['id'] = entity_id
                if 'created_at' in entity:
                    updated_data['created_at'] = entity['created_at']
                # Update entity
                entities[i] = {**entity, **updated_data}
                self.save_data(entity_type, entities)
                return entities[i]
        return None

    def delete_entity(self, entity_type: str, entity_id: str) -> bool:
        """
        Delete an entity by ID.

        Args:
            entity_type: Type of entity to delete
            entity_id: ID of the entity

        Returns:
            True if deleted, False if not found
        """
        entities = self.load_data(entity_type)
        for i, entity in enumerate(entities):
            if entity.get('id') == entity_id:
                del entities[i]
                self.save_data(entity_type, entities)
                return True
        return False

    def query_entities(self, entity_type: str, query: Dict) -> List[Dict]:
        """
        Query entities based on field values.

        Args:
            entity_type: Type of entity to query
            query: Dictionary of field-value pairs to match

        Returns:
            List of matching entities
        """
        entities = self.load_data(entity_type)
        results = []

        for entity in entities:
            match = True
            for key, value in query.items():
                if key not in entity or entity[key] != value:
                    match = False
                    break
            if match:
                results.append(entity)

        return results


class User:
    """
    Base User class for system users.
    """
    def __init__(self, username: str, password: str, email: str, name: str):
        """
        Initialize a user.

        Args:
            username: Unique username
            password: User password (should be hashed in production)
            email: User email address
            name: User's full name
        """
        self.username = username
        self.password = password  # In production, this should be hashed
        self.email = email
        self.name = name
        self.id = None  # Will be set when saved to DataStore
        self.created_at = None

    def to_dict(self) -> Dict:
        """
        Convert user to dictionary for storage.

        Returns:
            Dictionary representation of user
        """
        return {
            'username': self.username,
            'password': self.password,
            'email': self.email,
            'name': self.name,
            'type': 'user'
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'User':
        """
        Create a User from dictionary data.

        Args:
            data: Dictionary containing user data

        Returns:
            User object
        """
        user = cls(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            name=data['name']
        )
        user.id = data.get('id')
        user.created_at = data.get('created_at')
        return user


class Customer(User):
    """
    Customer class for individual customers.
    """
    def __init__(self, username: str, password: str, email: str, name: str,
                 address: str, phone: str):
        """
        Initialize a customer.

        Args:
            username: Unique username
            password: User password
            email: User email address
            name: User's full name
            address: Customer's shipping address
            phone: Customer's phone number
        """
        super().__init__(username, password, email, name)
        self.address = address
        self.phone = phone
        self.loyalty_points = 0
        self.orders = []

    def to_dict(self) -> Dict:
        """
        Convert customer to dictionary for storage.

        Returns:
            Dictionary representation of customer
        """
        data = super().to_dict()
        data.update({
            'address': self.address,
            'phone': self.phone,
            'loyalty_points': self.loyalty_points,
            'orders': self.orders,
            'type': 'customer'
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Customer':
        """
        Create a Customer from dictionary data.

        Args:
            data: Dictionary containing customer data

        Returns:
            Customer object
        """
        customer = cls(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            name=data['name'],
            address=data['address'],
            phone=data['phone']
        )
        customer.id = data.get('id')
        customer.created_at = data.get('created_at')
        customer.loyalty_points = data.get('loyalty_points', 0)
        customer.orders = data.get('orders', [])
        return customer

    def add_loyalty_points(self, points: int):
        """
        Add loyalty points to customer account.

        Args:
            points: Number of points to add
        """
        self.loyalty_points += points


class RetailStore(User):
    """
    RetailStore class for bulk-ordering retail stores.
    """
    def __init__(self, username: str, password: str, email: str, name: str,
                business_address: str, phone: str, tax_id: str):
        """
        Initialize a retail store.

        Args:
            username: Unique username
            password: User password
            email: User email address
            name: Business name
            business_address: Business address
            phone: Business phone number
            tax_id: Business tax ID
        """
        super().__init__(username, password, email, name)
        self.business_address = business_address
        self.phone = phone
        self.tax_id = tax_id
        self.bulk_discount_rate = 0.05  # Default 5% discount
        self.orders = []

    def to_dict(self) -> Dict:
        """
        Convert retail store to dictionary for storage.

        Returns:
            Dictionary representation of retail store
        """
        data = super().to_dict()
        data.update({
            'business_address': self.business_address,
            'phone': self.phone,
            'tax_id': self.tax_id,
            'bulk_discount_rate': self.bulk_discount_rate,
            'orders': self.orders,
            'type': 'retail_store'
        })
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'RetailStore':
        """
        Create a RetailStore from dictionary data.

        Args:
            data: Dictionary containing retail store data

        Returns:
            RetailStore object
        """
        store = cls(
            username=data['username'],
            password=data['password'],
            email=data['email'],
            name=data['name'],
            business_address=data['business_address'],
            phone=data['phone'],
            tax_id=data['tax_id']
        )
        store.id = data.get('id')
        store.created_at = data.get('created_at')
        store.bulk_discount_rate = data.get('bulk_discount_rate', 0.05)
        store.orders = data.get('orders', [])
        return store


class Category:
    """
    Category class for organizing products hierarchically.
    """
    def __init__(self, name: str, description: str, parent_id: Optional[str] = None):
        """
        Initialize a category.

        Args:
            name: Category name
            description: Category description
            parent_id: ID of parent category (None for top-level categories)
        """
        self.name = name
        self.description = description
        self.parent_id = parent_id
        self.id = None  # Will be set when saved to DataStore

    def to_dict(self) -> Dict:
        """
        Convert category to dictionary for storage.

        Returns:
            Dictionary representation of category
        """
        return {
            'name': self.name,
            'description': self.description,
            'parent_id': self.parent_id
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Category':
        """
        Create a Category from dictionary data.

        Args:
            data: Dictionary containing category data

        Returns:
            Category object
        """
        category = cls(
            name=data['name'],
            description=data['description'],
            parent_id=data.get('parent_id')
        )
        category.id = data.get('id')
        return category


class Product:
    """
    Product class for items sold in the store.
    """
    def __init__(self, name: str, description: str, category_id: str,
                 base_price: float, inventory_count: int,
                 attributes: Optional[Dict] = None):
        """
        Initialize a product.

        Args:
            name: Product name
            description: Product description
            category_id: ID of the category this product belongs to
            base_price: Base price of the product
            inventory_count: Current inventory count
            attributes: Additional product attributes (color, size, etc.)
        """
        self.name = name
        self.description = description
        self.category_id = category_id
        self.base_price = base_price
        self.inventory_count = inventory_count
        self.attributes = attributes or {}
        self.id = None  # Will be set when saved to DataStore

    def to_dict(self) -> Dict:
        """
        Convert product to dictionary for storage.

        Returns:
            Dictionary representation of product
        """
        return {
            'name': self.name,
            'description': self.description,
            'category_id': self.category_id,
            'base_price': self.base_price,
            'inventory_count': self.inventory_count,
            'attributes': self.attributes
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'Product':
        """
        Create a Product from dictionary data.

        Args:
            data: Dictionary containing product data

        Returns:
            Product object
        """
        product = cls(
            name=data['name'],
            description=data['description'],
            category_id=data['category_id'],
            base_price=data['base_price'],
            inventory_count=data['inventory_count'],
            attributes=data.get('attributes', {})
        )
        product.id = data.get('id')
        return product

    def update_inventory(self, quantity: int) -> bool:
        """
        Update inventory count.

        Args:
            quantity: Change in inventory (positive for increase, negative for decrease)

        Returns:
            True if update successful, False if insufficient inventory
        """
        new_count = self.inventory_count + quantity
        if new_count < 0:
            return False
        self.inventory_count = new_count
        return True


class CartItem:
    """
    CartItem class for items in a shopping cart.
    """
    def __init__(self, product_id: str, quantity: int, unit_price: float):
        """
        Initialize a cart item.

        Args:
            product_id: ID of the product
            quantity: Quantity of the product
            unit_price: Price per unit at time of adding to cart
        """
        self.product_id = product_id
        self.quantity