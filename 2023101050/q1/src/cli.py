import os
import json
import datetime
import uuid
import time
from enum import Enum
from typing import List, Dict, Optional, Any
import random
import fcntl

# ===== ENUMS =====
class OrderStatus(Enum):
    PLACED = "Placed"
    PREPARING = "Preparing"
    READY = "Ready for Pickup/Delivery"
    IN_TRANSIT = "In Transit"
    DELIVERED = "Delivered"
    PICKED_UP = "Picked Up"
    CANCELLED = "Cancelled"

class OrderType(Enum):
    DELIVERY = "Home Delivery"
    TAKEAWAY = "Takeaway"

class UserRole(Enum):
    CUSTOMER = "Customer"
    RESTAURANT = "Restaurant Staff"
    DELIVERY_AGENT = "Delivery Agent"
    MANAGER = "Manager"

# ===== MODELS =====
class User:
    def __init__(self, user_id: str, name: str, email: str, role: UserRole):
        self.user_id = user_id
        self.name = name
        self.email = email
        self.role = role

    def to_dict(self):
        return {
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "role": self.role.value
        }

class Customer(User):
    def __init__(self, user_id: str, name: str, email: str, address: str):
        super().__init__(user_id, name, email, UserRole.CUSTOMER)
        self.address = address
        self.order_history = []

    def to_dict(self):
        data = super().to_dict()
        data.update({"address": self.address, "order_history": self.order_history})
        return data

class DeliveryAgent(User):
    def __init__(self, user_id: str, name: str, email: str):
        super().__init__(user_id, name, email, UserRole.DELIVERY_AGENT)
        self.available = True
        self.current_order = None
        self.completed_deliveries = []

    def to_dict(self):
        data = super().to_dict()
        data.update({
            "available": self.available,
            "current_order": self.current_order,
            "completed_deliveries": self.completed_deliveries
        })
        return data

# i am not sure of the code that i have written below
class DeliveryAgentProfile:
    """Enhanced profile for delivery agents with more details"""
    def __init__(self, agent: DeliveryAgent):
        self.agent = agent
        self.performance_metrics = {
            "total_deliveries": len(agent.completed_deliveries),
            "on_time_deliveries": 0,  # To be implemented
            "average_delivery_time": 0.0,  # To be calculated
            "rating": 4.5  # Default rating
        }
        self.duty_status = agent.available
        self.working_hours = {
            "start_time": None,
            "end_time": None,
            "total_hours": 0.0
        }

    def update_performance(self, new_delivery):
        """Update performance metrics after each delivery"""
        # Logic to calculate performance metrics
        self.performance_metrics['total_deliveries'] += 1

    def toggle_duty_status(self):
        """Toggle the duty status of the delivery agent"""
        self.agent.available = not self.agent.available
        self.duty_status = self.agent.available

        # Log working hours when changing status
        current_time = datetime.datetime.now()
        if self.duty_status:  # Going on duty
            self.working_hours['start_time'] = current_time
        else:  # Going off duty
            if self.working_hours['start_time']:
                duration = (current_time - self.working_hours['start_time']).total_seconds() / 3600
                self.working_hours['end_time'] = current_time
                self.working_hours['total_hours'] += duration

    def to_dict(self):
        """Convert profile to dictionary for serialization"""
        return {
            "name": self.agent.name,
            "email": self.agent.email,
            "performance_metrics": self.performance_metrics,
            "duty_status": self.duty_status,
            "working_hours": {
                "start_time": self.working_hours['start_time'].isoformat() if self.working_hours['start_time'] else None,
                "end_time": self.working_hours['end_time'].isoformat() if self.working_hours['end_time'] else None,
                "total_hours": self.working_hours['total_hours']
            }
        }



class MenuItem:
    def __init__(self, item_id: str, name: str, description: str, price: float, prep_time: int):
        self.item_id = item_id
        self.name = name
        self.description = description
        self.price = price
        self.prep_time = prep_time  # in minutes

    def to_dict(self):
        return {
            "item_id": self.item_id,
            "name": self.name,
            "description": self.description,
            "price": self.price,
            "prep_time": self.prep_time
        }

class Restaurant:
    def __init__(self, restaurant_id: str, name: str, address: str):
        self.restaurant_id = restaurant_id
        self.name = name
        self.address = address
        self.menu_items = {}
        self.orders = []

    def add_menu_item(self, item):
        self.menu_items[item.item_id] = item

    def to_dict(self):
        return {
            "restaurant_id": self.restaurant_id,
            "name": self.name,
            "address": self.address,
            "menu_items": {k: v.to_dict() for k, v in self.menu_items.items()},
            "orders": self.orders
        }

class OrderItem:
    def __init__(self, menu_item: MenuItem, quantity: int):
        self.menu_item = menu_item
        self.quantity = quantity

    def get_total_price(self):
        return self.menu_item.price * self.quantity

class Order:
    def __init__(self, order_id: str, customer_id: str, restaurant_id: str,
                 items: List[OrderItem], order_type: OrderType):
        self.order_id = order_id
        self.customer_id = customer_id
        self.restaurant_id = restaurant_id
        self.items = items
        self.order_type = order_type
        self.status = OrderStatus.PLACED
        self.delivery_agent_id = None
        self.placed_time = datetime.datetime.now()

        # Calculate preparation time based on items
        prep_time = max([item.menu_item.prep_time for item in items])
        self.estimated_ready_time = self.placed_time + datetime.timedelta(minutes=prep_time)

        # For delivery orders, add estimated delivery time
        if order_type == OrderType.DELIVERY:
            # Assuming 15 minutes for delivery after food is ready
            self.estimated_delivery_time = self.estimated_ready_time + datetime.timedelta(minutes=15)
        else:
            self.estimated_delivery_time = None

    def get_total_price(self):
        return sum(item.get_total_price() for item in self.items)

    def get_time_remaining(self):
        """Returns the estimated time remaining in minutes"""
        now = datetime.datetime.now()
        if self.status in [OrderStatus.DELIVERED, OrderStatus.PICKED_UP, OrderStatus.CANCELLED]:
            return 0

        if self.order_type == OrderType.DELIVERY and self.estimated_delivery_time:
            remaining = (self.estimated_delivery_time - now).total_seconds() / 60
        else:
            remaining = (self.estimated_ready_time - now).total_seconds() / 60

        return max(0, int(remaining))

    def to_dict(self):
        return {
            "order_id": self.order_id,
            "customer_id": self.customer_id,
            "restaurant_id": self.restaurant_id,
            "status": self.status.value,
            "order_type": self.order_type.value,
            "delivery_agent_id": self.delivery_agent_id,
            "placed_time": self.placed_time.isoformat(),
            "estimated_ready_time": self.estimated_ready_time.isoformat(),
            "estimated_delivery_time": self.estimated_delivery_time.isoformat() if self.estimated_delivery_time else None
        }

