import { apiFetch } from './client';

export function registerUser(payload) {
  return apiFetch('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

export function loginUser(payload) {
  return apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
}

export function getCurrentUser() {
  return apiFetch('/api/auth/me');
}