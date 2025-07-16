// Coffee Shop Order Service
class OrderService {
  constructor() {
    this.orders = new Map();
    this.queue = [];
  }

  // Create new order - async operation
  async createOrder(orderData) {
    const orderId = this.generateOrderId();
    
    const order = {
      id: orderId,
      drink: orderData.drink,
      location: orderData.location,
      customerId: orderData.customer_id,
      status: 'preparing',
      createdAt: new Date(),
      estimatedTime: this.calculateEstimatedTime(orderData.drink)
    };

    this.orders.set(orderId, order);
    this.queue.push(order);
    
    // Start async processing
    this.processOrderAsync(orderId);
    
    return {
      order_id: orderId,
      status: 'preparing',
      estimated_time: order.estimatedTime
    };
  }

  // Get order status - for polling
  getOrderStatus(orderId) {
    const order = this.orders.get(orderId);
    if (!order) {
      throw new Error('Order not found');
    }

    return {
      order_id: orderId,
      status: order.status,
      pickup_location: order.status === 'ready' ? 'counter 2' : null,
      updated_at: order.updatedAt || order.createdAt
    };
  }

  // Async processing simulation
  async processOrderAsync(orderId) {
    const order = this.orders.get(orderId);
    
    // Simulate preparation time
    setTimeout(() => {
      order.status = 'ready';
      order.updatedAt = new Date();
      
      // Could trigger webhook or push notification here
      this.notifyCustomer(order);
    }, this.getProcessingTime(order.drink));
  }

  calculateEstimatedTime(drink) {
    const times = {
      'coffee': '3 minutes',
      'latte': '5 minutes',
      'large latte': '8 minutes',
      'cappuccino': '6 minutes'
    };
    return times[drink] || '5 minutes';
  }

  generateOrderId() {
    return 'abc' + Math.random().toString(36).substr(2, 6);
  }

  getProcessingTime(drink) {
    // Convert estimated time to milliseconds for demo
    return drink.includes('large') ? 8000 : 5000;
  }

  notifyCustomer(order) {
    console.log(`Order ${order.id} is ready for pickup!`);
    // In real app: send push notification, SMS, etc.
  }
}

module.exports = OrderService;