# ===== DATA STORAGE =====

class DataStore:
    """Singleton class to manage persistent data storage using JSON files"""
    _instance = None
    #  Use current working directory for data storage
    _data_dir = os.path.join(os.getcwd(), ".food_delivery_app")
    _lock_file = os.path.join(_data_dir, "datastore.lock")
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DataStore, cls).__new__(cls)
            cls._instance.initialize()
        return cls._instance


    def _ensure_data_dir(self):
        """Ensure data directory exists"""
        os.makedirs(self._data_dir, exist_ok=True)
        print(f"Data directory created at: {self._data_dir}")

    def _get_file_path(self, filename):
        """Get full path for a data file"""
        return os.path.join(self._data_dir, filename)

    def _acquire_lock(self):
        """Acquire a file lock to prevent concurrent writes"""
        self._lock_file_handle = open(self._lock_file, 'w')
        fcntl.flock(self._lock_file_handle.fileno(), fcntl.LOCK_EX)

    def _release_lock(self):
        """Release the file lock"""
        fcntl.flock(self._lock_file_handle.fileno(), fcntl.LOCK_UN)
        self._lock_file_handle.close()

    def initialize(self):
        """Initialize data store with persistent storage"""
        self._ensure_data_dir()

        # Initialize data dictionaries
        self.users = {}
        self.customers = {}
        self.delivery_agents = {}
        self.restaurants = {}
        self.orders = {}
        self.active_user = None

        # Load existing data if available
        self.load_data()

        # If no data exists, load sample data
        if not self.users:
            self.load_sample_data()

    def load_data(self):
        """Load data from JSON files"""
        try:
            self._acquire_lock()

            # Load users
            users_file = self._get_file_path('users.json')
            if os.path.exists(users_file):
                with open(users_file, 'r') as f:
                    user_data = json.load(f)

                    # Reconstruct user objects
                    for user_id, data in user_data.items():
                        role = UserRole(data['role'])
                        if role == UserRole.CUSTOMER:
                            user = Customer(
                                user_id,
                                data['name'],
                                data['email'],
                                data['address']
                            )
                            user.order_history = data.get('order_history', [])
                            self.customers[user_id] = user
                        elif role == UserRole.DELIVERY_AGENT:
                            user = DeliveryAgent(
                                user_id,
                                data['name'],
                                data['email']
                            )
                            user.available = data.get('available', True)
                            user.current_order = data.get('current_order')
                            user.completed_deliveries = data.get('completed_deliveries', [])
                            self.delivery_agents[user_id] = user
                        else:
                            user = User(user_id, data['name'], data['email'], role)

                        self.users[user_id] = user

            # Load restaurants
            restaurants_file = self._get_file_path('restaurants.json')
            if os.path.exists(restaurants_file):
                with open(restaurants_file, 'r') as f:
                    restaurant_data = json.load(f)

                    for rest_id, data in restaurant_data.items():
                        restaurant = Restaurant(rest_id, data['name'], data['address'])

                        # Reconstruct menu items
                        for item_id, item_data in data['menu_items'].items():
                            menu_item = MenuItem(
                                item_id,
                                item_data['name'],
                                item_data['description'],
                                item_data['price'],
                                item_data['prep_time']
                            )
                            restaurant.add_menu_item(menu_item)

                        restaurant.orders = data.get('orders', [])
                        self.restaurants[rest_id] = restaurant

            # Load orders
            orders_file = self._get_file_path('orders.json')
            if os.path.exists(orders_file):
                with open(orders_file, 'r') as f:
                    order_data = json.load(f)

                    for order_id, data in order_data.items():
                        # Reconstruct order items
                        order_items = []
                        for item_data in data['items']:
                            menu_item = self.restaurants[data['restaurant_id']].menu_items[item_data['item_id']]
                            order_items.append(OrderItem(menu_item, item_data['quantity']))

                        # Create order object
                        order = Order(
                            order_id,
                            data['customer_id'],
                            data['restaurant_id'],
                            order_items,
                            OrderType(data['order_type'])
                        )

                        # Restore additional order attributes
                        order.status = OrderStatus(data['status'])
                        order.delivery_agent_id = data.get('delivery_agent_id')
                        order.placed_time = datetime.datetime.fromisoformat(data['placed_time'])
                        order.estimated_ready_time = datetime.datetime.fromisoformat(data['estimated_ready_time'])
                        order.estimated_delivery_time = (
                            datetime.datetime.fromisoformat(data['estimated_delivery_time'])
                            if data['estimated_delivery_time'] else None
                        )

                        self.orders[order_id] = order

        except Exception as e:
            print(f"Error loading data: {e}")
        finally:
            self._release_lock()

    def save_data(self):
        """Save data to JSON files with enhanced logging"""
        try:
            self._acquire_lock()

            # Save users
            users_data = {}
            for user_id, user in self.users.items():
                if isinstance(user, Customer):
                    user_data = user.to_dict()
                elif isinstance(user, DeliveryAgent):
                    user_data = user.to_dict()
                else:
                    user_data = user.to_dict()
                users_data[user_id] = user_data

            users_file = self._get_file_path('users.json')
            with open(users_file, 'w') as f:
                json.dump(users_data, f, indent=2)
            print(f"Users data saved to {users_file}")

            # Save restaurants
            restaurants_data = {}
            for rest_id, restaurant in self.restaurants.items():
                restaurant_data = restaurant.to_dict()
                restaurants_data[rest_id] = restaurant_data

            restaurants_file = self._get_file_path('restaurants.json')
            with open(restaurants_file, 'w') as f:
                json.dump(restaurants_data, f, indent=2)
            print(f"Restaurants data saved to {restaurants_file}")

            # Save orders
            orders_data = {}
            for order_id, order in self.orders.items():
                order_data = order.to_dict()

                # Add additional order item details
                order_data['items'] = [
                    {
                        'item_id': item.menu_item.item_id,
                        'quantity': item.quantity
                    } for item in order.items
                ]

                orders_data[order_id] = order_data

            orders_file = self._get_file_path('orders.json')
            with open(orders_file, 'w') as f:
                json.dump(orders_data, f, indent=2)
            print(f"Orders data saved to {orders_file}")

        except Exception as e:
            print(f"Error saving data: {e}")
        finally:
            self._release_lock()


    def load_sample_data(self):
        """Load sample data for testing"""
        # Keep the previous sample data loading logic the same
        # But add a save_data() call at the end

        # (Keep the existing implementation)

        # Add at the end:
        self.save_data()

