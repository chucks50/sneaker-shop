# FastAPI to Laravel 13 migration plan

## Audit findings

The repository contains a React 18/Vite frontend, a FastAPI/SQLAlchemy backend, PostgreSQL Docker configuration, and no Render or Netlify manifests. `backend/app/main.py` creates tables using `create_all`, seeds catalog data at startup, configures CORS, and implements all routes. `models.py`, `schemas.py`, `crud.py`, `auth.py`, `db.py`, and `config.py` hold database, validation, business logic, JWT/password, connection, and settings code. The Python implementation will remain intact during migration. The ignored root `.env` was not inspected. No live database dump or migration history is checked in, so production schema comparison remains necessary before migrations.

## API contract inventory

| Endpoint | Method | Purpose | Authentication |
|---|---|---|---|
| `/health` | GET | Health JSON | Public |
| `/` | GET | API identity JSON | Public |
| `/api/products` | GET | Active products (`skip`, `limit`) | Public |
| `/api/products/{product_id}` | GET | Product detail | Public |
| `/api/auth/register` | POST | Register user | Public |
| `/api/auth/login` | POST | Return JWT and user | Public |
| `/api/auth/forgot-password` | POST | Reset token issuance (currently logged to server console only) | Public |
| `/api/auth/reset-password` | POST | Change password with reset JWT | Public |
| `/api/auth/me` | GET | Current user | Bearer JWT |
| `/api/admin/products` | GET | Admin catalog | Admin email + JWT |
| `/api/admin/products` | POST | Create product | Admin email + JWT |
| `/api/admin/products/{product_id}` | PUT | Update product | Admin email + JWT |
| `/api/admin/products/{product_id}` | DELETE | Soft-deactivate product | Admin email + JWT |
| `/api/addresses` | POST | Create current user's address | Bearer JWT |
| `/api/addresses` | GET | List current user's addresses | Bearer JWT |
| `/api/cart` | GET | Current user's cart lines | Bearer JWT |
| `/api/cart/items` | POST | Add/increment cart line; validate stock | Bearer JWT |
| `/api/cart/items/{item_id}` | PUT | Set cart quantity | Bearer JWT |
| `/api/cart/items/{item_id}` | DELETE | Remove cart line | Bearer JWT |
| `/api/checkout/create-session` | POST | Create pending order and Stripe Checkout session | Bearer JWT |
| `/api/checkout/session-status` | GET | Retrieve owned session status | Bearer JWT |
| `/api/webhooks/stripe` | POST | Verify Stripe signature and update order | Stripe signature |
| `/api/orders` | GET | Current user's orders | Bearer JWT |
| `/api/orders/{order_id}` | GET | Current user's order detail | Bearer JWT |
| `/api/orders/{order_id}/status` | PATCH | Admin status update; cannot set paid | Admin email + JWT |

The frontend API modules are `frontend/src/api/{client,auth,products,cart,orders,addresses}.js`. `client.js` uses `VITE_API_URL`, JSON requests, local-storage bearer JWT, and reads errors from `detail`. Auth state persists JWT in localStorage and calls `/api/auth/me` on startup. Login shape is `{access_token, token_type, user}`; successful responses are direct JSON, not a `{data: ...}` envelope. Frontend source changes should not be necessary if Laravel preserves this contract.

## Database inventory from SQLAlchemy models

Tables: `users`, `addresses`, `categories`, `products`, `product_variants`, `product_images`, `reviews`, `cart_items`, `orders`, `order_items`.

| Table | Fields, nullability, constraints, defaults | Relationships |
|---|---|---|
| `users` | `id` integer PK; `email` varchar(255) required unique/indexed; `password_hash` varchar(255) required; `first_name` varchar(100), `last_name` varchar(100) required; `phone` varchar(50) nullable; `is_active` boolean default true | has addresses, cart, orders, reviews |
| `addresses` | `id` PK; `user_id` FK required; `street` varchar(255), `city` varchar(100), `postal_code` varchar(20), `country` varchar(100) required; `is_default` boolean default false | belongs to user; orders reference it |
| `categories` | `id` PK; `name` varchar(100) required; `slug` varchar(120) required unique | has products |
| `products` | `id` PK; `name` varchar(200), `slug` varchar(200) unique, `brand` varchar(100), `description` text, `base_price` float, `category_id` FK required; `featured` false/default, `is_active` true/default | belongs to category; has variants/images/reviews/cart/order items |
| `product_variants` | `id` PK; `product_id` FK; `size` varchar(20), `color` varchar(50), unique required `sku` varchar(100); `stock_quantity` integer default 0; nullable `price_override` float | belongs to product; referenced by cart/order items |
| `product_images` | `id` PK; `product_id` FK; required `url` varchar(500); nullable `alt_text` varchar(200); `is_primary` false/default | belongs to product |
| `reviews` | `id` PK; `product_id`, `user_id` FKs; required `rating` integer, `created_at` datetime; nullable `comment` text | belongs to product/user |
| `cart_items` | `id` PK; `user_id`, `product_id`, `variant_id` FKs; `quantity` integer required default 1 | belongs to user/product/variant |
| `orders` | `id` PK; `user_id`, `address_id` FKs; required `status`, `payment_status` varchar(50) default pending; required float `subtotal`, `shipping_fee` (default 0), `total_amount`; required `payment_method` varchar(50); nullable unique `stripe_checkout_session_id` varchar(255), nullable `stripe_payment_intent_id` varchar(255); required `created_at` datetime | belongs to user/address; has items |
| `order_items` | `id` PK; `order_id`, `product_id`, `variant_id` FKs; required integer `quantity`, float `unit_price`, varchar(200) `product_name_snapshot` | belongs to order/product/variant |

