import { apiFetch } from './client';

function normalizeProduct(product) {
  const primaryImage = product.images?.find((image) => image.is_primary) ?? product.images?.[0];

  return {
    ...product,
    price: product.base_price,
    image_url: primaryImage?.url ?? '',
    short_description: product.description,
    variants: (product.variants ?? []).map((variant) => ({
      ...variant,
      label: `${variant.size} / ${variant.color}`,
      stock: variant.stock_quantity,
      price: variant.price_override ?? product.base_price,
    })),
  };
}

export function getProducts() {
  return apiFetch('/api/products').then((products) => products.map(normalizeProduct));
}

export function getProductById(id) {
  return apiFetch(`/api/products/${id}`).then(normalizeProduct);
}
