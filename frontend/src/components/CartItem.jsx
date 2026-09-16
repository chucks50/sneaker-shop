export default function CartItem({ item, isUpdating, onIncrease, onDecrease, onRemove }) {
  return (
    <div className="cart-item">
      <img src={item.image_url} alt={item.product_name} />
      <div className="cart-item-info">
        <p className="name">{item.product_name}</p>
        <p className="variant">{item.variant_label}</p>
      </div>
      <div className="quantity-controls">
        <button onClick={onDecrease} disabled={isUpdating} aria-label="Decrease quantity">-</button>
        <span>{item.quantity}</span>
        <button onClick={onIncrease} disabled={isUpdating} aria-label="Increase quantity">+</button>
      </div>
      <p className="item-total">&euro;{(item.price * item.quantity).toFixed(2)}</p>
      <button onClick={onRemove} disabled={isUpdating} className="remove-btn">
        {isUpdating ? 'Updating…' : 'Remove'}
      </button>
    </div>
  );
}   