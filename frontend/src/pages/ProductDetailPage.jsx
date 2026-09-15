import { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { getProductById } from '../api/products';
import { useCart } from '../state/cart';

export default function ProductDetailPage() {
  const { productId } = useParams();
  const navigate = useNavigate();
  const { addItem } = useCart();

  const [product, setProduct] = useState(null);
  const [status, setStatus] = useState('loading');
  const [selectedVariantId, setSelectedVariantId] = useState(null);
  const [cartError, setCartError] = useState(null);
  const [justAdded, setJustAdded] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setStatus('loading');

    getProductById(productId)
      .then((data) => {
        if (cancelled) return;
        setProduct(data);
        setSelectedVariantId(data.variants?.[0]?.id ?? null);
        setStatus('ready');
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });

    return () => {
      cancelled = true;
    };
  }, [productId]);

  if (status === 'loading') return <p className="loading-state">Loading product&hellip;</p>;
  if (status === 'error') return <p className="error-state">Product not found.</p>;

  const selectedVariant = product.variants.find((v) => v.id === selectedVariantId);

  function handleAddToCart() {
    setCartError(null);
    setJustAdded(false);

    if (!selectedVariant || selectedVariant.stock <= 0) {
      setCartError('This variant is out of stock.');
      return;
    }

    addItem({
      productId: product.id,
      variantId: selectedVariant.id,
      name: product.name,
      price: product.price,
      image_url: product.image_url,
      quantity: 1,
    });

    setJustAdded(true);
  }

  return (
    <div className="product-detail">
      <img src={product.image_url} alt={product.name} />

      <div className="product-detail-info">
        <h1>{product.name}</h1>
        <p className="brand">{product.brand}</p>
        <p className="price">&euro;{product.price.toFixed(2)}</p>
        <p className="description">{product.description}</p>

        <fieldset className="variant-picker">
          <legend>Choose a variant</legend>
          {product.variants.map((variant) => (
            <label key={variant.id} className={variant.stock <= 0 ? 'disabled' : undefined}>
              <input
                type="radio"
                name="variant"
                value={variant.id}
                checked={selectedVariantId === variant.id}
                disabled={variant.stock <= 0}
                onChange={() => {
                  setSelectedVariantId(variant.id);
                  setCartError(null);
                  setJustAdded(false);
                }}
              />
              {variant.label}
              {variant.stock <= 0 && ' (out of stock)'}
            </label>
          ))}
        </fieldset>

        {cartError && <p className="error-state">{cartError}</p>}
        {justAdded && <p className="success-state">Added to cart.</p>}

        <button onClick={handleAddToCart}>Add to cart</button>
        {justAdded && <button onClick={() => navigate('/cart')}>Go to cart</button>}
      </div>
    </div>
  );
}