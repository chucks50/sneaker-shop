import { apiFetch } from './client';

export function registerUser(payload) {
  return apiFetch('/api/auth/register', { method: 'POST', body: JSON.stringify(payload) });
}

export function loginUser(payload) {
  return apiFetch('/api/auth/login', { method: 'POST', body: JSON.stringify(payload) });
}

export function requestPasswordReset(payload) {
  return apiFetch('/api/auth/forgot-password', { method: 'POST', body: JSON.stringify(payload) });
}

export function resetPassword(payload) {
  return apiFetch('/api/auth/reset-password', { method: 'POST', body: JSON.stringify(payload) });
}

export function getCurrentUser() {
  return apiFetch('/api/auth/me');
}