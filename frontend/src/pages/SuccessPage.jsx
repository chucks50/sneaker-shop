import { useEffect, useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import Alert from '../components/Alert';
import { getCheckoutSessionStatus } from '../api/orders';

export default function SuccessPage() {
  const [params] = useSearchParams();
  const sessionId = params.get('session_id');
  const [status, setStatus] = useState('loading');
  const [errorMessage, setErrorMessage] = useState('');

  useEffect(() => {
    if (!sessionId) {
      setStatus('error');
      setErrorMessage('Stripe did not return a checkout session.');
      return;
    }

    getCheckoutSessionStatus(sessionId)
      .then((session) => setStatus(session.payment_status === 'paid' ? 'paid' : 'processing'))
      .catch((error) => {
        setStatus('error');
        setErrorMessage(error.message);
      });
  }, [sessionId]);

  return (
    <div className="empty-state">
      {status === 'loading' && <p>Confirming your payment with Stripe...</p>}
      {status === 'paid' && <><h1>Payment confirmed</h1><p>Stripe confirmed your payment.</p></>}
      {status === 'processing' && <><h1>Payment processing</h1><p>Stripe has not confirmed the payment yet. Your order will update when confirmation arrives.</p></>}
      {status === 'error' && <Alert type="error">{errorMessage}</Alert>}
      {status !== 'loading' && (
        <div className="confirmation-actions">
          <Link to="/"><button>Continue shopping</button></Link>
          <Link to="/orders"><button>View orders</button></Link>
        </div>
      )}
    </div>
  );
}