# ===== SERVICES =====
class OrderService:
    def __init__(self, data_store):
        self.data_store = data_store

    def create_order(self, customer_id, restaurant_id, item_selections, order_type):
        """Create a new order with JSON persistence"""
        if restaurant_id not in self.data_store.restaurants:
            print(f"Error creating order: '{restaurant_id}'")
            raise ValueError(f"Restaurant not found")

        if order_type == OrderType.DELIVERY:
                available_agents = [agent for agent in self.data_store.delivery_agents.values()
                                   if agent.available]
                if not available_agents:
                    raise ValueError(f"no available agents")
                    return None

        try:
            # Reload latest data to ensure we have most recent state
            self.data_store.load_data()

            # Check if any delivery agents are available for delivery orders
            if order_type == OrderType.DELIVERY:
                available_agents = [agent for agent in self.data_store.delivery_agents.values()
                                   if agent.available]
                if not available_agents:
                    raise ValueError(f"no available agents")
                    return None

            restaurant = self.data_store.restaurants[restaurant_id]

            # Validate menu items
            for selection in item_selections:
                item_id = selection["item_id"]
                if item_id not in restaurant.menu_items:
                    raise ValueError(f"Menu item {item_id} not found.")
                    return None

            # Create order items
            order_items = []
            for selection in item_selections:
                item_id = selection["item_id"]
                quantity = selection["quantity"]
                menu_item = restaurant.menu_items[item_id]
                order_items.append(OrderItem(menu_item, quantity))

            # Create the order with a unique ID
            order_id = f"order-{int(time.time())}-{random.randint(1000, 9999)}"
            order = Order(order_id, customer_id, restaurant_id, order_items, order_type)

            # If delivery order, assign a delivery agent
            if order_type == OrderType.DELIVERY:
                success = self._assign_delivery_agent(order)
                if not success:
                    raise ValueError(f"Cannot assign delivery agent")
                    return None

            # Save the order
            self.data_store.orders[order_id] = order

            # Update customer's order history
            customer = self.data_store.customers[customer_id]
            customer.order_history.append(order_id)

            # Update restaurant's orders
            restaurant.orders.append(order_id)

            # Save data to persist changes
            self.data_store.save_data()

            return order
        except ValueError:
            raise
        except Exception as e:
            print(f"Error creating order: {e}")
            return None
    def update_estimated_delivery_time(self, order_id, new_delivery_time, agent_id):
        """Allow a delivery agent to update the estimated delivery time for an order."""
        if order_id not in self.data_store.orders:
            print(f"❌ Error: Order '{order_id}' not found.")
            return False

        order = self.data_store.orders[order_id]

        # ✅ Prevent updates if the order is already delivered
        if order.status == OrderStatus.DELIVERED:
            print(f"🚨 Error: Cannot update delivery time. Order '{order_id}' is already delivered.")
            return False

        # ✅ Ensure only the assigned delivery agent can update the time
        if order.delivery_agent_id != agent_id:
            print(f"❌ Error: Agent '{agent_id}' is not assigned to order '{order_id}'.")
            return False

        # ✅ Validate delivery time format and check for negative values
        try:
            # Parse HH:MM format into a datetime object
            new_time = datetime.datetime.strptime(new_delivery_time, "%H:%M").time()
        except ValueError:
            print(f"❌ Error: Invalid time format '{new_delivery_time}'. Expected format: HH:MM.")
            raise ValueError("Invalid delivery time format")

        # ✅ Check if the time is in the past (assuming 24-hour format)
        current_time = datetime.datetime.now().time()
        if new_time < current_time:
            print(f"❌ Error: Cannot set delivery time in the past. Current time: {current_time}.")
            raise ValueError("Delivery time cannot be in the past")

        # ✅ Update the estimated delivery time
        order.estimated_delivery_time = new_delivery_time
        self.data_store.orders[order_id] = order  # Save the updated order
        print(f"✅ Order '{order_id}' delivery time updated to {new_delivery_time} by Agent '{agent_id}'.")

        return True



    def _assign_delivery_agent(self, order):
        """Assign an available delivery agent to the order"""
        # Reload latest delivery agent data
        available_agents = [agent for agent in self.data_store.delivery_agents.values()
                           if agent.available]

        if not available_agents:
            print("No delivery agents available")
            return False

        # Select first available agent
        agent = available_agents[0]
        agent.available = False
        agent.current_order = order.order_id
        order.delivery_agent_id = agent.user_id

        return True
    def toggle_delivery_agent_duty(self, agent_id):
        """Toggle the duty status of a delivery agent, but prevent toggling if they have an active order."""
        if agent_id not in self.data_store.delivery_agents:
            print(f"❌ Error: Delivery agent '{agent_id}' not found.")
            return False

        agent = self.data_store.delivery_agents[agent_id]

        # ✅ Prevent toggling duty if the agent is currently assigned to an order
        if agent.current_order:
            print(f"🚨 Error: Agent '{agent_id}' cannot go off duty while handling order '{agent.current_order}'.")
            return False

        # ✅ Toggle duty status
        agent.is_on_duty = not agent.is_on_duty
        print(f"✅ Agent '{agent_id}' duty status toggled to {'ON' if agent.is_on_duty else 'OFF'}.")

        return True

    def update_order_status(self, order_id, new_status, user_id=None):
        """Update the status of an order with JSON persistence"""
        if order_id not in self.data_store.orders:
            print(f"Error updating order status: '{order_id}'")
            return False

        try:
            # Reload latest data to prevent conflicts
            self.data_store.load_data()

            # Retrieve the order
            order = self.data_store.orders[order_id]

            # If the user is a delivery agent, verify it's the assigned agent
            if user_id and order.delivery_agent_id and user_id != order.delivery_agent_id:
                print(f"Error: Order not assigned to agent '{user_id}'")
                return False

            # Check if order is already delivered (prevent marking again)
            if order.status == OrderStatus.DELIVERED:
                print(f"🚨 Error: Order '{order_id}' is already marked as delivered. Cannot update again.")
                return False  # ✅ Fix: Prevent redundant delivery status update

            # Update order status
            order.status = new_status

            # Handle delivery agent status updates
            if new_status == OrderStatus.DELIVERED and order.delivery_agent_id:
                agent = self.data_store.delivery_agents.get(order.delivery_agent_id)
                if agent:
                    agent.available = True

                    # Ensure agent attributes exist
                    if not hasattr(agent, 'completed_deliveries'):
                        agent.completed_deliveries = []

                    # Reset current_order if it matches this order
                    if hasattr(agent, 'current_order') and agent.current_order == order_id:
                        agent.current_order = None

                    # Ensure unique entries in completed deliveries
                    if order_id not in agent.completed_deliveries:
                        agent.completed_deliveries.append(order_id)

            # Save updated data
            self.data_store.save_data()

            return True

        except Exception as e:
            print(f"Error updating order status: {e}")
            return False  # ✅ Fix: Ensure function always returns a boolean


    def get_order_details(self, order_id, user_id=None):
    # Check if order exists
        if order_id not in self.data_store.orders:
            print(f"Error retrieving order details: '{order_id}'")
            raise ValueError(f"Order not found: {order_id}")

        order = self.data_store.orders[order_id]

    # If user_id is provided, check if order belongs to that user
        if user_id and order.customer_id != user_id:
            print(f"Error: Order does not belong to user '{user_id}'")
            raise PermissionError(f"Order does not belong to user")

        try:
            # Reload latest data to ensure accuracy
            self.data_store.load_data()

            # Retrieve related entities
            customer = self.data_store.customers[order.customer_id]
            restaurant = self.data_store.restaurants[order.restaurant_id]

            # Construct order details
            details = {
                "order_id": order.order_id,
                "status": order.status.value,
                "type": order.order_type.value,
                "customer": customer.name,
                "restaurant": restaurant.name,
                "items": [
                    {
                        "name": item.menu_item.name,
                        "quantity": item.quantity,
                        "price": item.menu_item.price
                    } for item in order.items
                ],
                "total_price": order.get_total_price(),
                "time_remaining": order.get_time_remaining(),
                "placed_time": order.placed_time.isoformat(),
                "estimated_ready_time": order.estimated_ready_time.isoformat(),
                "estimated_delivery_time": order.estimated_delivery_time.isoformat() if order.estimated_delivery_time else None
            }

            return details

        except Exception as e:
            print(f"Error retrieving order details: {e}")
            raise KeyError(f"Error retrieving order details: {e}")
    def cancel_order(self, order_id, user_id):
        """Cancel an order with JSON persistence"""
        try:
            # Reload latest data
            self.data_store.load_data()

            # Retrieve the order
            order = self.data_store.orders[order_id]

            # Only allow cancellation of non-completed orders
            if order.status in [OrderStatus.PLACED, OrderStatus.PREPARING]:
                # Update order status
                order.status = OrderStatus.CANCELLED

                # If delivery agent was assigned, free them up
                if order.delivery_agent_id:
                    agent = self.data_store.delivery_agents[order.delivery_agent_id]
                    agent.available = True
                    agent.current_order = None

                # Save updated data
                self.data_store.save_data()

                return True
            else:
                print("Order cannot be cancelled at this stage.")
                return False

        except Exception as e:
            print(f"Error cancelling order: {e}")
            return False

    def get_customer_orders(self, customer_id):
        """Retrieve all orders for a specific customer"""
        try:
            # Reload latest data
            self.data_store.load_data()

            # Filter orders by customer ID
            customer_orders = [
                self.get_order_details(order_id)
                for order_id in self.data_store.customers[customer_id].order_history
            ]

            return customer_orders

        except Exception as e:
            print(f"Error retrieving customer orders: {e}")
            return []
    def get_delivery_agent_history(self, agent_id):
        """Retrieve the delivery history of a delivery agent."""
        if agent_id not in self.data_store.delivery_agents:
            print(f"❌ Error: Delivery agent '{agent_id}' not found.")
            return []

        agent = self.data_store.delivery_agents[agent_id]

        # ✅ Return a list of completed deliveries (or an empty list if none exist)
        return agent.completed_deliveries if hasattr(agent, 'completed_deliveries') else []


