import { apiFetch } from './client';

function normalizeOrder(order) {
  return {
    ...order,
    total: order.total_amount,
    items: (order.items ?? []).map((item) => ({
      ...item,
      price: item.unit_price,
      product_name: item.product_name_snapshot,
      variant_label: `Variant #${item.variant_id}`,
    })),
  };
}

export function checkout(payload) {
  return apiFetch('/api/orders/checkout', { method: 'POST', body: JSON.stringify(payload) }).then(normalizeOrder);
}

export function getOrders() {
  return apiFetch('/api/orders').then((orders) => orders.map(normalizeOrder));
}

export function getOrderById(id) {
  return apiFetch(`/api/orders/${id}`).then(normalizeOrder);
}