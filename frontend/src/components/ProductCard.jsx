import {Link} from 'react-router-dom';


export default function ProductCard({ product }) {
  const availableStock = (product.variants ?? []).reduce((total, variant) => total + variant.stock, 0);

  return (<article className="product-card">
      <img src={product.image_url} alt={product.name} loading="lazy" onError={(event) => { event.currentTarget.style.visibility = 'hidden'; }} />
      <h3>{product.name}</h3>
      <p className="brand">{product.brand}</p>
      <p className="price">&euro;{product.price.toFixed(2)}</p>
      <p className="short-desc">{product.short_description}</p>
      <p className={`stock-label ${availableStock > 0 ? 'in-stock' : 'sold-out'}`}>
        {availableStock > 0 ? 'In stock' : 'Sold out'}
      </p>
      <Link to={`/products/${product.id}`}>
        <button>View details</button>
      </Link>
    </article>);
}
