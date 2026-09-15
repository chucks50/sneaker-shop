import { createContext, useContext, useReducer } from 'react';

const CartContext = createContext(null);

function cartReducer(state, action) {
  switch (action.type) {
    case 'ADD_ITEM': {
      const { productId, variantId, name, price, image_url, quantity = 1 } = action.payload;
      const existing = state.items.find(
        (item) => item.productId === productId && item.variantId === variantId
      );

      if (existing) {
        return {
          ...state,
          items: state.items.map((item) =>
            item === existing ? { ...item, quantity: item.quantity + quantity } : item
          ),
        };
      }

      return {
        ...state,
        items: [...state.items, { productId, variantId, name, price, image_url, quantity }],
      };
    }

    case 'REMOVE_ITEM':
      return {
        ...state,
        items: state.items.filter(
          (item) =>
            !(item.productId === action.payload.productId && item.variantId === action.payload.variantId)
        ),
      };

    case 'UPDATE_QUANTITY':
      return {
        ...state,
        items: state.items.map((item) =>
          item.productId === action.payload.productId && item.variantId === action.payload.variantId
            ? { ...item, quantity: action.payload.quantity }
            : item
        ),
      };

    case 'CLEAR_CART':
      return { ...state, items: [] };

    default:
      return state;
  }
}

export function CartProvider({ children }) {
  const [state, dispatch] = useReducer(cartReducer, { items: [] });
  return <CartContext.Provider value={{ state, dispatch }}>{children}</CartContext.Provider>;
}

export function useCart() {
  const ctx = useContext(CartContext);
  if (!ctx) throw new Error('useCart must be used within a CartProvider');

  const { state, dispatch } = ctx;

  return {
    items: state.items,
    itemCount: state.items.reduce((sum, item) => sum + item.quantity, 0),
    total: state.items.reduce((sum, item) => sum + item.price * item.quantity, 0),
    addItem: (payload) => dispatch({ type: 'ADD_ITEM', payload }),
    removeItem: (productId, variantId) => dispatch({ type: 'REMOVE_ITEM', payload: { productId, variantId } }),
    updateQuantity: (productId, variantId, quantity) =>
      dispatch({ type: 'UPDATE_QUANTITY', payload: { productId, variantId, quantity } }),
    clearCart: () => dispatch({ type: 'CLEAR_CART' }),
  };
}
