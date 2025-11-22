# Little Coffee Co API

## Async Order Processing

This API demonstrates asynchronous order processing patterns commonly used in high-traffic applications.

### Key Features
- Non-blocking order creation
- Real-time status polling
- Event-driven notifications
- Queue-based processing

### API Endpoints

#### Create Order (Async)
```http
POST /orders
Content-Type: application/json

{
  "drink": "large latte",
  "location": "downtown",
  "customer_id": "123",
  "service": "mobile"
}
