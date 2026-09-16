import { createContext, createElement, useContext, useState, useCallback } from 'react';
import { getCart, addCartItem, updateCartItem, removeCartItem } from '../api/cart';

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error

  const refresh = useCallback(async () => {
    setStatus('loading');
    try {
      const data = await getCart();
      setItems(data.items ?? data); // adjust if your /api/cart wraps items differently
      setStatus('ready');
    } catch {
      setStatus('error');
    }
  }, []);

  return createElement(CartContext.Provider, { value: { items, status, refresh } }, children);
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within a CartProvider');
  const { items, status, refresh } = ctx;

  const itemCount = items.reduce((sum, item) => sum + item.quantity, 0);
  const total = items.reduce((sum, item) => sum + item.price * item.quantity, 0);

  async function addItem({ productId, variantId, quantity = 1 }) {
    await addCartItem({ product_id: productId, variant_id: variantId, quantity });
    await refresh();
  }

  async function increaseQuantity(item) {
    await updateCartItem(item.id, item.quantity + 1);
    await refresh();
  }

  async function decreaseQuantity(item) {
    if (item.quantity <= 1) return removeItem(item);
    await updateCartItem(item.id, item.quantity - 1);
    await refresh();
  }

  async function removeItem(item) {
    await removeCartItem(item.id);
    await refresh();
  }

  return { items, status, itemCount, total, refresh, addItem, increaseQuantity, decreaseQuantity, removeItem };
}