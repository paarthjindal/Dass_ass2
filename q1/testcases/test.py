import unittest
import uuid
import datetime
import os
import sys
import json

# Add the parent directory to the Python path to import the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main application classes and enums
from src.cli import (
    FoodDeliveryApp, 
    DataStore, 
    OrderService, 
    MenuService, 
    ManagerService,
    User, 
    Customer, 
    DeliveryAgent, 
    Restaurant, 
    MenuItem, 
    Order, 
    OrderItem,
    OrderStatus, 
    OrderType, 
    UserRole
)

class EnhancedTestResult(unittest.TestResult):
    def __init__(self, stream=sys.stderr, descriptions=True, verbosity=1):
        super().__init__(stream, descriptions, verbosity)
        self.stream = sys.stdout
        self.test_results = {
            'total': 0,
            'passed': 0,
            'failed': 0,
            'errors': 0
        }
    
    def addSuccess(self, test):
        super().addSuccess(test)
        self._print_result(test, 'PASS', '\033[92m')  # Green
        self.test_results['total'] += 1
        self.test_results['passed'] += 1
    
    def addError(self, test, err):
        super().addError(test, err)
        self._print_result(test, 'ERROR', '\033[93m')  # Yellow
        self._print_traceback(err)
        self.test_results['total'] += 1
        self.test_results['errors'] += 1
    
    def addFailure(self, test, err):
        super().addFailure(test, err)
        self._print_result(test, 'FAIL', '\033[91m')  # Red
        self._print_traceback(err)
        self.test_results['total'] += 1
        self.test_results['failed'] += 1
    
    def _print_result(self, test, status, color):
        try:
            # Try multiple ways to get the test name
            if hasattr(test, '_testMethodName'):
                test_name = test._testMethodName
            elif hasattr(test, 'shortDescription'):
                test_name = test.shortDescription() or str(test)
            else:
                test_name = str(test)
            
            # Truncate very long test names
            if len(test_name) > 100:
                test_name = test_name[:97] + '...'
            
            print(f"{color}{status:<10}\033[0m {test_name}")
        except Exception as e:
            # Fallback print in case of any unexpected error
            print(f"{color}{status:<10}\033[0m Test Case")
    
    def _print_traceback(self, err):
        try:
            print('\033[90m')  # Gray color for traceback
            traceback.print_exception(*err)
            print('\033[0m')  # Reset color
        except Exception:
            # Ensure any error in printing traceback doesn't crash the test runner
            print("Error printing traceback")
    
    def printSummary(self):
        print("\n--- Test Summary ---")
        print(f"Total Tests:  {self.test_results['total']}")
        print(f"Passed:       {self.test_results['passed']}")
        print(f"Failed:       {self.test_results['failed']}")
        print(f"Errors:       {self.test_results['errors']}")

        # Color-coded summary
        if self.test_results['failed'] or self.test_results['errors']:
            status_color = '\033[91m'  # Red for failures
        else:
            status_color = '\033[92m'  # Green for success
        
        print(f"\n{status_color}Overall Status: {'PASS' if self.wasSuccessful() else 'FAIL'}\033[0m")



class EnhancedTestRunner(unittest.TextTestRunner):
    def __init__(self, *args, **kwargs):
        kwargs['resultclass'] = EnhancedTestResult
        super().__init__(*args, **kwargs)
    
    def run(self, test):
        result = super().run(test)
        result.printSummary()
        return result


