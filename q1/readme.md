# Food Delivery System - Software Specifications & Use Cases

## **1. Software Requirements Specification (SRS)**

### **1.1 Functional Requirements**
- **Order Types**: Customers can place **Home Delivery** or **Takeaway** orders.
- **Order Tracking**: Customers can check the estimated time left for delivery.
- **Multiple Orders**: Customers can place multiple orders at once.
- **Fleet Management**: The system assigns delivery agents for home delivery orders.
- **Restaurant View**: The company manager can view order details from a restaurant’s perspective.
- **Persistence**: The system should maintain data across multiple instances (shared memory or database).

### **1.2 Non-Functional Requirements**
- **Scalability**: The system should support multiple customers placing orders simultaneously.
- **Reliability**: Ensures real-time order tracking and updates.
- **Security**: Restrict access to **restaurant view** for managers only.
- **Performance**: Response time should be low to avoid delays in order processing.

## **2. Use Cases**

| **Use Case** | **Actor** | **Description** |
|-------------|----------|----------------|
| **Place Order** | Customer | Customers place orders for Home Delivery or Takeaway. |
| **View Order Status** | Customer | Customers check the time left for delivery. |
| **Assign Delivery Agent** | System | Assigns an available delivery agent to an order. |
| **Update Order Status** | Delivery Agent | Marks order as picked up, on the way, or delivered. |
| **View All Orders** | Manager | The restaurant manager can see all ongoing orders. |
| **Manage Delivery Fleet** | System | Ensures fair assignment of agents to new orders. |

## **3. System Overview**
The system consists of three main actors:
1. **Customers**: Place orders and track their delivery.
2. **Delivery Agents**: Deliver home delivery orders and update their status.
3. **Manager**: Monitors all restaurant orders.

The system maintains **persistence** so that if the app is opened in multiple instances, they share the same order data.

---

## **4. Expected Workflow**
1. A **customer** places an order (Home Delivery or Takeaway).
2. If **Home Delivery**, an available **delivery agent** is assigned.
3. The order status updates in real-time (Pending → Out for Delivery → Delivered).
4. Customers can check the remaining time for their order.
5. The **restaurant manager** can monitor all orders.
6. The system ensures data consistency across multiple running instances.

---

This document outlines the **functional requirements, actors, use cases, and expected system workflow** to ensure a well-structured implementation of the food delivery system.
