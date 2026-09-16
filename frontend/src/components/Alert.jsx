export default function Alert({ type = 'error', children }) {
  return <p className={`alert alert-${type}`}>{children}</p>;
}