import pytest
import sys
import os
# Add the parent directory to the Python path to import the main application
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.cli import (
    DollmartEMarket, OrderStatus, IndividualCustomer, RetailStore, ShoppingCart,
    Product, CartItem, DataStore, OrderService, UserService, ProductService
)

@pytest.fixture
def setup_emarket():
    """Fixture to set up the e-market system before each test."""
    emarket = DollmartEMarket()
    return emarket


# ----- Basic Setup Tests -----
def test_register_individual(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Alice", "alice@example.com", "123 St", "1234567890")
    assert user is not None
    assert user.name == "Alice"

def test_register_retail_store(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("RetailCorp", "contact@retail.com", "Market St", "9876543210", "LIC123", 5000)
    assert user is not None
    assert user.name == "RetailCorp"

def test_register_manager(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    assert user is not None
    assert user.name == "ManagerCorp"
    assert user.is_manager == True

def test_login_valid_user(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Bob", "bob@example.com", "456 Road", "1122334455")
    assert emarket.login(user.user_id) == True

def test_login_invalid_user(setup_emarket):
    emarket = setup_emarket
    assert emarket.login("invalid_id") == False


# ----- Shopping Cart Tests -----
def test_add_product_to_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Eve", "eve@example.com", "789 Lane", "9988776655")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Laptop", "High-end laptop", 1200.00, "cat2", 10)
    assert emarket.add_to_cart(product.product_id, 1) == True

def test_add_product_insufficient_stock(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Charlie", "charlie@example.com", "999 Blvd", "2233445566")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("TV", "Smart TV", 500.00, "cat2", 2)
    assert emarket.add_to_cart(product.product_id, 5) == False

def test_view_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("David", "david@example.com", "444 Street", "5566778899")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Phone", "Smartphone", 800.00, "cat2", 20)
    emarket.add_to_cart(product.product_id, 2)

    cart = emarket.view_cart()
    assert len(cart["items"]) == 1
    assert cart["items"][0]["name"] == "Phone"
    assert cart["total"] > 0

def test_remove_item_from_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Emily", "emily@example.com", "555 Lane", "6677889900")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Tablet", "Android tablet", 300.00, "cat2", 15)
    emarket.add_to_cart(product.product_id, 1)

    assert emarket.shopping_cart.remove_from_cart(product.product_id) == True
    cart = emarket.view_cart()
    assert len(cart["items"]) == 0

def test_update_cart_quantity(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Frank", "frank@example.com", "123 Avenue", "7766554433")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Monitor", "HD Monitor", 200.00, "cat2", 5)
    emarket.add_to_cart(product.product_id, 1)

    assert emarket.update_cart_item(product.product_id, 3) == True
    cart = emarket.view_cart()
    assert cart["items"][0]["quantity"] == 3

def test_clear_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("George", "george@example.com", "789 Boulevard", "9988665544")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Keyboard", "Mechanical Keyboard", 70.00, "cat2", 10)
    emarket.add_to_cart(product.product_id, 2)

    emarket.shopping_cart.clear()
    cart = emarket.view_cart()
    assert len(cart["items"]) == 0


# ----- Checkout and Orders -----
def test_successful_checkout(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Hannah", "hannah@example.com", "456 Plaza", "1122446688")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Camera", "DSLR Camera", 900.00, "cat2", 10)
    emarket.add_to_cart(product.product_id, 1)

    result = emarket.checkout("standard", "456 Plaza")
    assert result["success"] == True
    assert result["order_id"] is not None

def test_checkout_empty_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Ivy", "ivy@example.com", "555 Plaza", "9998887777")
    emarket.login(user.user_id)

    result = emarket.checkout("standard", "555 Plaza")
    assert result["success"] == False
    assert result["message"] == "Cart is empty or user not logged in"

def test_apply_valid_coupon(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Jake", "jake@example.com", "789 Avenue", "1122334455")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Mouse", "Wireless Mouse", 50.00, "cat2", 10)
    emarket.add_to_cart(product.product_id, 1)

    # Create a coupon
    coupon = emarket.order_service.generate_coupon(user)
    result = emarket.checkout("standard", "789 Avenue", coupon.code)
    assert result["success"] == True
    assert result["discount_applied"] > 0

def test_apply_invalid_coupon(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Katie", "katie@example.com", "123 Lane", "9988776655")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Speaker", "Bluetooth Speaker", 100.00, "cat2", 10)
    emarket.add_to_cart(product.product_id, 1)

    result = emarket.checkout("standard", "123 Lane", "INVALIDCODE")
    assert result["success"] == True
    assert result["discount_applied"] == 0.0


# ----- Edge Cases -----
def test_search_non_existent_product(setup_emarket):
    emarket = setup_emarket
    results = emarket.search_products("NonExistentItem")
    assert len(results) == 0

def test_add_product_with_negative_quantity(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Liam", "liam@example.com", "456 Plaza", "1122446688")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Camera", "DSLR Camera", 900.00, "cat2", 10)
    assert emarket.add_to_cart(product.product_id, -3) == False

def test_update_cart_negative_quantity(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Mia", "mia@example.com", "555 Plaza", "9998887777")
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Speaker", "Bluetooth speaker", 100.00, "cat2", 10)
    emarket.add_to_cart(product.product_id, 2)

    assert emarket.update_cart_item(product.product_id, -1) == False

def test_remove_non_existent_item(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Noah", "noah@example.com", "789 Avenue", "1122334455")
    emarket.login(user.user_id)

    assert emarket.shopping_cart.remove_from_cart("invalid_product_id") == False

def test_view_empty_cart(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_individual("Olivia", "olivia@example.com", "123 Lane", "9988776655")
    emarket.login(user.user_id)

    cart = emarket.view_cart()
    assert len(cart["items"]) == 0
    assert cart["total"] == 0.0


# ----- Manager Tests -----
def test_manager_add_product(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    assert emarket.add_product("Keyboard", "Mechanical Keyboard", 70.00, "cat2", 10) == True

def test_manager_edit_product(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Gaming Mouse", "RGB gaming mouse", 80.00, "cat2", 10)
    product.stock_quantity = 30
    assert emarket.product_service.update_product_stock(product.product_id, 20) == True

def test_manager_remove_product(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    product = emarket.product_service.create_product("Monitor", "HD Monitor", 200.00, "cat2", 5)
    assert emarket.delete_product(product.product_id) == True

def test_manager_remove_non_existent_product(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    assert emarket.delete_product("invalid_product_id") == False

def test_manager_add_product_without_name(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    assert emarket.add_product("", "Mechanical Keyboard", 70.00, "cat2", 10) == False

def test_manager_add_product_without_price(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    assert emarket.add_product("Keyboard", "Mechanical Keyboard", 0.0, "cat2", 10) == False

def test_manager_add_product_without_category(setup_emarket):
    emarket = setup_emarket
    user = emarket.register_retail_store("ManagerCorp", "manager@retail.com", "Manager St", "1122334455", "LIC456", 10000, is_manager=True)
    emarket.login(user.user_id)

    assert emarket.add_product("Keyboard", "Mechanical Keyboard", 70.00, "", 10) == False


if __name__ == "__main__":
    pytest.main(["-v", "--color=yes"])