class MenuService:
    def __init__(self, data_store):
        self.data_store = data_store

    def get_restaurant_menu(self, restaurant_id):
        """Retrieve the menu for a restaurant"""
        if restaurant_id not in self.data_store.restaurants:
            return None  # Restaurant not found

        restaurant = self.data_store.restaurants[restaurant_id]
        return list(restaurant.menu_items.values())  # ✅ Convert to list

class ManagerService:
     def __init__(self, data_store):
        self.data_store = data_store
        self.delivery_agent_profiles = {}
     def get_all_orders(self):
        """Retrieve all orders from the data store"""
        return list(self.data_store.orders.values())  # ✅ Fetch all stored orders

     def add_delivery_agent(self, name: str, email: str):
        """Add a new delivery agent"""
        try:
            # Validate email (basic check)
            if not email or '@' not in email:
                print("Invalid email address")
                return None

            # Check if email already exists
            for agent in self.data_store.delivery_agents.values():
                if agent.email == email:
                    print("Email already exists")
                    return None

            # Create new delivery agent
            agent_id = str(uuid.uuid4())
            new_agent = DeliveryAgent(agent_id, name, email)

            # Create enhanced profile
            profile = DeliveryAgentProfile(new_agent)

            # Add to data store
            self.data_store.users[agent_id] = new_agent
            self.data_store.delivery_agents[agent_id] = new_agent
            self.delivery_agent_profiles[agent_id] = profile

            # Save data
            self.data_store.save_data()

            print(f"Delivery agent {name} added successfully")
            return new_agent

        except Exception as e:
            print(f"Error adding delivery agent: {e}")
            return None

     def remove_delivery_agent(self, agent_id: str):
        """Remove a delivery agent"""
        try:
            # Check if agent exists and is not currently on an active order
            if agent_id not in self.data_store.delivery_agents:
                print("Delivery agent not found")
                return False

            agent = self.data_store.delivery_agents[agent_id]

            # Check if agent has an active order
            if agent.current_order:
                print("Cannot remove agent with an active order")
                return False

            # Remove from various data stores
            del self.data_store.users[agent_id]
            del self.data_store.delivery_agents[agent_id]

            if agent_id in self.delivery_agent_profiles:
                del self.delivery_agent_profiles[agent_id]

            # Save updated data
            self.data_store.save_data()

            print(f"Delivery agent {agent.name} removed successfully")
            return True

        except Exception as e:
            print(f"Error removing delivery agent: {e}")
            return False

     def get_delivery_agent_profiles(self, agent_id=None):
        """Retrieve delivery agent profiles

        Args:
            agent_id (str, optional): If provided, returns only that agent's profile

        Returns:
            list: List of delivery agent profile dictionaries
        """
        try:
            # If a specific agent ID is requested
            if agent_id:
                if agent_id in self.data_store.delivery_agents:
                    agent = self.data_store.delivery_agents[agent_id]
                    # Make sure agent has completed_deliveries attribute
                    if not hasattr(agent, 'completed_deliveries'):
                        agent.completed_deliveries = []

                    return [{
                        'id': agent.user_id,
                        'name': agent.name,
                        'email': agent.email,
                        'available': getattr(agent, 'available', True),
                        'completed_deliveries': len(agent.completed_deliveries),
                        'current_order': getattr(agent, 'current_order', None)
                    }]
                return []  # Return empty list if agent doesn't exist

            # Return all agents if no specific ID is provided
            profiles = []
            for agent in self.data_store.delivery_agents.values():
                # Make sure agent has completed_deliveries attribute
                if not hasattr(agent, 'completed_deliveries'):
                    agent.completed_deliveries = []

                profiles.append({
                    'id': agent.user_id,
                    'name': agent.name,
                    'email': agent.email,
                    'available': getattr(agent, 'available', True),
                    'completed_deliveries': len(agent.completed_deliveries),
                    'current_order': getattr(agent, 'current_order', None)
                })
            return profiles

        except Exception as e:
            print(f"Error retrieving delivery agent profiles: {e}")
            return []

     def update_restaurant_menu(self, restaurant_id: str, action: str, item_data: Dict[str, Any] = None):
        """Update restaurant menu with various actions"""
        try:
            # Validate restaurant exists
            if restaurant_id not in self.data_store.restaurants:
                raise KeyError(f"Restaurant {restaurant_id} not found")
                print("Restaurant not found")
                return False

            restaurant = self.data_store.restaurants[restaurant_id]

            if action == "add":
                # Validate item data
                if not all(key in item_data for key in ['name', 'description', 'price', 'prep_time']):
                    print("Incomplete menu item data")
                    return False
                 # ✅ New validation: Ensure price is non-negative

                if item_data['price'] < 0:
                    raise ValueError("Price cannot be negative")  # ✅ Fix
                # Create new menu item
                item_id = str(uuid.uuid4())
                new_item = MenuItem(
                    item_id,
                    item_data['name'],
                    item_data['description'],
                    item_data['price'],
                    item_data['prep_time']
                )

                restaurant.add_menu_item(new_item)
                print(f"Menu item {new_item.name} added successfully")

            elif action == "remove":
                # Validate item exists
                if item_data['item_id'] not in restaurant.menu_items:
                    print("Menu item not found")
                    return False

                del restaurant.menu_items[item_data['item_id']]
                print("Menu item removed successfully")

            # Save updated data
            self.data_store.save_data()
            return True
        except ValueError:
         raise  # ✅ Allow ValueError to propagate so unittest can catch it
        except Exception as e:
            print(f"Error updating menu: {e}")
            return False

     def get_restaurant_overview(self, restaurant_id):
        """Get an overview of a restaurant's operations"""
        restaurant = self.data_store.restaurants[restaurant_id]
        orders = [order for order in self.data_store.orders.values()
                 if order.restaurant_id == restaurant_id]

        active_orders = [order for order in orders
                        if order.status not in [OrderStatus.DELIVERED, OrderStatus.PICKED_UP, OrderStatus.CANCELLED]]

        delivery_orders_count = sum(1 for order in orders if order.order_type == OrderType.DELIVERY)
        takeaway_orders_count = sum(1 for order in orders if order.order_type == OrderType.TAKEAWAY)

        return {
            "restaurant_name": restaurant.name,
            "total_orders": len(orders),
            "active_orders": len(active_orders),
            "delivery_orders": delivery_orders_count,
            "takeaway_orders": takeaway_orders_count
        }

