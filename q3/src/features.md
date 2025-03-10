# Dollmart E-Market System Design

## Core Classes

1. **User**: Base class for system users
   - **Customer** (extends User): For individual customers
   - **RetailStore** (extends User): For bulk-ordering retail stores

2. **Product**: Represents items for sale
   - Properties: id, name, description, category, base_price, inventory_count

3. **Category**: Hierarchical product organization

4. **Order**: Contains order information
   - Properties: id, customer, items, status, delivery_details, total_price

5. **Cart**: Shopping cart functionality
   - Methods: add_item, remove_item, update_quantity, calculate_total

6. **Discount**: Manages various discounts
   - **LoyaltyDiscount**: For regular customers
   - **BulkDiscount**: For retail stores and large orders

7. **DeliveryService**: Handles delivery management
   - Properties: delivery_options, tracking_info, status

8. **DataStore**: Persistence layer for storing data in JSON format

9. **SearchEngine**: Handles product searching and filtering

10. **UserInterface**: CLI interface for the system

## Relationships

- A User can have one Cart and multiple Orders
- A Cart contains multiple Products
- An Order contains multiple Products and is associated with one DeliveryService
- Products belong to Categories
- Discounts can be applied to Orders or specific Products

## Key Workflows

1. **Customer Registration and Login**
   - Register as individual or retail store
   - Authentication and profile management

2. **Product Browsing and Searching**
   - Browse by category
   - Search by name, description, or attributes
   - Filter and sort results

3. **Shopping Cart Management**
   - Add/remove products
   - Update quantities
   - Calculate totals with applicable discounts

4. **Checkout Process**
   - Review cart
   - Apply discounts and coupons
   - Select delivery options
   - Confirm payment

5. **Order Management**
   - View order history
   - Track order status
   - Process returns

6. **Loyalty Program**
   - Track purchase history
   - Generate discount coupons based on purchase volume/frequency

7. **Delivery Management**
   - Select delivery options
   - Track delivery status
   - Handle delivery issues