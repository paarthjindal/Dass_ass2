# **Food Delivery System - Software Specifications & Use Cases**

## **1. Software Specifications**

### **1.1 Functional Requirements**
- **Order Types**: Customers can place **Home Delivery** or **Takeaway** orders.
- **Order Tracking**: Customers can check the estimated time left for delivery.
- **Multiple Orders**: Customers can place multiple orders at once.
- **Fleet Management**: The system assigns delivery agents for home delivery orders.
- **Restaurant View**: The company manager can view order details from a restaurant’s perspective.
- **Persistence**: The system maintains data consistency across multiple instances (shared memory or database).
- **Delivery History**: Delivery agents can view their past deliveries.
- **Menu Management**: Managers can add, update, or remove menu items.
- **Order Validation**: The system checks for item availability and ensures valid inputs.
- **View Estimated Delivery Time**: Customers should be able to view the **time required/left for their order to be delivered**.

### **1.2 Non-Functional Requirements**
- **Scalability**: The system should support multiple customers placing orders simultaneously.
- **Reliability**: Ensures real-time order tracking and updates.
- **Security**: Restrict access to **restaurant view** for managers only.
- **Performance**: Response time should be low to avoid delays in order processing.
- **Error Handling**: Proper validation and error messages for incorrect inputs.
- **Concurrency Management**: Ensures multiple orders are processed efficiently.

## **2. Major Use Cases**

| **Use Case** | **Actor** | **Description** |
|-------------|----------|----------------|
| **Place Order** | Customer | Customers place orders for Home Delivery or Takeaway. |
| **View Order Status** | Customer | Customers check the time left for delivery. |
| **View Estimated Delivery Time** | Customer | Customers should be able to view the time required/left for their order to be delivered. |
| **Assign Delivery Agent** | System | Assigns an available delivery agent to an order. |
| **Update Order Status** | Delivery Agent | Marks order as picked up, on the way, or delivered. |
| **View All Orders** | Manager | The restaurant manager can see all ongoing orders. |
| **Manage Delivery Fleet** | System | Ensures fair assignment of agents to new orders. |
| **Modify Menu** | Manager | Managers can add, edit, or remove menu items. |
| **Update Estimated Delivery Time** | Delivery Agent | Delivery agents can update the expected delivery time. |
| **View Delivery History** | Delivery Agent | Agents can check a list of completed deliveries. |
| **Handle Invalid Orders** | System | Rejects invalid orders (e.g., items not available, negative price). |

## **3. System Overview**
The system consists of three main actors:
1. **Customers**: Place orders and track their delivery.
2. **Delivery Agents**: Deliver home delivery orders and update their status.
3. **Manager**: Monitors all restaurant orders and manages the menu.

The system ensures **persistence**, meaning data remains consistent across multiple running instances.

---

## **4. Expected Workflow**
1. A **customer** places an order (Home Delivery or Takeaway).
2. If **Home Delivery**, an available **delivery agent** is assigned.
3. The order status updates in real-time (Pending → Out for Delivery → Delivered).
4. Customers can check the **time required/left for their order to be delivered**.
5. The **restaurant manager** can monitor all orders and modify the menu.
6. Delivery agents update the estimated delivery time if needed.
7. The system ensures data consistency across multiple running instances.

---

This document provides a **business-level software specification**, detailing major use cases and the functional structure of the food delivery system.



# Instruction to run the testcase
- First navigate to testcase folder of q1
then just python test1.py