import { Link } from 'react-router-dom';

const STATUS_LABELS = { pending: 'Pending', paid: 'Paid', shipped: 'Shipped' };

export default function OrderCard({ order }) {
  return (
    <Link to={`/orders/${order.id}`} className="order-card">
      <span>{new Date(order.created_at).toLocaleDateString()}</span>
      <span>&euro;{order.total.toFixed(2)}</span>
      <span className={`status-badge status-${order.status}`}>
        {STATUS_LABELS[order.status] ?? order.status}
      </span>
    </Link>
  );
}