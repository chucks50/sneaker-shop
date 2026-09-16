import { apiFetch } from './client';
import { getProductById } from './products';

export function getCart() {
  return apiFetch('/api/cart').then(async (items) => {
    const products = await Promise.all(items.map((item) => getProductById(item.product_id)));

    return items.map((item, index) => {
      const product = products[index];
      const variant = product.variants.find((candidate) => candidate.id === item.variant_id);

      return {
        ...item,
        product_name: product.name,
        variant_label: variant?.label ?? `Variant #${item.variant_id}`,
        price: variant?.price ?? product.price,
        image_url: product.image_url,
      };
    });
  });
}

export function addCartItem(payload) {
  return apiFetch('/api/cart/items', { method: 'POST', body: JSON.stringify(payload) });
}

export function updateCartItem(itemId, quantity) {
  return apiFetch(`/api/cart/items/${itemId}`, { method: 'PUT', body: JSON.stringify({ quantity }) });
}

export function removeCartItem(itemId) {
  return apiFetch(`/api/cart/items/${itemId}`, { method: 'DELETE' });
}