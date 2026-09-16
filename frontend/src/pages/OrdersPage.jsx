import { useEffect, useState } from 'react';
import { getOrders } from '../api/orders';
import Alert from '../components/Alert';
import OrderCard from '../components/OrderCard';

export default function OrdersPage() {
  const [orders, setOrders] = useState([]);
  const [status, setStatus] = useState('loading');

  useEffect(() => {
    getOrders()
      .then((data) => { setOrders(data); setStatus('ready'); })
      .catch(() => setStatus('error'));
  }, []);

  if (status === 'loading') return <p className="loading-state">Loading orders&hellip;</p>;
  if (status === 'error') return <Alert type="error">Couldn't load your orders.</Alert>;
  if (orders.length === 0) return <p className="empty-state">You haven't placed any orders yet.</p>;

  return (
    <div className="orders-list">
      {orders.map((order) => <OrderCard key={order.id} order={order} />)}
    </div>
  );
}