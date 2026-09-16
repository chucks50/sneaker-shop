import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useCart } from '../state/cart';
import AddressForm from '../components/AddressForm';
import Alert from '../components/Alert';
import { checkout } from '../api/orders';
import { getAddresses } from '../api/addresses';

const PAYMENT_METHODS = [
  { id: 'ideal', label: 'iDEAL' },
  { id: 'card', label: 'Credit card' },
];

export default function CheckoutPage() {
  const { items, total, refresh } = useCart();
  const navigate = useNavigate();

  const [addressId, setAddressId] = useState(null);
  const [paymentMethod, setPaymentMethod] = useState(PAYMENT_METHODS[0].id);
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState(null);
  const [addresses, setAddresses] = useState([]);
  const [showNewAddress, setShowNewAddress] = useState(false);

  useEffect(() => {
    getAddresses()
      .then((data) => {
        setAddresses(data);
        if (data.length > 0) setAddressId(data[0].id);
        else setShowNewAddress(true);
      })
      .catch((err) => setErrorMessage(err.message));
  }, []);

  async function handlePlaceOrder() {
    setStatus('submitting');
    setErrorMessage(null);

    try {
      const order = await checkout({ address_id: addressId, payment_method: paymentMethod });
      await refresh(); // cart should now be empty server-side after checkout
      navigate(`/order-confirmation/${order.id}`);
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.message);
    }
  }

  if (items.length === 0) {
    return <p className="empty-state">Your cart is empty — nothing to check out.</p>;
  }

  return (
    <div className="checkout-page">
      <section className="cart-summary">
        <h2>Order summary</h2>
        {items.map((item) => (
          <div key={item.id} className="summary-row">
            <span>{item.product_name} &times; {item.quantity}</span>
            <span>&euro;{(item.price * item.quantity).toFixed(2)}</span>
          </div>
        ))}
        <div className="summary-row total"><strong>Total: &euro;{total.toFixed(2)}</strong></div>
      </section>

      <section>
        <h2>Delivery address</h2>
        {addresses.length > 0 && (
          <div className="saved-addresses">
            {addresses.map((address) => (
              <label className="saved-address" key={address.id}>
                <input
                  type="radio"
                  name="address"
                  checked={!showNewAddress && addressId === address.id}
                  onChange={() => {
                    setAddressId(address.id);
                    setShowNewAddress(false);
                  }}
                />
                <span>{address.street}, {address.city} {address.postal_code}, {address.country}</span>
              </label>
            ))}
            <button type="button" onClick={() => { setShowNewAddress(true); setAddressId(null); }}>
              Use a new address
            </button>
          </div>
        )}
        {showNewAddress && <AddressForm onSuccess={(id) => { setAddressId(id); setShowNewAddress(false); }} />}
      </section>

      <section>
        <h2>Payment method</h2>
        {PAYMENT_METHODS.map((method) => (
          <label key={method.id}>
            <input
              type="radio"
              name="payment"
              checked={paymentMethod === method.id}
              onChange={() => setPaymentMethod(method.id)}
            />
            {method.label}
          </label>
        ))}
      </section>

      {errorMessage && <Alert type="error">{errorMessage}</Alert>}

      <button onClick={handlePlaceOrder} disabled={!addressId || status === 'submitting'}>
        {status === 'submitting' ? 'Placing order…' : 'Place order'}
      </button>
    </div>
  );
}