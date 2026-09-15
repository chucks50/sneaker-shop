import { apiFetch } from './client';

export function getProducts() {
  return apiFetch('/api/products');
}

export function getProductById(id) {
  return apiFetch(`/api/products/${id}`);
}
