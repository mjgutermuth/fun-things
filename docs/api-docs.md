# Little Coffee Co API Documentation

A RESTful API for managing coffee orders with both synchronous and asynchronous processing patterns.

## Base URL
https://api.coffeeshop.com/v1

## Authentication
All requests require an API key in the header:
Authorization: Bearer your_api_key_here

## Order Management

### Create Order

Creates a new coffee order. Supports both synchronous and asynchronous processing modes.

**Endpoint:** `POST /orders`

**Request Body:**
```json
{
  "drink": "string",
  "size": "small|medium|large", 
  "location": "string",
  "customer_id": "string",
  "service": "counter|mobile",
  "special_instructions": "string (optional)"
}
```

Response (Synchronous - service: "counter"):

```json{
  "order_id": "abc123",
  "status": "completed",
  "drink": "large latte",
  "total": 4.50,
  "payment_status": "paid",
  "pickup_location": "counter 2",
  "completed_at": "2025-07-16T10:30:00Z"
}
```

Response (Asynchronous - service: "mobile"):

```json{
  "order_id": "def456",
  "status": "preparing",
  "drink": "large latte", 
  "estimated_time": "8 minutes",
  "created_at": "2025-07-16T10:30:00Z",
  "polling_url": "/orders/def456"
}
```

## Status Codes:

200 OK - Order completed immediately (counter service)
202 Accepted - Order accepted for processing (mobile service)
400 Bad Request - Invalid order data
401 Unauthorized - Missing or invalid API key

**Get Order Status**

Retrieves the current status of an order. Use this endpoint to poll for order completion.
Endpoint: GET /orders/{order_id}

Response:
```json{
  "order_id": "def456",
  "status": "preparing|ready|completed|cancelled",
  "drink": "large latte",
  "location": "downtown",
  "estimated_time": "5 minutes",
  "pickup_location": "counter 2 (when ready)",
  "created_at": "2025-07-16T10:30:00Z",
  "updated_at": "2025-07-16T10:33:00Z"
}
```

Status Values:

preparing - Order is being made
ready - Order is ready for pickup
completed - Order has been picked up
cancelled - Order was cancelled

Status Codes:

200 OK - Order found
404 Not Found - Order ID does not exist
401 Unauthorized - Missing or invalid API key

**Cancel Order**

Cancels an existing order if it hasn't been completed.

Endpoint: DELETE /orders/{order_id}
Response:

```json{
  "order_id": "def456", 
  "status": "cancelled",
  "refund_status": "processing",
  "cancelled_at": "2025-07-16T10:35:00Z"
}
```

Menu Management

**Get Menu**
Returns the current menu with available drinks and pricing.

Endpoint: GET /menu
Response:

```json{
  "categories": [
    {
      "name": "Coffee",
      "items": [
        {
          "id": "coffee_regular",
          "name": "Regular Coffee",
          "sizes": {
            "small": 2.50,
            "medium": 3.00, 
            "large": 3.50
          },
          "preparation_time": "2-3 minutes"
        },
        {
          "id": "latte",
          "name": "Latte",
          "sizes": {
            "small": 4.00,
            "medium": 4.50,
            "large": 5.00
          },
          "preparation_time": "5-8 minutes"
        }
      ]
    }
  ],
  "last_updated": "2025-07-16T08:00:00Z"
}
```

**Webhooks (Optional)**
For real-time order updates, you can register webhook endpoints that will receive notifications when order status changes.

**Register Webhook**
Endpoint: POST /webhooks
Request Body:
```json{
  "url": "https://your-app.com/webhook/orders",
  "events": ["order.ready", "order.completed", "order.cancelled"],
  "secret": "your_webhook_secret"
}
```

**Webhook Payload**
When an order status changes, we'll send a POST request to your webhook URL:
```json{
  "event": "order.ready",
  "order_id": "def456",
  "timestamp": "2025-07-16T10:38:00Z",
  "data": {
    "status": "ready",
    "pickup_location": "counter 2"
  }
}
```

**Error Handling**
All errors follow this format:
```json{
  "error": {
    "code": "INVALID_ORDER_DATA",
    "message": "The drink field is required",
    "details": {
      "field": "drink",
      "value": null
    }
  },
  "timestamp": "2025-07-16T10:30:00Z"
}
```

**Rate Limiting**
Standard tier: 100 requests per minute
Premium tier: 1000 requests per minute
Rate limit headers included in all responses:

X-RateLimit-Limit: Maximum requests per window
X-RateLimit-Remaining: Requests remaining in current window
X-RateLimit-Reset: Unix timestamp when window resets

## SDK Examples
JavaScript

```javascriptconst coffee = new CoffeeShopAPI('your_api_key');

// Async order
const order = await coffee.orders.create({
  drink: 'large latte',
  location: 'downtown',
  customer_id: 'user123',
  service: 'mobile'
});

// Poll for status
const status = await coffee.orders.getStatus(order.order_id);
Python
pythonfrom coffeeshop import CoffeeShopAPI

client = CoffeeShopAPI('your_api_key')

# Async order
order = client.orders.create({
    'drink': 'large latte',
    'location': 'downtown', 
    'customer_id': 'user123',
    'service': 'mobile'
})

# Poll for status  
status = client.orders.get_status(order['order_id'])
```

## Async Patterns Best Practices
Polling Strategy

Poll every 30 seconds for orders with estimated_time > 5 minutes
Poll every 10 seconds for orders with estimated_time < 5 minutes
Use exponential backoff if receiving 429 rate limit responses

## Error Recovery

Store order IDs locally for recovery
Implement retry logic with exponential backoff
Handle network timeouts gracefully

## User Experience

Show immediate confirmation when order is accepted
Display estimated time and allow status checking
Send push notifications when order status changes (via webhooks)
