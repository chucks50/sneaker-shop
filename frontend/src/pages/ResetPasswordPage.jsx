import { useState } from 'react';
import { Link } from 'react-router-dom';
import Alert from '../components/Alert';
import { requestPasswordReset, resetPassword } from '../api/auth';

export default function ResetPasswordPage() {
  const [email, setEmail] = useState('');
  const [token, setToken] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [status, setStatus] = useState('idle');
  const [errorMessage, setErrorMessage] = useState(null);
  const [successMessage, setSuccessMessage] = useState(null);

  async function handleRequestToken(e) {
    e.preventDefault();
    setStatus('submitting');
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const data = await requestPasswordReset({ email });
      setStatus('success');
      setSuccessMessage(
        `${data.message || 'If an account with that email exists, a password reset email has been sent.'} Check the server console for the demo reset token.`
      );
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.message);
    }
  }

  async function handleResetPassword(e) {
    e.preventDefault();
    setStatus('submitting');
    setErrorMessage(null);
    setSuccessMessage(null);

    try {
      const data = await resetPassword({ email, reset_token: token, new_password: newPassword });
      setStatus('success');
      setSuccessMessage(data.message || 'Password updated successfully.');
      setEmail('');
      setToken('');
      setNewPassword('');
    } catch (err) {
      setStatus('error');
      setErrorMessage(err.message);
    }
  }

  return (
    <div className="auth-form">
      <h1>Reset password</h1>

      <form onSubmit={handleRequestToken}>
        <label>Email
          <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        {errorMessage && <Alert type="error">{errorMessage}</Alert>}
        {successMessage && <Alert type="success">{successMessage}</Alert>}
        <button type="submit" disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Sending reset email…' : 'Request reset email'}
        </button>
      </form>

      <form onSubmit={handleResetPassword}>
        <label>Email
          <input type="email" name="email" value={email} onChange={(e) => setEmail(e.target.value)} required />
        </label>
        <label>Reset token
          <input name="resetToken" value={token} onChange={(e) => setToken(e.target.value)} required />
        </label>
        <label>New password
          <input type="password" name="newPassword" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} required minLength={8} />
        </label>
        {errorMessage && <Alert type="error">{errorMessage}</Alert>}
        {successMessage && <Alert type="success">{successMessage}</Alert>}
        <button type="submit" disabled={status === 'submitting'}>
          {status === 'submitting' ? 'Updating password…' : 'Update password'}
        </button>
      </form>

      <p><Link to="/login">Back to login</Link></p>
    </div>
  );
}
