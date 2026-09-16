// src/pages/OrderConfirmationPage.jsx
import { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getOrderById } from '../api/orders';
import Alert from '../components/Alert';

export default function OrderConfirmationPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    getOrderById(orderId)
      .then((data) => { setOrder(data); setStatus('ready'); })
      .catch(() => setStatus('error'));
  }, [orderId]);

  if (status === 'loading') return <p className="loading-state">Loading order&hellip;</p>;
  if (status === 'error') return <Alert type="error">Couldn't find that order.</Alert>;

  return (
    <div className="order-confirmation">
      <h1>Thanks for your order!</h1>
      <p>Order #{order.id}</p>
      <p>Total: &euro;{order.total.toFixed(2)}</p>
      <p>Status: {order.status}</p>

      <div className="confirmation-actions">
        <Link to="/"><button>Continue shopping</button></Link>
        <Link to="/orders"><button>View orders</button></Link>
      </div>
    </div>
  );
}