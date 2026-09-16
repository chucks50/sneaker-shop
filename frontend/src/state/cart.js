import { createContext, createElement, useContext, useState, useCallback } from 'react';
import { getCart, addCartItem, updateCartItem, removeCartItem } from '../api/cart';

const CartContext = createContext(null);

export function CartProvider({ children }) {
  const [items, setItems] = useState([]);
  const [status, setStatus] = useState('idle'); // idle | loading | ready | error
  const [updatingItemId, setUpdatingItemId] = useState(null);

  const refresh = useCallback(async () => {
    setStatus((currentStatus) => (currentStatus === 'ready' ? currentStatus : 'loading'));
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
    setUpdatingItemId(`new-${productId}-${variantId}`);
    try {
      await addCartItem({ product_id: productId, variant_id: variantId, quantity });
      await refresh();
    } finally {
      setUpdatingItemId(null);
    }
  }

  async function increaseQuantity(item) {
    setUpdatingItemId(item.id);
    try {
      await updateCartItem(item.id, item.quantity + 1);
      await refresh();
    } finally {
      setUpdatingItemId(null);
    }
  }

  async function decreaseQuantity(item) {
    if (item.quantity <= 1) return removeItem(item);
    setUpdatingItemId(item.id);
    try {
      await updateCartItem(item.id, item.quantity - 1);
      await refresh();
    } finally {
      setUpdatingItemId(null);
    }
  }

  async function removeItem(item) {
    setUpdatingItemId(item.id);
    try {
      await removeCartItem(item.id);
      await refresh();
    } finally {
      setUpdatingItemId(null);
    }
  }

  return {
    items,
    status,
    itemCount,
    total,
    updatingItemId,
    refresh,
    addItem,
    increaseQuantity,
    decreaseQuantity,
    removeItem,
  };
}