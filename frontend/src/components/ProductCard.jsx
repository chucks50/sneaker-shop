import {Link} from 'react-router-dom';


export default function ProductCard({ product }) {
  return (<article className="product-card">
      <img src={product.image_url} alt={product.name} loading="lazy" />
      <h3>{product.name}</h3>
      <p className="brand">{product.brand}</p>
      <p className="price">&euro;{product.price.toFixed(2)}</p>
      <p className="short-desc">{product.short_description}</p>
      <Link to={`/products/${product.id}`}>
        <button>View details</button>
      </Link>
    </article>);
}
