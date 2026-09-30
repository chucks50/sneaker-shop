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

export function createCheckoutSession(payload) {
  return apiFetch('/api/checkout/create-session', { method: 'POST', body: JSON.stringify(payload) });
}

export function getCheckoutSessionStatus(sessionId) {
  const query = new URLSearchParams({ session_id: sessionId });
  return apiFetch('/api/checkout/session-status?' + query.toString());
}

export function getOrders() {
  return apiFetch('/api/orders').then((orders) => orders.map(normalizeOrder));
}

export function getOrderById(id) {
  return apiFetch(`/api/orders/${id}`).then(normalizeOrder);
}