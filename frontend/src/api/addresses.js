import { apiFetch } from './client';

export function createAddress(payload) {
  return apiFetch('/api/addresses', { method: 'POST', body: JSON.stringify(payload) });
}