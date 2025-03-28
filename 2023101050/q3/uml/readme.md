# 📌 E-Marketing System - Class Descriptions

## 1️⃣ Product Class
### 📌 Description
The `Product` class represents an individual product available in the e-market. It contains details such as product name, description, price, and stock quantity.

### 📌 State (Attributes)
| Attribute      | Type    | Description |
|---------------|--------|-------------|
| `product_id`  | `str`  | Unique identifier for the product. |
| `name`        | `str`  | Name of the product. |
| `description` | `str`  | Brief description of the product. |
| `price`       | `float` | Price of the product. |
| `category_id` | `str`  | ID of the category the product belongs to. |
| `stock_quantity` | `int` | Available stock for the product. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `__init__(self, product_id, name, description, price, category_id, stock_quantity)` | Initializes the product with given details. |

---

## 2️⃣ CartItem Class
### 📌 Description
The `CartItem` class represents an item added to a shopping cart, containing the product and its quantity.

### 📌 State (Attributes)
| Attribute  | Type   | Description |
|------------|--------|-------------|
| `product`  | `Product` | The product associated with this cart item. |
| `quantity` | `int`  | The number of units of this product in the cart. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `__init__(self, product, quantity)` | Initializes a cart item with a specific product and quantity. |
| `get_subtotal(self, user: User) -> float` | Calculates the total price for this item, considering user discounts. |

---

## 3️⃣ ShoppingCart Class
### 📌 Description
The `ShoppingCart` class manages the list of items a user intends to purchase.

### 📌 State (Attributes)
| Attribute  | Type   | Description |
|------------|--------|-------------|
| `user`  | `User` | The owner of the shopping cart. |
| `items` | `List[CartItem]` | A list of items added to the cart. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `add_item(self, product: Product, quantity: int)` | Adds a product to the shopping cart. |
| `remove_item(self, product_id: str)` | Removes an item from the cart. |
| `update_quantity(self, product_id: str, quantity: int)` | Updates the quantity of a specific item. |
| `get_total(self) -> float` | Computes the total cost of all items in the cart. |

---

## 4️⃣ User Class (Base Class)
### 📌 Description
The `User` class is a base class representing both **individual customers** and **retail stores**.

### 📌 State (Attributes)
| Attribute  | Type   | Description |
|------------|--------|-------------|
| `user_id`  | `str` | Unique identifier for the user. |
| `name`     | `str` | Name of the user. |
| `email`    | `str` | User's email address. |
| `address`  | `str` | User's physical address. |
| `phone`    | `str` | Contact phone number. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `__init__(self, user_id, name, email, address, phone)` | Initializes a user with the given attributes. |
| `get_discount_rate(self) -> float` | Returns the discount rate applicable to the user. |

---

## 5️⃣ IndividualCustomer Class (Inherits from User)
### 📌 Description
The `IndividualCustomer` class represents a regular customer and extends the `User` class.

### 📌 Additional State
| Attribute        | Type   | Description |
|-----------------|--------|-------------|
| `loyalty_points` | `int` | Accumulated loyalty points for discounts. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `get_discount_rate(self) -> float` | Returns a discount based on loyalty points. |

---

## 6️⃣ RetailStore Class (Inherits from User)
### 📌 Description
The `RetailStore` class represents a business that purchases products in bulk and qualifies for special discounts.

### 📌 Additional State
| Attribute               | Type   | Description |
|-------------------------|--------|-------------|
| `business_license`      | `str`  | Unique business registration number. |
| `monthly_purchase_volume` | `float` | Total monthly purchase amount. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `get_discount_rate(self) -> float` | Returns a bulk discount based on monthly purchase volume. |

---

## 7️⃣ Order Class
### 📌 Description
The `Order` class represents a confirmed purchase made by a user.

### 📌 State (Attributes)
| Attribute  | Type   | Description |
|------------|--------|-------------|
| `order_id`  | `str` | Unique order identifier. |
| `user`  | `User` | The customer who placed the order. |
| `items` | `List[CartItem]` | A list of purchased items. |
| `delivery_method` | `str` | Type of delivery selected. |
| `delivery_address` | `str` | Shipping address. |
| `status` | `str` | Current status of the order. |
| `order_date` | `datetime` | Date and time of order placement. |
| `total_amount` | `float` | Final order cost after discounts. |

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `update_status(self, new_status: str)` | Updates the status of the order. |

---

## 8️⃣ OrderService Class
### 📌 Description
Handles order processing, shipping, and delivery updates.

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `mark_order_as_shipped(self, order_id: str) -> bool` | Marks an order as "shipped". |
| `mark_order_as_delivered(self, order_id: str) -> bool` | Marks an order as "delivered". |

---

## 9️⃣ DataStore Class
### 📌 Description
Manages data storage and retrieval for users, products, and orders.

### 📌 Behavior (Methods)
| Method  | Description |
|---------|-------------|
| `update_order(self, order_id: str, order_data: dict)` | Saves order updates to the database. |

---

## 📌 Summary of System Design
- **User types (`User`)**:
  - `IndividualCustomer`: Uses **loyalty points** for discounts.
  - `RetailStore`: Gets **bulk order discounts**.
- **Order Processing (`OrderService`)**:
  - Handles **shipping & delivery updates**.
- **Shopping (`ShoppingCart`, `CartItem`)**:
  - Manages items in the **user's cart** before checkout.
- **Data Persistence (`DataStore`)**:
  - Stores and retrieves **users, orders, and carts**.

---

## 🚀 Next Steps
- Add this markdown file to your `README.md`.
- Use it to document your **system architecture** for new developers.
- If needed, I can refine explanations or improve formatting.

Let me know how else I can help! 😊
