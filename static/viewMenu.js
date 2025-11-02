class OrderSystem {
  constructor() {
    this.order = [];
    this.orderList = document.getElementById("order-list");
    this.totalPriceEl = document.getElementById("total-price");
  }

  addToOrder(item) {
    const existing = this.order.find((i) => i.id === item.id);
    if (existing) {
      existing.quantity++;
    } else {
      this.order.push({ ...item, quantity: 1 });
    }
    this.updateOrderList();
  }

  updateOrderList() {
    this.orderList.innerHTML = "";
    let total = 0;
    this.order.forEach((item) => {
      total += item.price * item.quantity;
      const li = document.createElement("li");
      li.innerHTML = `
        <div class="flex justify-between items-center">
          <span>${item.name} (x${item.quantity})</span>
          <div class="flex items-center gap-2">
            <button onclick="orderSystem.decreaseQty(${item.id})" class="bg-gray-300 px-2 rounded">-</button>
            <button onclick="orderSystem.increaseQty(${item.id})" class="bg-gray-300 px-2 rounded">+</button>
            <span>Rs. ${item.price * item.quantity}</span>
          </div>
        </div>
      `;
      this.orderList.appendChild(li);
    });
    this.totalPriceEl.textContent = `Total: Rs. ${total}`;
  }

  increaseQty(id) {
    const item = this.order.find((i) => i.id === id);
    if (item) item.quantity++;
    this.updateOrderList();
  }

  decreaseQty(id) {
    const item = this.order.find((i) => i.id === id);
    if (item) {
      item.quantity--;
      if (item.quantity <= 0) {
        this.order = this.order.filter((i) => i.id !== id);
      }
    }
    this.updateOrderList();
  }

  clearOrder() {
    this.order = [];
    this.updateOrderList();
  }

  placeOrder() {
    if (this.order.length === 0) {
      alert("No items selected!");
      return;
    }
    const total = this.order.reduce((sum, item) => sum + item.price * item.quantity, 0);
    const orderData = { items: this.order, total };
    localStorage.setItem("latestOrder", JSON.stringify(orderData));
    alert("Order placed successfully!");
    this.clearOrder();
  }
}

const orderSystem = new OrderSystem();
