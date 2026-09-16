import{ useEffect, useState } from 'react';
import { getProducts } from '../api/products';
import Alert from '../components/Alert';
import ProductCard from '../components/ProductCard';

export default function HomePage() {
  const [products, setProducts] = useState([]);
  const [status, setStatus] = useState('loading'); // 'loading' | 'ready' | 'error'
  const [search, setSearch] = useState('');
  const [brand, setBrand] = useState('all');
  const [category, setCategory] = useState('all');
  const [sort, setSort] = useState('featured');

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

  const brands = [...new Set(products.map((product) => product.brand))].sort();
  const categories = [...new Set(products.map((product) => product.category?.name).filter(Boolean))].sort();
  const visibleProducts = products
    .filter((product) => {
      const query = search.trim().toLowerCase();
      const searchableText = `${product.name} ${product.brand} ${product.description}`.toLowerCase();
      return (
        (!query || searchableText.includes(query)) &&
        (brand === 'all' || product.brand === brand) &&
        (category === 'all' || product.category?.name === category)
      );
    })
    .sort((first, second) => {
      if (sort === 'price-low') return first.price - second.price;
      if (sort === 'price-high') return second.price - first.price;
      return Number(second.featured) - Number(first.featured);
    });

  return (
    <div className="shop-page">
      <div className="shop-heading">
        <div>
          <p className="eyebrow">The everyday rotation</p>
          <h1>Find your next pair</h1>
        </div>
        <p>{visibleProducts.length} of {products.length} products</p>
      </div>

      <div className="product-filters" aria-label="Product filters">
        <label>
          Search
          <input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search sneakers" />
        </label>
        <label>
          Brand
          <select value={brand} onChange={(event) => setBrand(event.target.value)}>
            <option value="all">All brands</option>
            {brands.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
        <label>
          Category
          <select value={category} onChange={(event) => setCategory(event.target.value)}>
            <option value="all">All categories</option>
            {categories.map((option) => <option key={option} value={option}>{option}</option>)}
          </select>
        </label>
        <label>
          Sort
          <select value={sort} onChange={(event) => setSort(event.target.value)}>
            <option value="featured">Featured</option>
            <option value="price-low">Price: low to high</option>
            <option value="price-high">Price: high to low</option>
          </select>
        </label>
      </div>

      {visibleProducts.length === 0 ? (
        <p className="empty-state">No sneakers match those filters.</p>
      ) : (
        <div className="product-grid">
          {visibleProducts.map((product) => <ProductCard key={product.id} product={product} />)}
        </div>
      )}
    </div>
  );
}
