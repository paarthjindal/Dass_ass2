# Basic set Up
- Make a accounts of the customers(Sign Up).
- Add the chefs and Delivery boys.

# Basic Test Case
## Customer
- Login by the customer by the Signup credentials
- Make a Home delivery order.
- Make a Takeaway Order.
- View all orders by the customer, that is order history.

## Manager/owner
- Login as the manager.
- View All orders.
- Add a delivery agent.
- Remove a delivery Agent.
- Add a chef.
- Remove a chef.
- Update Menu: Add a item, Remove a item,view menu.
- view staff profiles with further details.

## Chef
- Login as the chef.
- View current orders
- Mark order as complete
- Update order preparation time
- Toggle duty status
- View order history

## Delivery Boy
- View current order
- Mark order as delivered
- Update delivery time
- Toggle duty status
- View delivery history

# Edge cases

## Manager
- Add a delivery agent with already existing ID.
- Remove a delivery agent which dont exist.
- Add a item which already exist.
- Remove a item which doesnt exist.
- View profile of Delivery boy that doesn't exist.
- View profile of Delivery boy that is removed.


## Delivery Boy
- View current order and then mark one of the orders as delivered and then check wheather it removed from their or not.
- View current order and then update order delivery time and then check wheather it removed from their or not.
- Mark the order delivered which doesnt exist.
- Mark the order delivered which is already delivered.
- Update order delivery time for the order which doesnt exist.
- Update order delivery time for the order which is already finished.
- Update order delivery time to a negative value.
- Mark a order delivered when its in the "In Kitchen" phase.
- Toggle duty when already working on an order.

## Customer 
- Place a same order twice and it should make them separate entry.
- Check order status of the order which doesnt exist. 
- Check order status of the order which belongs to some other user.