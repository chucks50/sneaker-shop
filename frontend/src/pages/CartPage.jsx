import { useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useCart } from '../state/cart';
import Alert from '../components/Alert';
import CartItem from '../components/CartItem';

export default function CartPage() {
  const { items, status, total, refresh, increaseQuantity, decreaseQuantity, removeItem } = useCart();

  useEffect(() => {
    refresh();
  }, [refresh]);

  if (status === 'loading' || status === 'idle') return <p className="loading-state">Loading cart&hellip;</p>;
  if (status === 'error') return <Alert type="error">Couldn't load your cart.</Alert>;

  if (items.length === 0) {
    return (
      <div className="empty-state">
        <p>Your cart is empty.</p>
        <Link to="/"><button>Continue shopping</button></Link>
      </div>
    );
  }

  return (
    <div className="cart-page">
      {items.map((item) => (
        <CartItem
          key={item.id}
          item={item}
          onIncrease={() => increaseQuantity(item)}
          onDecrease={() => decreaseQuantity(item)}
          onRemove={() => removeItem(item)}
        />
      ))}

      <div className="cart-total"><strong>Total: &euro;{total.toFixed(2)}</strong></div>

      <Link to="/checkout">
        <button disabled={items.length === 0}>Checkout</button>
      </Link>
    </div>
  );
}