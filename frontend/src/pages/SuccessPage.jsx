import { Link } from 'react-router-dom';

export default function SuccessPage() {
  return (
    <div className="empty-state">
      <h1>Payment successful</h1>
      <p>Your payment has been received, but the final order status is confirmed by Stripe webhook processing.</p>
      <p>You can continue shopping or view your orders.</p>
      <div className="confirmation-actions">
        <Link to="/"><button>Continue shopping</button></Link>
        <Link to="/orders"><button>View orders</button></Link>
      </div>
    </div>
  );
}