No enum types, composite indexes, explicit FK delete rules, or automatic `updated_at` fields are declared. User email, category slug, product slug, variant SKU, and Stripe session ID have uniqueness constraints. Only orders and reviews declare timestamps. These details reflect models, not a live PostgreSQL catalog. Existing `create_all` cannot safely evolve a production schema.

## Existing business and deployment behavior

- Admin authorization compares authenticated email with `ADMIN_EMAIL`.
- Passwords use bcrypt. HS256 access JWTs use `sub` user ID and 30-minute default expiry; reset JWTs expire after 15 minutes and include `purpose=password_reset`.
- Cart add checks positive quantity, product/variant relationship, and stock. Cart updates check positivity; checkout validates active products, stock, and address ownership. Checkout prices come from DB values and snapshot to order lines.
- Checkout uses Stripe EUR, creates a hosted session, redirects to `{FRONTEND_URL}/success?session_id=...` or `/cancel`, and returns `{order_id, session_id, checkout_url, payment_status}`. Webhooks verify signature, order/user/session, amount, currency, and idempotently mark paid/failed.
- Stripe checkout has stock/cart lifecycle gaps: checkout does not decrement stock; webhook clears the user's cart on success. Preserve wire behavior while reviewing these transaction edges.
- CORS defaults to localhost:5173, 127.0.0.1:5173, and `https://sneaker-shop-ck.netlify.app`, configurable by `CORS_ALLOWED_ORIGINS`.
- `docker-compose.yml` runs PostgreSQL 15 and Python. GitHub Actions builds React and compiles Python. Frontend `VITE_API_URL` examples are localhost:8001 (direct) and :8000 (Docker). Backend settings include `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_EMAIL`, `CORS_ALLOWED_ORIGINS`, `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `FRONTEND_URL`, `STRIPE_CURRENCY`, `STRIPE_PAYMENT_METHOD_CONFIGURATION`, and access-token expiry.
- No Render/Netlify config is checked in. PHP 8.5.1 and Laragon Composer are available. Active PHP CLI lacks `pdo_pgsql`; local PostgreSQL is unverified. Live DB/Stripe/hosting flows cannot yet be claimed.

## Python to Laravel map

| FastAPI/Python | Laravel |
|---|---|
| Routes/dependencies | `routes/api.php`, controllers, auth/admin middleware |
| SQLAlchemy | Explicit Eloquent models for legacy tables |
| Pydantic | Laravel validation and compatible JSON responses |
| Settings | Laravel `.env` and config |
| HS256 JWT | JWT service/middleware retaining bearer format and claims |
| Passlib bcrypt | Laravel `Hash` with legacy bcrypt compatibility |
| Stripe Python SDK | Official `stripe/stripe-php` |
| CORS middleware | Explicit Laravel CORS origins |
| FastAPI exceptions | JSON errors with `detail` for frontend compatibility |

## Staged implementation

1. Keep Python under `backend/`; create Laravel 13 under `backend/laravel/` with Composer dependencies and Render instructions.
2. Bind all ten tables explicitly. Do not drop, rename, or alter production tables. Require live schema comparison before applying migrations.
3. Implement every endpoint with current paths, methods, JSON shape, auth, ownership checks, database-derived prices, and signed Stripe flow.
4. Verify PHP syntax, isolated database behavior where available, and frontend build. Mark unavailable live integrations unverified.
5. Recheck frontend compatibility. Prefer Netlify `VITE_API_URL` without React source edits. Do not alter external hosting settings here.
6. Keep Python until successful production end-to-end verification.
