import { useEffect, useState } from 'react';
import { useAuth } from '../state/auth';
import Alert from '../components/Alert';
import {
  createProduct,
  deactivateProduct,
  getAdminProducts,
  updateProduct,
} from '../api/products';

const emptyForm = {
  name: '',
  slug: '',
  brand: '',
  description: '',
  base_price: '',
  category_slug: 'lifestyle',
  image_url: '',
  featured: false,
  size: '42',
  color: 'Black / White',
  stock_quantity: 0,
};

export default function AdminProductsPage() {
  const { isAdmin } = useAuth();
  const [products, setProducts] = useState([]);
  const [form, setForm] = useState(emptyForm);
  const [editingId, setEditingId] = useState(null);
  const [status, setStatus] = useState('loading');
  const [message, setMessage] = useState(null);

  async function loadProducts() {
    setStatus('loading');
    try {
      setProducts(await getAdminProducts());
      setStatus('ready');
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
      setStatus('error');
    }
  }

  useEffect(() => {
    if (isAdmin) loadProducts();
  }, [isAdmin]);

  function handleChange(event) {
    const { name, value, type, checked } = event.target;
    setForm((current) => ({ ...current, [name]: type === 'checkbox' ? checked : value }));
  }

  function startEdit(product) {
    const variant = product.variants[0] ?? {};
    setEditingId(product.id);
    setForm({
      ...emptyForm,
      name: product.name,
      slug: product.slug,
      brand: product.brand,
      description: product.description,
      base_price: product.base_price,
      category_slug: product.category?.slug ?? 'lifestyle',
      image_url: product.image_url,
      featured: product.featured,
      size: variant.size ?? '42',
      color: variant.color ?? 'Black / White',
      stock_quantity: variant.stock_quantity ?? 0,
    });
    setMessage(null);
  }

  function resetForm() {
    setEditingId(null);
    setForm(emptyForm);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    setMessage(null);
    const payload = {
      name: form.name,
      slug: form.slug,
      brand: form.brand,
      description: form.description,
      base_price: Number(form.base_price),
      category_slug: form.category_slug,
      image_url: form.image_url,
      featured: form.featured,
      variants: [{
        size: form.size,
        color: form.color,
        stock_quantity: Number(form.stock_quantity),
      }],
    };

    try {
      if (editingId) {
        await updateProduct(editingId, payload);
      } else {
        await createProduct(payload);
      }
      resetForm();
      setMessage({ type: 'success', text: editingId ? 'Product updated.' : 'Product created.' });
      await loadProducts();
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    }
  }

  async function handleDeactivate(product) {
    if (!window.confirm(`Hide ${product.name} from the shop?`)) return;
    try {
      await deactivateProduct(product.id);
      setMessage({ type: 'success', text: 'Product hidden from the shop.' });
      await loadProducts();
    } catch (error) {
      setMessage({ type: 'error', text: error.message });
    }
  }

  if (!isAdmin) return <Alert type="error">Admin access required.</Alert>;
  if (status === 'loading') return <p className="loading-state">Loading product management…</p>;

  return (
    <div className="admin-products">
      <div className="shop-heading">
        <div>
          <p className="eyebrow">Store operations</p>
          <h1>Manage products</h1>
        </div>
      </div>

      {message && <Alert type={message.type}>{message.text}</Alert>}

      <form className="product-admin-form" onSubmit={handleSubmit}>
        <h2>{editingId ? 'Edit product' : 'Add product'}</h2>
        <label>Name<input name="name" value={form.name} onChange={handleChange} required /></label>
        <label>Slug<input name="slug" value={form.slug} onChange={handleChange} required /></label>
        <label>Brand<input name="brand" value={form.brand} onChange={handleChange} required /></label>
        <label>Description<textarea name="description" value={form.description} onChange={handleChange} required /></label>
        <label>Price<input name="base_price" type="number" min="0" step="0.01" value={form.base_price} onChange={handleChange} required /></label>
        <label>Category
          <select name="category_slug" value={form.category_slug} onChange={handleChange}>
            <option value="lifestyle">Lifestyle</option>
            <option value="running">Running</option>
            <option value="basketball">Basketball</option>
            <option value="trail">Trail</option>
          </select>
        </label>
        <label>Image URL<input name="image_url" type="url" value={form.image_url} onChange={handleChange} /></label>
        <label>Size<input name="size" value={form.size} onChange={handleChange} required /></label>
        <label>Color<input name="color" value={form.color} onChange={handleChange} required /></label>
        <label>Stock<input name="stock_quantity" type="number" min="0" value={form.stock_quantity} onChange={handleChange} required /></label>
        <label className="checkbox-label"><input name="featured" type="checkbox" checked={form.featured} onChange={handleChange} /> Featured product</label>
        <div className="admin-form-actions">
          <button type="submit">{editingId ? 'Save changes' : 'Add product'}</button>
          {editingId && <button type="button" onClick={resetForm}>Cancel</button>}
        </div>
      </form>

      <div className="admin-product-list">
        {products.map((product) => (
          <article className={`admin-product-row ${product.is_active ? '' : 'inactive'}`} key={product.id}>
            <div>
              <strong>{product.name}</strong>
              <span>{product.brand} · €{product.base_price.toFixed(2)} · {product.is_active ? 'Visible' : 'Hidden'}</span>
            </div>
            <div className="admin-row-actions">
              <button onClick={() => startEdit(product)}>Edit</button>
              {product.is_active && <button onClick={() => handleDeactivate(product)}>Hide</button>}
            </div>
          </article>
        ))}
      </div>
    </div>
  );
}