# ===== CLI APPLICATION =====
class FoodDeliveryApp:
    def __init__(self):
        self.data_store = DataStore()
        self.order_service = OrderService(self.data_store)
        self.menu_service = MenuService(self.data_store)
        self.manager_service = ManagerService(self.data_store)

    def start(self):
        print("=" * 50)
        print("Welcome to Food Delivery System")
        print("=" * 50)

        # Ensure data is loaded before starting
        self.data_store.load_data()

        # If no sample data exists, load it
        if not self.data_store.users:
            self.load_initial_sample_data()

        # Select user role for the session
        self.select_user_role()

        # Show the appropriate menu based on selected role
        while True:
            self.show_main_menu()


    def load_initial_sample_data(self):
        """Load initial sample data if no data exists"""
        # Create a single restaurant
        restaurant = Restaurant(str(uuid.uuid4()), "Foodie Central", "123 Main St")
        restaurant.add_menu_item(MenuItem(str(uuid.uuid4()), "Margherita Pizza", "Classic tomato and cheese pizza", 12.99, 15))
        restaurant.add_menu_item(MenuItem(str(uuid.uuid4()), "Pepperoni Pizza", "Spicy pepperoni pizza", 14.99, 15))
        restaurant.add_menu_item(MenuItem(str(uuid.uuid4()), "Classic Burger", "Beef burger with cheese", 9.99, 10))
        restaurant.add_menu_item(MenuItem(str(uuid.uuid4()), "Veggie Burger", "Plant-based burger", 10.99, 10))
        self.data_store.restaurants[restaurant.restaurant_id] = restaurant

        # Create sample customers
        customer1 = Customer(str(uuid.uuid4()), "John Doe", "john@example.com", "789 Elm St")
        self.data_store.users[customer1.user_id] = customer1
        self.data_store.customers[customer1.user_id] = customer1

        # Create sample delivery agents
        agent1 = DeliveryAgent(str(uuid.uuid4()), "Mike Smith", "mike@delivery.com")
        self.data_store.users[agent1.user_id] = agent1
        self.data_store.delivery_agents[agent1.user_id] = agent1

        # Ensure at least one more delivery agent is available
        agent2 = DeliveryAgent(str(uuid.uuid4()), "Sarah Johnson", "sarah@delivery.com")
        self.data_store.users[agent2.user_id] = agent2
        self.data_store.delivery_agents[agent2.user_id] = agent2

        # Create sample restaurant staff and manager
        staff1 = User(str(uuid.uuid4()), "Sarah Cook", "sarah@restaurant.com", UserRole.RESTAURANT)
        manager1 = User(str(uuid.uuid4()), "Alex Manager", "alex@company.com", UserRole.MANAGER)

        self.data_store.users[staff1.user_id] = staff1
        self.data_store.users[manager1.user_id] = manager1

        # Save the sample data
        self.data_store.save_data()


    def select_user_role(self):
        print("\nSelect your role:")
        print("1. Customer")
        print("2. Restaurant Staff")
        print("3. Delivery Agent")
        print("4. Manager")

        choice = input("\nEnter choice: ")

        # Reload data to ensure most recent state
        self.data_store.load_data()

        # Set active user based on role selection
        if choice == "1":
            if not self.data_store.customers:
                print("No customers found. Loading sample data...")
                self.load_initial_sample_data()
            self.data_store.active_user = list(self.data_store.customers.values())[0]
        elif choice == "2":
            staff_users = [user for user in self.data_store.users.values() if user.role == UserRole.RESTAURANT]
            if not staff_users:
                print("No restaurant staff found. Loading sample data...")
                self.load_initial_sample_data()
                staff_users = [user for user in self.data_store.users.values() if user.role == UserRole.RESTAURANT]
            self.data_store.active_user = staff_users[0]
        elif choice == "3":
            # Show list of delivery agents for selection
            if not self.data_store.delivery_agents:
                print("No delivery agents found. Loading sample data...")
                self.load_initial_sample_data()

            # Display available delivery agents
            print("\nAvailable Delivery Agents:")
            delivery_agents = list(self.data_store.delivery_agents.values())
            for idx, agent in enumerate(delivery_agents, 1):
                print(f"{idx}. {agent.name} - ID: {agent.user_id}")

            # Prompt for agent selection
            while True:
                try:
                    agent_idx = int(input("\nSelect delivery agent (number): ")) - 1
                    if 0 <= agent_idx < len(delivery_agents):
                        self.data_store.active_user = delivery_agents[agent_idx]
                        break
                    else:
                        print("Invalid selection. Please try again.")
                except ValueError:
                    print("Please enter a valid number.")

        elif choice == "4":
            manager_users = [user for user in self.data_store.users.values() if user.role == UserRole.MANAGER]
            if not manager_users:
                print("No managers found. Loading sample data...")
                self.load_initial_sample_data()
                manager_users = [user for user in self.data_store.users.values() if user.role == UserRole.MANAGER]
            self.data_store.active_user = manager_users[0]
        else:
            print("Invalid choice. Defaulting to Customer role.")
            if not self.data_store.customers:
                self.load_initial_sample_data()
            self.data_store.active_user = list(self.data_store.customers.values())[0]

        print(f"\nWelcome, {self.data_store.active_user.name}!")


    def show_main_menu(self):
        active_user = self.data_store.active_user

        print(f"\nMain Menu ({active_user.role.value}):")

        if active_user.role == UserRole.CUSTOMER:
            self.show_customer_menu()
        elif active_user.role == UserRole.RESTAURANT:
            self.show_restaurant_menu()
        elif active_user.role == UserRole.DELIVERY_AGENT:
            self.show_delivery_agent_menu()
        elif active_user.role == UserRole.MANAGER:
            self.show_manager_menu()

    def show_customer_menu(self):
        print("1. View Restaurants")
        print("2. Place Order")
        print("3. View Order History")
        print("4. Track Order")
        print("5. Change User Role")
        print("6. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            self.view_restaurants()
        elif choice == "2":
            self.place_order()
        elif choice == "3":
            self.view_order_history()
        elif choice == "4":
            self.track_order()
        elif choice == "5":
            self.select_user_role()
        elif choice == "6":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")

    def show_restaurant_menu(self):
        print("1. View Current Orders")
        print("2. Update Order Status")
        print("3. Change User Role")
        print("4. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            self.view_restaurant_orders()
        elif choice == "2":
            self.update_order_status_restaurant()
        elif choice == "3":
            self.select_user_role()
        elif choice == "4":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")

    def show_delivery_agent_menu(self):
        active_user = self.data_store.active_user
        print(f"\nWelcome, {active_user.name} (Delivery Agent)")

        print("1. View Assigned Order")
        print("2. Update Delivery Status")
        print("3. View Delivery History")
        print("4. Toggle Duty Status")
        print("5. Change User Role")
        print("6. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            self.view_assigned_order()
        elif choice == "2":
            self.update_delivery_status()
        elif choice == "3":
            self.view_delivery_history()
        elif choice == "4":
            self.toggle_duty_status()
        elif choice == "5":
            self.select_user_role()
        elif choice == "6":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")
    def toggle_duty_status(self):
        active_user = self.data_store.active_user

        # Ensure the active user is a delivery agent
        if active_user.role != UserRole.DELIVERY_AGENT:
            print("Access denied. Not a delivery agent.")
            return

        agent = self.data_store.delivery_agents[active_user.user_id]

        # Toggle availability
        agent.available = not agent.available

        # Update working hours and status
        if agent.available:
            print("You are now on duty.")
        else:
            print("You are now off duty.")

        # Optional: Save the updated status
        self.data_store.save_data()
    def show_manager_menu(self):
        print("1. View Restaurant Dashboard")
        print("2. Manage Delivery Agents")
        print("3. View All Orders")
        print("4. Update Restaurant Menu")
        print("5. Change User Role")
        print("6. Exit")

        choice = input("\nEnter choice: ")

        if choice == "1":
            self.view_restaurant_dashboard()
        elif choice == "2":
            self.manage_delivery_agents()
        elif choice == "3":
            self.view_all_orders()
        elif choice == "4":
            self.update_restaurant_menu()
        elif choice == "5":
            self.select_user_role()
        elif choice == "6":
            print("Goodbye!")
            exit(0)
        else:
            print("Invalid choice. Please try again.")
    # ===== CUSTOMER FUNCTIONS =====
    def view_restaurants(self):
        print("\nAvailable Restaurants:")
        for idx, restaurant in enumerate(self.data_store.restaurants.values(), 1):
            print(f"{idx}. {restaurant.name} - {restaurant.address}")

    def place_order(self):
        # Display available restaurants
        self.view_restaurants()

        # Select restaurant
        restaurant_idx = int(input("\nSelect restaurant (number): ")) - 1
        restaurant_ids = list(self.data_store.restaurants.keys())
        restaurant_id = restaurant_ids[restaurant_idx]

        # Display menu
        # Display menu
        menu = self.menu_service.get_restaurant_menu(restaurant_id)
        print("\nMenu Items:")
        for idx, item in enumerate(menu, 1):
            print(f"{idx}. {item.name} - ${item.price} - {item.description}")
        # Select items
        item_selections = []
        while True:
            item_idx = int(input("\nSelect item (number, 0 to finish): "))
            if item_idx == 0:
                break

            if 1 <= item_idx <= len(menu):
                quantity = int(input("Enter quantity: "))
                item_id = menu[item_idx-1].item_id
                item_selections.append({"item_id": item_id, "quantity": quantity})
            else:
                print("Invalid item selection.")

        if not item_selections:
            print("No items selected. Order cancelled.")
            return

        # Select order type
        print("\nOrder Type:")
        print("1. Home Delivery")
        print("2. Takeaway")

        order_type_choice = input("Select order type: ")
        if order_type_choice == "1":
            order_type = OrderType.DELIVERY
        else:
            order_type = OrderType.TAKEAWAY

        # Create order
        order = self.order_service.create_order(
            self.data_store.active_user.user_id,
            restaurant_id,
            item_selections,
            order_type
        )
        if(order!=None):
           print(f"\nOrder placed successfully! Order ID: {order.order_id}")
           print(f"Estimated {'delivery' if order_type == OrderType.DELIVERY else 'pickup'} time: " +
                f"{order.estimated_delivery_time if order_type == OrderType.DELIVERY else order.estimated_ready_time}")

    def view_order_history(self):
        active_user = self.data_store.active_user
        customer = self.data_store.customers[active_user.user_id]

        if not customer.order_history:
            print("\nNo order history found.")
            return

        print("\nOrder History:")
        for order_id in customer.order_history:
            order = self.data_store.orders.get(order_id)
            if order:
                restaurant = self.data_store.restaurants[order.restaurant_id]
                print(f"Order ID: {order.order_id} - {restaurant.name} - " +
                      f"Status: {order.status.value} - Total: ${order.get_total_price():.2f}")

    def track_order(self):
        order_id = input("\nEnter Order ID to track: ")

        if order_id not in self.data_store.orders:
            print("Order not found.")
            return

        order_details = self.order_service.get_order_details(order_id)

        print("\nOrder Details:")
        print(f"Order ID: {order_details['order_id']}")
        print(f"Status: {order_details['status']}")
        print(f"Restaurant: {order_details['restaurant']}")
        print(f"Order Type: {order_details['type']}")
        print(f"Time Remaining: {order_details['time_remaining']} minutes")

        print("\nItems:")
        for item in order_details['items']:
            print(f"- {item['name']} x{item['quantity']}")

        print(f"Total Price: ${order_details['total_price']:.2f}")

    # ===== RESTAURANT FUNCTIONS =====
    def view_restaurant_orders(self):
        # In a real system, we would filter by the restaurant the staff works at
        restaurant_id = list(self.data_store.restaurants.keys())[0]
        restaurant = self.data_store.restaurants[restaurant_id]

        print(f"\nCurrent Orders for {restaurant.name}:")

        active_orders = [self.data_store.orders[order_id] for order_id in restaurant.orders
                         if order_id in self.data_store.orders and
                         self.data_store.orders[order_id].status not in
                         [OrderStatus.DELIVERED, OrderStatus.PICKED_UP, OrderStatus.CANCELLED]]

        if not active_orders:
            print("No active orders.")
            return

        for idx, order in enumerate(active_orders, 1):
            print(f"{idx}. Order ID: {order.order_id} - Status: {order.status.value} - " +
                  f"Type: {order.order_type.value} - Items: {len(order.items)}")

    def update_order_status_restaurant(self):
        order_id = input("\nEnter Order ID to update: ")

        if order_id not in self.data_store.orders:
            print("Order not found.")
            return

        order = self.data_store.orders[order_id]

        print("\nCurrent Status:", order.status.value)
        print("\nSelect New Status:")
        print("1. Preparing")
        print("2. Ready for Pickup/Delivery")

        choice = input("\nEnter choice: ")

        if choice == "1":
            new_status = OrderStatus.PREPARING
        elif choice == "2":
            new_status = OrderStatus.READY
        else:
            print("Invalid choice.")
            return

        self.order_service.update_order_status(
            order_id,
            new_status,
            self.data_store.active_user.user_id
        )

        print(f"Order status updated to {new_status.value}.")

    # ===== DELIVERY AGENT FUNCTIONS =====
    def view_assigned_order(self):
        active_user = self.data_store.active_user

        # Ensure the active user is a delivery agent
        if active_user.role != UserRole.DELIVERY_AGENT:
            print("Access denied. Not a delivery agent.")
            return

        agent = self.data_store.delivery_agents[active_user.user_id]

        if not agent.current_order:
            print("\nNo order currently assigned.")
            return

        try:
            order_details = self.order_service.get_order_details(agent.current_order)

            print("\nAssigned Order:")
            print(f"Order ID: {order_details['order_id']}")
            print(f"Customer: {order_details['customer']}")
            print(f"Restaurant: {order_details['restaurant']}")
            print(f"Status: {order_details['status']}")
            print(f"Items: {len(order_details['items'])}")
            print(f"Total Price: ${order_details['total_price']:.2f}")
        except Exception as e:
            print(f"Error retrieving order details: {e}")

    def update_delivery_status(self):
        active_user = self.data_store.active_user

        # Ensure the active user is a delivery agent
        if active_user.role != UserRole.DELIVERY_AGENT:
            print("Access denied. Not a delivery agent.")
            return

        agent = self.data_store.delivery_agents[active_user.user_id]

        if not agent.current_order:
            print("\nNo order currently assigned.")
            return

        order = self.data_store.orders[agent.current_order]

        print("\nCurrent Status:", order.status.value)
        print("\nSelect New Status:")
        print("1. In Transit")
        print("2. Delivered")

        choice = input("\nEnter choice: ")

        try:
            if choice == "1":
                new_status = OrderStatus.IN_TRANSIT
            elif choice == "2":
                new_status = OrderStatus.DELIVERED
            else:
                print("Invalid choice.")
                return

            # Verify the order belongs to this specific agent
            if order.delivery_agent_id != active_user.user_id:
                print("Error: This order is not assigned to you.")
                return

            self.order_service.update_order_status(
                agent.current_order,
                new_status,
                active_user.user_id
            )

            print(f"Delivery status updated to {new_status.value}.")
        except Exception as e:
            print(f"Error updating delivery status: {e}")

    def view_delivery_history(self):
        active_user = self.data_store.active_user

        # Ensure the active user is a delivery agent
        if active_user.role != UserRole.DELIVERY_AGENT:
            print("Access denied. Not a delivery agent.")
            return

        agent = self.data_store.delivery_agents[active_user.user_id]

        if not agent.completed_deliveries:
            print("\nNo completed deliveries found.")
            return

        print(f"\nDelivery History for {active_user.name}:")
        for order_id in agent.completed_deliveries:
            try:
                order = self.data_store.orders.get(order_id)
                if order and order.delivery_agent_id == active_user.user_id:
                    restaurant = self.data_store.restaurants[order.restaurant_id]
                    print(f"Order ID: {order.order_id} - {restaurant.name} - Status: {order.status.value}")
            except Exception as e:
                print(f"Error retrieving order details: {e}")
    # ===== MANAGER FUNCTIONS =====
    def view_restaurant_dashboard(self):
        # In a real system, the manager would select a restaurant
        restaurant_id = list(self.data_store.restaurants.keys())[0]
        overview = self.manager_service.get_restaurant_overview(restaurant_id)

        print(f"\nDashboard for {overview['restaurant_name']}:")
        print(f"Total Orders: {overview['total_orders']}")
        print(f"Active Orders: {overview['active_orders']}")
        print(f"Delivery Orders: {overview['delivery_orders']}")
        print(f"Takeaway Orders: {overview['takeaway_orders']}")

# Add new methods for enhanced management
    def manage_delivery_agents(self):
        while True:
            print("\nDelivery Agent Management:")
            print("1. View Delivery Agents")
            print("2. Add Delivery Agent")
            print("3. Remove Delivery Agent")
            print("4. View Agent Profiles")
            print("5. Back to Main Menu")

            choice = input("\nEnter choice: ")

            if choice == "1":
                self._view_delivery_agents()
            elif choice == "2":
                self._add_delivery_agent()
            elif choice == "3":
                self._remove_delivery_agent()
            elif choice == "4":
                self._view_agent_profiles()
            elif choice == "5":
                break
            else:
                print("Invalid choice. Please try again.")


    def _view_delivery_agents(self):
        print("\nDelivery Agents:")
        for idx, agent in enumerate(self.data_store.delivery_agents.values(), 1):
            status = "Available" if agent.available else f"Busy (Order: {agent.current_order})"
            print(f"{idx}. {agent.name} - Status: {status} - " +
                  f"Completed Deliveries: {len(agent.completed_deliveries)}")

    def _add_delivery_agent(self):
        name = input("Enter agent name: ")
        email = input("Enter agent email: ")
        self.manager_service.add_delivery_agent(name, email)

    def _remove_delivery_agent(self):
        agent_id = input("Enter agent ID to remove: ")
        self.manager_service.remove_delivery_agent(agent_id)

    def _view_agent_profiles(self):
        profiles = self.manager_service.get_delivery_agent_profiles()
        if not profiles:
            print("No agent profiles found.")
            return

        for profile in profiles:
            print("\nAgent Profile:")
            print(f"Name: {profile['name']}")
            print(f"Email: {profile['email']}")
            print("Performance Metrics:")
            for metric, value in profile['performance_metrics'].items():
                print(f"- {metric.replace('_', ' ').title()}: {value}")
            print(f"Duty Status: {'On Duty' if profile['duty_status'] else 'Off Duty'}")
            print("Working Hours:")
            print(f"- Total Hours: {profile['working_hours']['total_hours']:.2f}")

    def update_restaurant_menu(self):
        # In a real system, select restaurant based on manager's restaurant
        restaurant_id = list(self.data_store.restaurants.keys())[0]

        while True:
            print("\nMenu Management:")
            print("1. View Menu")
            print("2. Add Menu Item")
            print("3. Remove Menu Item")
            print("4. Back to Main Menu")

            choice = input("\nEnter choice: ")

            if choice == "1":
                self._view_menu(restaurant_id)
            elif choice == "2":
                self._add_menu_item(restaurant_id)
            elif choice == "3":
                self._remove_menu_item(restaurant_id)
            elif choice == "4":
                break
            else:
                print("Invalid choice. Please try again.")



    def _view_menu(self, restaurant_id):
        menu = self.menu_service.get_restaurant_menu(restaurant_id)
        print("\nCurrent Menu:")
        for item in menu:
            print(f"ID: {item['item_id']} - {item['name']} - ${item['price']} - {item['description']}")

    def _add_menu_item(self, restaurant_id):
        name = input("Enter item name: ")
        description = input("Enter item description: ")

        # Input validation for price
        while True:
            try:
                price = float(input("Enter item price: "))
                break
            except ValueError:
                print("Invalid price. Please enter a number.")

        # Input validation for preparation time
        while True:
            try:
                prep_time = int(input("Enter preparation time (minutes): "))
                break
            except ValueError:
                print("Invalid time. Please enter a number.")

        item_data = {
            'name': name,
            'description': description,
            'price': price,
            'prep_time': prep_time
        }

        self.manager_service.update_restaurant_menu(restaurant_id, "add", item_data)

    def _remove_menu_item(self, restaurant_id):
        item_id = input("Enter item ID to remove: ")
        item_data = {'item_id': item_id}
        self.manager_service.update_restaurant_menu(restaurant_id, "remove", item_data)

    def view_all_orders(self):
        print("\nAll Orders:")
        for order_id, order in self.data_store.orders.items():
            restaurant = self.data_store.restaurants[order.restaurant_id]
            print(f"Order ID: {order.order_id} - {restaurant.name} - " +
                  f"Status: {order.status.value} - Type: {order.order_type.value}")

# ===== MAIN =====
if __name__ == "__main__":
    app = FoodDeliveryApp()
    app.start()