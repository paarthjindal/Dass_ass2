# Basic set Up
- Make a accounts of the customers (Individual and retail both).
- Add the Delivery boys.

# Basic Test Case
## Customer
- Login by the customer by the Signup credentials
- Add item in the cart by browsing the Products.
- Add item in the cart by searching them.
- View the cart.
- Update the quantity.
- Remove Item.
- Apply coupon.
- Make a order.
- Clear the cart.
- View all orders by the customer, that is order history.
- View all the coupons.

## Manager
- Add New Product
- Edit Product
- Remove Product
- List All Products
- View All orders.


# Edge Test Cases
## Customer
- Search a item with no matching string .
- Add a product with zero or negative quantity.
- Add a item that doesnt exist.
- View the cart when it is empty.
- Update quantity to negative or zero.
- Remove item that doesnt exist .
- Apply coupon that doesnt exist.

## Manager
- Add a item without name .
- Add a item Without Price.
- Add a item without category.
- Add the Product with the same name.
- Edit a product which doesnt exist.
- Remove a product which doesnt exist.
- Remove a delivery agent which doesnt exist.
