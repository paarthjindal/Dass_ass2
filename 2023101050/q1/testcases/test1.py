import unittest
import uuid
import datetime
import os
import sys
import json
import traceback

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

        # Create food delivery app instance
        # self.app = FoodDeliveryApp(self.data_store)

        # Create test data
        self._create_test_data()

    def _create_test_data(self):
        """Create sample data for testing"""
        # Create test restaurant
        self.test_restaurant = Restaurant(str(uuid.uuid4()), "Test Restaurant", "123 Test St")
        self.test_menu_item = MenuItem(str(uuid.uuid4()), "Test Pizza", "Test Description", 10.99, 15)
        self.test_menu_item2 = MenuItem(str(uuid.uuid4()), "Test Burger", "Delicious Burger", 8.99, 10)
        self.test_restaurant.add_menu_item(self.test_menu_item)
        self.test_restaurant.add_menu_item(self.test_menu_item2)
        self.data_store.restaurants[self.test_restaurant.restaurant_id] = self.test_restaurant

        # Create test customer
        self.test_customer = Customer(str(uuid.uuid4()), "Test Customer", "test@example.com", "456 Test Ave")
        self.data_store.users[self.test_customer.user_id] = self.test_customer
        self.data_store.customers[self.test_customer.user_id] = self.test_customer

          # Create test customer
        self.another_customer = Customer(str(uuid.uuid4()), "Another Customer", "test1@example.com", "456 Test1 Ave")
        self.data_store.users[self.another_customer.user_id] = self.another_customer
        self.data_store.customers[self.another_customer.user_id] = self.another_customer
        # Create test delivery agent
        self.test_delivery_agent = DeliveryAgent(str(uuid.uuid4()), "Test Agent", "agent@example.com")
        self.data_store.users[self.test_delivery_agent.user_id] = self.test_delivery_agent
        self.data_store.delivery_agents[self.test_delivery_agent.user_id] = self.test_delivery_agent

        # Create manager user
        self.test_manager = User(str(uuid.uuid4()), "Manager", "manager@example.com", UserRole.MANAGER)
        self.data_store.users[self.test_manager.user_id] = self.test_manager

    ###############################
    # BASIC SETUP AND USER TESTS
    ###############################

    def test_manager_add_delivery_agent(self):
        """Test manager adding a new delivery agent"""
        agent = self.manager_service.add_delivery_agent("New Agent", "newagent@example.com")
        self.assertIsNotNone(agent)
        self.assertEqual(agent.name, "New Agent")
        self.assertEqual(agent.email, "newagent@example.com")
        self.assertIn(agent.user_id, self.data_store.delivery_agents)




    ###############################
    # CUSTOMER BASIC TESTS
    ###############################

    def test_customer_place_delivery_order(self):
        """Test customer placing a home delivery order"""
        # Place the order
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        self.assertIsNotNone(order)
        self.assertEqual(order.customer_id, self.test_customer.user_id)
        self.assertEqual(order.status, OrderStatus.PLACED)
        self.assertIn(order.order_id, self.test_customer.order_history)

    def test_customer_place_takeaway_order(self):
        """Test customer placing a takeaway order"""
        # Place the order
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
           OrderType.TAKEAWAY

        )

        self.assertIsNotNone(order)
        self.assertEqual(order.customer_id, self.test_customer.user_id)
        self.assertEqual(order.order_type, OrderType.TAKEAWAY)
        self.assertEqual(order.status, OrderStatus.PLACED)
        self.assertIn(order.order_id, self.test_customer.order_history)



    def test_customer_view_order_history(self):
        """Test customer viewing their order history"""
        print("Available delivery agents:", len(self.order_service.data_store.delivery_agents))
        sys.stdout.flush()  # ✅ Force output

        try:
            order1 = self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
                OrderType.DELIVERY
            )
            print("Order 1 created:", order1.order_id if order1 else "Failed")
        except Exception as e:
            print("🚨 Exception occurred while creating Order 1:", e)
            order1 = None
        sys.stdout.flush()

        try:
            order2 = self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": self.test_menu_item2.item_id, "quantity": 2}],
                OrderType.TAKEAWAY
            )
            print("Order 2 created:", order2.order_id if order2 else "Failed")
        except Exception as e:
            print("🚨 Exception occurred while creating Order 2:", e)
            order2 = None
        sys.stdout.flush()

        if not order2:
            print("🚨 Order 2 was not created! Possible issue with order constraints.")
            sys.stdout.flush()

        self.assertIsNotNone(order1, "Order 1 was not created")
        self.assertIsNotNone(order2, "Order 2 was not created")  # This may fail if order2 == None

        # Get order history from latest stored customer object
        test_customer_from_store = self.order_service.data_store.customers[self.test_customer.user_id]
        order_history = test_customer_from_store.order_history

        print(f"Customer order history AFTER: {order_history}")
        sys.stdout.flush()

        self.assertEqual(len(order_history), 2)
        self.assertIn(order1.order_id, order_history)
        self.assertIn(order2.order_id, order_history)


    ###############################
    # MANAGER BASIC TESTS
    ###############################

    def test_manager_view_all_orders(self):
        """Test manager viewing all orders"""
        # Place two orders
        order1 = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        order2 = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item2.item_id, "quantity": 2}],
            OrderType.TAKEAWAY
        )

        # Get all orders
        all_orders = self.manager_service.get_all_orders()

        self.assertEqual(len(all_orders), 2)
        order_ids = [o.order_id for o in all_orders]
        self.assertIn(order1.order_id, order_ids)
        self.assertIn(order2.order_id, order_ids)

    def test_manager_add_menu_item(self):
        """Test manager adding a menu item"""
        restaurant_id = self.test_restaurant.restaurant_id

        # Add new menu item
        new_item = {
            'name': 'New Pasta',
            'description': 'Delicious pasta',
            'price': 12.99,
            'prep_time': 20
        }

        result = self.manager_service.update_restaurant_menu(restaurant_id, "add", new_item)
        self.assertTrue(result)

        # Verify item was added
        restaurant = self.data_store.restaurants[restaurant_id]
        menu_items = restaurant.menu_items  # ✅ Use the correct attribute

        pasta_items = [item for item in menu_items.values() if item.name == 'New Pasta']
        self.assertEqual(len(pasta_items), 1)
        pasta_item = pasta_items[0]
        self.assertEqual(pasta_item.description, 'Delicious pasta')
        self.assertEqual(pasta_item.price, 12.99)
        self.assertEqual(pasta_item.prep_time, 20)


    def test_manager_remove_menu_item(self):
        """Test manager removing a menu item"""
        restaurant_id = self.test_restaurant.restaurant_id
        item_id = self.test_menu_item.item_id

        # Remove the menu item
        result = self.manager_service.update_restaurant_menu(
            restaurant_id,
            "remove",
            {'item_id': item_id}
        )

        self.assertTrue(result)

        # Verify item was removed
        restaurant = self.data_store.restaurants[restaurant_id]
        self.assertNotIn(item_id, restaurant.menu_items)

    def test_manager_view_restaurant_menu(self):
        """Test manager viewing restaurant menu"""
        restaurant_id = self.test_restaurant.restaurant_id

        # Get the menu
        menu = self.menu_service.get_restaurant_menu(restaurant_id)

        self.assertEqual(len(menu), 2)
        menu_item_ids = [item.item_id for item in menu]
        self.assertIn(self.test_menu_item.item_id, menu_item_ids)
        self.assertIn(self.test_menu_item2.item_id, menu_item_ids)

    def test_manager_remove_delivery_agent(self):
        """Test manager removing a delivery agent"""
        agent_id = self.test_delivery_agent.user_id

        # Remove the agent
        result = self.manager_service.remove_delivery_agent(agent_id)

        self.assertTrue(result)
        self.assertNotIn(agent_id, self.data_store.delivery_agents)

    def test_manager_view_staff_profiles(self):
        """Test manager viewing staff profiles"""
        # Add a second agent
        agent2 = self.manager_service.add_delivery_agent("Second Agent", "second@example.com")

        # Get agent profiles
        profiles = self.manager_service.get_delivery_agent_profiles()

        self.assertEqual(len(profiles), 2)
        agent_ids = [profile['id'] for profile in profiles]
        self.assertIn(self.test_delivery_agent.user_id, agent_ids)
        self.assertIn(agent2.user_id, agent_ids)

    ###############################
    # DELIVERY AGENT BASIC TESTS
    ###############################

    def test_delivery_agent_view_current_order(self):
        """Test delivery agent viewing current order"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Get current order
        current_order = None
        if self.test_delivery_agent.current_order:
            current_order = self.data_store.orders.get(self.test_delivery_agent.current_order)

        self.assertIsNotNone(current_order)
        self.assertEqual(current_order.order_id, order.order_id)

    def test_delivery_agent_mark_order_delivered(self):
        """Test delivery agent marking an order as delivered"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Update order status to IN_TRANSIT
        self.order_service.update_order_status(
            order.order_id,
            OrderStatus.IN_TRANSIT,
            self.test_delivery_agent.user_id
        )

        # Mark order as DELIVERED
        result = self.order_service.update_order_status(
            order.order_id,
            OrderStatus.DELIVERED,
            self.test_delivery_agent.user_id
        )

        # Fetch the updated agent from `data_store` (fix for stale reference issue)
        updated_agent = self.data_store.delivery_agents[self.test_delivery_agent.user_id]

        # Assertions
        self.assertTrue(result)
        self.assertEqual(self.data_store.orders[order.order_id].status, OrderStatus.DELIVERED)

        # ✅ Fix: Check the latest agent object from `data_store`
        self.assertIsNone(updated_agent.current_order)

        self.assertIn(order.order_id, updated_agent.completed_deliveries)

    def test_delivery_agent_update_delivery_time(self):
        """Test delivery agent updating delivery time"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Update delivery time
        # Note: Assuming there's a method like this in OrderService
        # If not, you may need to add it or test differently
        initial_delivery_time = order.estimated_delivery_time

        # Add 15 minutes
        new_delivery_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=30)
        ).strftime("%H:%M")

        result = self.order_service.update_estimated_delivery_time(
            order.order_id,
            new_delivery_time,
            self.test_delivery_agent.user_id
        )

        self.assertTrue(result)
        self.assertEqual(self.data_store.orders[order.order_id].estimated_delivery_time, new_delivery_time)

    def test_delivery_agent_view_delivery_history(self):
        """Test delivery agent viewing delivery history"""
        # Create and deliver two orders
        for i in range(2):
            order = self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
                OrderType.DELIVERY
            )

            # Assign and deliver the order
            order.delivery_agent_id = self.test_delivery_agent.user_id
            self.test_delivery_agent.current_order = order.order_id
            self.data_store.orders[order.order_id] = order

            # Mark as in transit then delivered
            self.order_service.update_order_status(
                order.order_id,
                OrderStatus.IN_TRANSIT,
                self.test_delivery_agent.user_id
            )
            self.order_service.update_order_status(
                order.order_id,
                OrderStatus.DELIVERED,
                self.test_delivery_agent.user_id
            )

        # ✅ Fetch the updated agent from `data_store`
        updated_agent = self.data_store.delivery_agents[self.test_delivery_agent.user_id]

        # Check delivery history
        delivery_history = updated_agent.completed_deliveries
        print(f"✅ Delivery history: {delivery_history}")  # Debugging
        self.assertEqual(len(delivery_history), 2)


    ###############################
    # MANAGER EDGE CASE TESTS
    ###############################

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

    def test_manager_remove_delivery_agent_with_active_order(self):
        """Test removing a delivery agent with an active order"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Try to remove the agent
        result = self.manager_service.remove_delivery_agent(self.test_delivery_agent.user_id)

        # Should not be allowed to remove agent with active order
        self.assertFalse(result)
        self.assertIn(self.test_delivery_agent.user_id, self.data_store.delivery_agents)

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

    def test_manager_update_menu_with_invalid_price(self):
        """Test updating menu with invalid price"""
        restaurant_id = self.test_restaurant.restaurant_id

        # Try to add item with negative price
        invalid_item = {
            'name': 'Invalid Pizza',
            'description': 'Test Pizza',
            'price': -12.99,
            'prep_time': 15
        }

        with self.assertRaises(ValueError):
            self.manager_service.update_restaurant_menu(restaurant_id, "add", invalid_item)

    def test_manager_add_delivery_agent_with_empty_id(self):
        """Test adding a delivery agent with empty ID"""
        # Try to add agent with empty ID - this should be handled by uuid generation
        agent = self.manager_service.add_delivery_agent("Empty ID Agent", "empty@example.com")
        self.assertIsNotNone(agent)
        self.assertNotEqual(agent.user_id, "")

    def test_manager_view_nonexistent_agent_profile(self):
        """Test viewing profile of a non-existent delivery agent"""
        profiles = self.manager_service.get_delivery_agent_profiles()

        # Check that non-existent agent is not in profiles
        non_existent_id = "non-existent-id"
        agent_ids = [profile['id'] for profile in profiles]
        self.assertNotIn(non_existent_id, agent_ids)

    def test_manager_view_removed_agent_profile(self):
        """Test viewing profile of a removed delivery agent"""
        agent_id = self.test_delivery_agent.user_id

        # Remove the agent
        self.manager_service.remove_delivery_agent(agent_id)

        # Get agent profiles
        profiles = self.manager_service.get_delivery_agent_profiles()

        # Check that removed agent is not in profiles
        agent_ids = [profile['id'] for profile in profiles]
        self.assertNotIn(agent_id, agent_ids)

    ###############################
    # DELIVERY AGENT EDGE CASE TESTS
    ###############################

    def test_delivery_agent_mark_order_delivered_and_check_removal(self):
        """Test marking order as delivered and checking it's removed from current order"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Mark order as IN_TRANSIT and then DELIVERED
        self.order_service.update_order_status(
            order.order_id,
            OrderStatus.IN_TRANSIT,
            self.test_delivery_agent.user_id
        )
        self.order_service.update_order_status(
            order.order_id,
            OrderStatus.DELIVERED,
            self.test_delivery_agent.user_id
        )

        # ✅ Fetch the updated delivery agent object from data_store
        updated_agent = self.data_store.delivery_agents[self.test_delivery_agent.user_id]

        # Check that current order is cleared
        self.assertIsNone(updated_agent.current_order)

        # Check that order is in completed deliveries
        self.assertIn(order.order_id, updated_agent.completed_deliveries)

    def test_delivery_agent_update_time_and_check_order_remains(self):
        """Test updating delivery time and checking order remains current"""
        # Create an order and assign to the agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign order to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Update delivery time
        new_delivery_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=30)
        ).strftime("%H:%M")

        self.order_service.update_estimated_delivery_time(
            order.order_id,
            new_delivery_time,
            self.test_delivery_agent.user_id
        )

        # Check that current order is still assigned
        self.assertEqual(self.test_delivery_agent.current_order, order.order_id)

    def test_delivery_agent_mark_nonexistent_order_delivered(self):
        """Test marking a non-existent order as delivered"""
        result = self.order_service.update_order_status(
            "non-existent-order",
            OrderStatus.DELIVERED,
            self.test_delivery_agent.user_id
        )
        self.assertFalse(result)

    def test_delivery_agent_mark_already_delivered_order(self):
        """Test that a delivery agent cannot mark an already delivered order as delivered again"""

        # Step 1: Create an order
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Step 2: Assign the order to the delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.data_store.orders[order.order_id] = order

        # Step 3: Mark the order as DELIVERED
        self.order_service.update_order_status(
            order.order_id,
            OrderStatus.DELIVERED,
            self.test_delivery_agent.user_id
        )

        # Step 4: Ensure the agent is NO LONGER assigned to the order
        updated_order = self.data_store.orders[order.order_id]
        print(f"🔍 Order {updated_order.order_id} status after delivery: {updated_order.status}")
        print(f"🔍 Order's assigned delivery agent after delivery: {updated_order.delivery_agent_id}")  # Likely None

        # Step 5: Try to mark it as delivered again (should fail due to agent restriction)
        result = self.order_service.update_order_status(
            order.order_id,
            OrderStatus.DELIVERED,
            self.test_delivery_agent.user_id
        )

        print(f"🚨 update_order_status() result on second attempt: {result}")  # Debugging

        # Step 6: Ensure function returns False
        self.assertFalse(result, "A delivered order should not be updated by an agent again.")


    def test_update_delivery_time_for_nonexistent_order(self):
        """Test updating delivery time for a non-existent order"""
        new_delivery_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=30)
        ).strftime("%H:%M")

        result = self.order_service.update_estimated_delivery_time(
            "non-existent-order",
            new_delivery_time,
            self.test_delivery_agent.user_id
        )

        self.assertFalse(result)

    def test_update_delivery_time_for_already_delivered_order(self):
        """Test updating delivery time for an already delivered order"""
        # Create and deliver an order
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Mark as delivered
        order.delivery_agent_id = self.test_delivery_agent.user_id
        order.status = OrderStatus.DELIVERED
        self.test_delivery_agent.completed_deliveries.append(order.order_id)
        self.test_delivery_agent.current_order = None
        self.data_store.orders[order.order_id] = order

        # Try to update delivery time
        new_delivery_time = (
            datetime.datetime.now() + datetime.timedelta(minutes=30)
        ).strftime("%H:%M")

        result = self.order_service.update_estimated_delivery_time(
            order.order_id,
            new_delivery_time,
            self.test_delivery_agent.user_id
        )

        self.assertFalse(result)

    def test_update_delivery_time_to_negative_value(self):
        """Test updating delivery time to a negative value"""
        # Create an order
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Assign to delivery agent
        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.data_store.orders[order.order_id] = order

        # Try to update with negative time
        with self.assertRaises(ValueError):
            self.order_service.update_estimated_delivery_time(
                order.order_id,
                "-30",
                self.test_delivery_agent.user_id
            )



    def test_toggle_duty_when_working_on_order(self):
        """Test toggling duty status when working on an order"""
        # Create an order and assign to agent
        order = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        order.delivery_agent_id = self.test_delivery_agent.user_id
        self.test_delivery_agent.current_order = order.order_id
        self.test_delivery_agent.is_on_duty = True
        self.data_store.orders[order.order_id] = order

        # Try to toggle duty
        result = self.order_service.toggle_delivery_agent_duty(
            self.test_delivery_agent.user_id
        )

        self.assertFalse(result)
        self.assertTrue(self.test_delivery_agent.is_on_duty)

    def test_view_delivery_history_when_no_orders_delivered(self):
        """Test viewing delivery history when no orders have been delivered"""
        # Ensure agent has no completed deliveries
        self.test_delivery_agent.completed_deliveries = []

        # Get delivery history
        history = self.order_service.get_delivery_agent_history(
            self.test_delivery_agent.user_id
        )

        self.assertEqual(len(history), 0)
        self.assertIsInstance(history, list)

    ###############################
    # CUSTOMER EDGE CASE TESTS
    ###############################

    def test_place_same_order_twice(self):
        """Test placing the same order twice creates separate entries"""
        # Define order items
        order_items = [{"item_id": self.test_menu_item.item_id, "quantity": 1}]

        # Place first order
        order1 = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            order_items,
            OrderType.DELIVERY
        )

        # Place second identical order
        order2 = self.order_service.create_order(
            self.test_customer.user_id,
            self.test_restaurant.restaurant_id,
            order_items,
            OrderType.DELIVERY
        )

        # Check that two distinct orders were created
        self.assertNotEqual(order1.order_id, order2.order_id)
        self.assertIn(order1.order_id, self.data_store.orders)
        self.assertIn(order2.order_id, self.data_store.orders)

    def test_check_nonexistent_order_status(self):
        """Test checking the status of a non-existent order"""
        with self.assertRaises(ValueError):
            self.order_service.get_order_details(
                "non-existent-order",
                self.test_customer.user_id
            )

    def test_check_order_status_of_another_user(self):
        """Test checking order status of an order belonging to another user"""
        # Create an order for another customer
        order = self.order_service.create_order(
            self.another_customer.user_id,
            self.test_restaurant.restaurant_id,
            [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
            OrderType.DELIVERY
        )

        # Try to check status with different user
        with self.assertRaises(PermissionError):
            self.order_service.get_order_details(
                order.order_id,
                self.test_customer.user_id
            )

    def test_place_order_with_no_items(self):
        """Test placing an order with no items"""
        with self.assertRaises(ValueError):
            self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [],  # Empty items list
                OrderType.DELIVERY
            )

    def test_place_order_with_invalid_item(self):
        """Test placing an order with invalid item selection"""
        with self.assertRaises(ValueError):
            self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": "non-existent-item", "quantity": 1}],
                OrderType.DELIVERY
            )

    def test_place_order_with_no_delivery_agents_available(self):
        """Test placing a delivery order when no agents are available"""
        # Set all delivery agents as off-duty and unavailable
        for agent in self.data_store.delivery_agents.values():
            agent.is_on_duty = False  # ✅ Ensure the agent is not on duty
            agent.available = False   # ✅ Ensure the agent is marked unavailable

        # Try to place delivery order (should raise ValueError)
        with self.assertRaises(ValueError):
            self.order_service.create_order(
                self.test_customer.user_id,
                self.test_restaurant.restaurant_id,
                [{"item_id": self.test_menu_item.item_id, "quantity": 1}],
                OrderType.DELIVERY  # Specifically a delivery order
            )



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

