import { Link } from 'react-router-dom';

export default function CancelPage() {
  return (
    <div className="empty-state">
      <h1>Checkout cancelled</h1>
      <p>Your payment was not completed, and no charge was made.</p>
      <div className="confirmation-actions">
        <Link to="/cart"><button>Return to cart</button></Link>
        <Link to="/"><button>Continue shopping</button></Link>
      </div>
    </div>
  );
}
