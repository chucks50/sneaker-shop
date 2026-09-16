import { useState } from 'react';
import { createAddress } from '../api/addresses';
import Alert from './Alert';

export default function AddressForm({ onSuccess }) {
  const [form, setForm] = useState({ street: '', city: '', postalCode: '', country: '' });
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState(null);

  function handleChange(e) {
    setForm({ ...form, [e.target.name]: e.target.value });
  }

  async function handleSubmit(e) {
    e.preventDefault();
    setStatus('submitting');
    setErrorMessage(null);

    try {
      const address = await createAddress({
        street: form.street,
        city: form.city,
        postal_code: form.postalCode,
        country: form.country,
      });
      setStatus('success');
      onSuccess(address.id);
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.message);
    }
  }

  return (
    <form onSubmit={handleSubmit} className="address-form">
      <label>Street <input name="street" value={form.street} onChange={handleChange} required /></label>
      <label>City <input name="city" value={form.city} onChange={handleChange} required /></label>
      <label>Postal code <input name="postalCode" value={form.postalCode} onChange={handleChange} required /></label>
      <label>Country <input name="country" value={form.country} onChange={handleChange} required /></label>

      {errorMessage && <Alert type="error">{errorMessage}</Alert>}
      {status === 'success' && <Alert type="success">Address saved.</Alert>}

      <button type="submit" disabled={status === 'submitting'}>
        {status === 'submitting' ? 'Saving…' : 'Save address'}
      </button>
    </form>
  );
}