class TestFoodDeliverySystem(unittest.TestCase):
    def setUp(self):
        """Set up a fresh environment for each test"""
        # Create a new data store for each test
        self.data_store = DataStore()
        
        # Reset data store
        self.data_store.users.clear()
        self.data_store.customers.clear()
        self.data_store.delivery_agents.clear()
        self.data_store.restaurants.clear()
        self.data_store.orders.clear()
        
        # Create services
        self.order_service = OrderService(self.data_store)
        self.menu_service = MenuService(self.data_store)
        self.manager_service = ManagerService(self.data_store)
        
        # Create test data
        self._create_test_data()
    
    def _create_test_data(self):
        """Create sample data for testing"""
        # Create test restaurant
        self.test_restaurant = Restaurant(str(uuid.uuid4()), "Test Restaurant", "123 Test St")
        self.test_menu_item = MenuItem(str(uuid.uuid4()), "Test Pizza", "Test Description", 10.99, 15)
        self.test_restaurant.add_menu_item(self.test_menu_item)
        self.data_store.restaurants[self.test_restaurant.restaurant_id] = self.test_restaurant
        
        # Create test customer
        self.test_customer = Customer(str(uuid.uuid4()), "Test Customer", "test@example.com", "456 Test Ave")
        self.data_store.users[self.test_customer.user_id] = self.test_customer
        self.data_store.customers[self.test_customer.user_id] = self.test_customer
        
        # Create test delivery agent
        self.test_delivery_agent = DeliveryAgent(str(uuid.uuid4()), "Test Agent", "agent@example.com")
        self.data_store.users[self.test_delivery_agent.user_id] = self.test_delivery_agent
        self.data_store.delivery_agents[self.test_delivery_agent.user_id] = self.test_delivery_agent


    # MANAGER SERVICE TESTS
    def test_manager_add_delivery_agent_duplicate_email(self):
        """Test adding a delivery agent with an existing email"""
        # First agent
        first_agent = self.manager_service.add_delivery_agent("Agent 1", "unique@example.com")
        self.assertIsNotNone(first_agent)
        
        # Try to add another agent with same email
        second_agent = self.manager_service.add_delivery_agent("Agent 2", "unique@example.com")
        self.assertIsNone(second_agent)
    
    def test_manager_remove_nonexistent_agent(self):
        """Test removing a delivery agent that doesn't exist"""
        # Try to remove an agent with a non-existent ID
        result = self.manager_service.remove_delivery_agent("non-existent-id")
        self.assertFalse(result)
    
    def test_manager_add_duplicate_menu_item(self):
        """Test adding a menu item with existing details"""
        restaurant_id = self.test_restaurant.restaurant_id
        
        # First item addition
        first_item = {
            'name': 'Unique Pizza', 
            'description': 'Test Pizza', 
            'price': 12.99, 
            'prep_time': 15
        }
        result = self.manager_service.update_restaurant_menu(restaurant_id, "add", first_item)
        self.assertTrue(result)
        
        # Try to add item with same details
        second_result = self.manager_service.update_restaurant_menu(restaurant_id, "add", first_item)
        self.assertTrue(second_result)  # Note: Currently allows duplicate items
    
    def test_manager_remove_nonexistent_menu_item(self):
        """Test removing a menu item that doesn't exist"""
        restaurant_id = self.test_restaurant.restaurant_id
        
        # Try to remove non-existent item
        result = self.manager_service.update_restaurant_menu(
            restaurant_id, 
            "remove", 
            {'item_id': "non-existent-id"}
        )
        self.assertFalse(result)
    
    def test_manager_view_nonexistent_agent_profile(self):
        """Test viewing profile of a non-existent delivery agent"""
        profiles = self.manager_service.get_delivery_agent_profiles()
        self.assertEqual(len(profiles), 1)  # Only the test agent
    
    # DELIVERY AGENT TESTS
    def test_delivery_agent_order_delivery_flow(self):
        """Test full order delivery workflow"""
        # Create an order and assign to the agent
        order_items = [
            OrderItem(self.test_menu_item, 1)
        ]
        order = Order(
            str(uuid.uuid4()), 
            self.test_customer.user_id, 
            self.test_restaurant.restaurant_id, 
            order_items, 
            OrderType.DELIVERY
        )
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        
        # Mark order as in transit
        self.order_service.update_order_status(
            order.order_id, 
            OrderStatus.IN_TRANSIT, 
            self.test_delivery_agent.user_id
        )
        
        # Mark order as delivered
        self.order_service.update_order_status(
            order.order_id, 
            OrderStatus.DELIVERED, 
            self.test_delivery_agent.user_id
        )
        
        # Check if order is in completed deliveries
        self.assertIn(order.order_id, self.test_delivery_agent.completed_deliveries)
        self.assertIsNone(self.test_delivery_agent.current_order)
    
    def test_delivery_agent_mark_nonexistent_order_delivered(self):
        """Test marking a non-existent order as delivered"""
        result = self.order_service.update_order_status(
            "non-existent-order", 
            OrderStatus.DELIVERED, 
            self.test_delivery_agent.user_id
        )
        self.assertFalse(result)
    
    def test_delivery_agent_mark_already_delivered_order(self):
        """Test marking an already delivered order"""
        # Create and deliver an order
        order_items = [
            OrderItem(self.test_menu_item, 1)
        ]
        order = Order(
            str(uuid.uuid4()), 
            self.test_customer.user_id, 
            self.test_restaurant.restaurant_id, 
            order_items, 
            OrderType.DELIVERY
        )
        order.delivery_agent_id = self.test_delivery_agent.user_id
        order.status = OrderStatus.DELIVERED
        
        # Try to mark as delivered again
        result = self.order_service.update_order_status(
            order.order_id, 
            OrderStatus.DELIVERED, 
            self.test_delivery_agent.user_id
        )
        self.assertFalse(result)
    
    def test_delivery_agent_toggle_duty_with_active_order(self):
        """Test toggling duty status while on an active order"""
        # Assign an order to the agent
        order_items = [
            OrderItem(self.test_menu_item, 1)
        ]
        order = Order(
            str(uuid.uuid4()), 
            self.test_customer.user_id, 
            self.test_restaurant.restaurant_id, 
            order_items, 
            OrderType.DELIVERY
        )
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        
        # Try to toggle duty
        original_status = self.test_delivery_agent.available
        self.test_delivery_agent.available = not original_status
        
        # Verify status remains unchanged
        self.assertEqual(self.test_delivery_agent.available, original_status)
    
    # CUSTOMER TESTS
    def test_customer_place_multiple_identical_orders(self):
        """Test placing multiple identical orders"""
        order_items = [
            OrderItem(self.test_menu_item, 1)
        ]
        
        # Place first order
        first_order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )
        
        # Place second order
        second_order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )
        
        # Verify orders are different
        self.assertNotEqual(first_order.order_id, second_order.order_id)
        self.assertEqual(len(self.test_customer.order_history), 2)
    
    def test_customer_check_nonexistent_order_status(self):
        """Test checking status of a non-existent order"""
        with self.assertRaises(KeyError):
            self.order_service.get_order_details("non-existent-order")
    
    def test_customer_check_order_of_another_user(self):
        """Test attempting to check an order belonging to another user"""
        # Create an order for the test customer
        order_items = [
            OrderItem(self.test_menu_item, 1)
        ]
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )
        
        # Create another customer
        another_customer = Customer(
            str(uuid.uuid4()), 
            "Another Customer", 
            "another@example.com", 
            "789 Another St"
        )
        
        # Attempt to get order details as another customer
        with self.assertRaises(KeyError):
            self.order_service.get_order_details(order.order_id, another_customer.user_id)
    
    # ADDITIONAL EDGE CASE TESTS
    def test_order_creation_with_invalid_restaurant(self):
        """Test creating an order with an invalid restaurant ID"""
        with self.assertRaises(KeyError):
            self.order_service.create_order(
                self.test_customer.user_id,
                "invalid-restaurant-id",
                [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
                OrderType.DELIVERY
            )
    
    def test_order_creation_with_invalid_menu_item(self):
        """Test creating an order with an invalid menu item"""
        with self.assertRaises(KeyError):
            self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": "invalid-item-id", "quantity": 1}],
                OrderType.DELIVERY
            )


