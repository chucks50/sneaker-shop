import{ useEffect, useState } from 'react';
import { getProducts } from '../api/products';
import Alert from '../components/Alert';
import ProductCard from '../components/ProductCard';

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading'); // 'loading' | 'ready' | 'error'

  useEffect(() => {
    let cancelled = false;

    getProducts()
      .then((data) => {
        if (!cancelled) {
          setProducts(data);
          setStatus('ready');
        }
      })
      .catch(() => {
        if (!cancelled) setStatus('error');
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === 'loading') return <p className="loading-state">Loading products&hellip;</p>;
  if (status === 'error') return <Alert type="error">Couldn't load products. Try refreshing.</Alert>;
  if (products.length === 0) return <p className="empty-state">No products available right now.</p>;

  return (
    <div className="product-grid">
      {products.map((product) => (
        <ProductCard key={product.id} product={product} />
      ))}
    </div>
  );
}
