import { useEffect, useState } from 'react';
import { useParams } from 'react-router-dom';
import { getOrderById } from '../api/orders';
import Alert from '../components/Alert';

export default function OrderDetailPage() {
  const { orderId } = useParams();
  const [order, setOrder] = useState(null);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    getOrderById(orderId)
      .then((data) => { setOrder(data); setStatus('ready'); })
      .catch(() => setStatus('error'));
  }, [orderId]);

  if (status === 'loading') return <p className="loading-state">Loading order&hellip;</p>;
  if (status === 'error') return <Alert type="error">Couldn't load that order.</Alert>;

  return (
    <div className="order-detail">
      <h1>Order #{order.id}</h1>
      <p>Status: {order.status}</p>

      <table>
        <thead>
          <tr><th>Product</th><th>Variant</th><th>Qty</th><th>Total</th></tr>
        </thead>
        <tbody>
          {order.items.map((item) => (
            <tr key={item.id}>
              <td>{item.product_name}</td>
              <td>{item.variant_label}</td>
              <td>{item.quantity}</td>
              <td>&euro;{(item.price * item.quantity).toFixed(2)}</td>
            </tr>
          ))}
        </tbody>
      </table>

      <p><strong>Order total: &euro;{order.total.toFixed(2)}</strong></p>

      {order.address && (
        <address>
          {order.address.street}, {order.address.city} {order.address.postal_code}, {order.address.country}
        </address>
      )}
    </div>
  );
}