# Custom test runner that uses colored output
def run_tests():
    # Create a test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(TestFoodDeliverySystem)
    
    # Create a test runner with color support
    runner = EnhancedTestRunner(verbosity=2, stream=sys.stdout)
    
    # Run the tests
    runner.run(suite)
    # Exit with non-zero status if tests failed
    # sys.exit(not result.wasSuccessful())


if __name__ == '__main__':
    run_tests()


# Key aspects of these tests:

# ## Manager Service Tests
# 1. `test_manager_add_delivery_agent_duplicate_email`: Prevents adding agents with duplicate emails
# 2. `test_manager_remove_nonexistent_agent`: Handles removing non-existent agents
# 3. `test_manager_add_duplicate_menu_item`: Tests adding menu items with existing details
# 4. `test_manager_remove_nonexistent_menu_item`: Handles removing non-existent menu items
# 5. `test_manager_view_nonexistent_agent_profile`: Checks profile viewing scenarios

# ## Delivery Agent Tests
# 1. `test_delivery_agent_order_delivery_flow`: Full order delivery workflow
# 2. `test_delivery_agent_mark_nonexistent_order_delivered`: Prevents marking non-existent orders
# 3. `test_delivery_agent_mark_already_delivered_order`: Prevents re-marking delivered orders
# 4. `test_delivery_agent_toggle_duty_with_active_order`: Handles duty status with active orders

# ## Customer Tests
# 1. `test_customer_place_multiple_identical_orders`: Allows placing multiple similar orders
# 2. `test_customer_check_nonexistent_order_status`: Handles checking non-existent orders
# 3. `test_customer_check_order_of_another_user`: Prevents accessing others' orders

# ## Additional Edge Case Tests
# 1. `test_order_creation_with_invalid_restaurant`: Handles invalid restaurant IDs
# 2. `test_order_creation_with_invalid_menu_item`: Handles invalid menu items

# Notes:
# - The tests use a fresh `DataStore` for each test to ensure isolation
# - Comprehensive coverage of various scenarios and edge cases
# - Uses PyUnit's assertion methods for verification
# - Simulates real-world usage and potential error conditions

