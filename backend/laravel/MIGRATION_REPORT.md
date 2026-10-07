# Laravel migration report

## Status

The Laravel replacement backend is implemented side by side with the existing FastAPI backend. It is not ready to be declared production-complete: live PostgreSQL schema compatibility, Stripe test payments/webhooks, and Render/Netlify deployments remain unverified. Keep the Python service available until those checks pass.

## 1. Python backend components mapped

The following existing files remain intact for rollback and have Laravel equivalents:

- app/main.py: routes, middleware, startup schema creation, demo seeding, CORS, Stripe Checkout and webhooks.
- app/models.py: the ten SQLAlchemy tables and relationships.
- app/schemas.py: request validation and response serialization.
- app/crud.py: catalog, user, address, cart, and order persistence.
- app/auth.py: bcrypt and HS256 access/reset JWT handling.
- app/db.py and app/config.py: database/session and environment configuration.
- requirements.txt and Dockerfile: Python runtime/dependency deployment configuration.

The Laravel service is in backend/laravel/. No Python files or data have been deleted.

## 2. Laravel components created

- Laravel 13 application with Composer lockfile and Stripe PHP SDK/JWT dependencies.
- routes/api.php with all existing /api routes, plus the existing / and /health paths.
- AuthController, CatalogController, AdminController, StoreController.
- Eloquent models for all ten legacy tables and relationships.
- HS256 JWT service and JWT/admin middleware.
- CORS, PostgreSQL URL, Stripe, SMTP, and API JSON error configuration.
- Guarded schema migration, Dockerfile, startup script, .env.example, and Render deployment guide.
- Feature tests covering API compatibility and core access rules.

## 3. Database

The database has not been connected or changed. SQLAlchemy metadata declares these tables: users, addresses, categories, products, product_variants, product_images, reviews, cart_items, orders, order_items.

The Laravel migration creates a table only if it is absent. It never drops or renames a table and its down() intentionally performs no destructive rollback. It cannot repair partially matching tables. The only schema comparison currently available is source metadata; a live PostgreSQL catalog check and backup are required before applying the migration. The new migration ledger table is the only addition when all ten tables already exist.

## 4. API

| Endpoint | Method | Purpose | Authentication |
|---|---|---|---|
| / | GET | API identity | Public |
| /health | GET | Health status | Public |
| /api/products | GET | Active product list | Public |
| /api/products/{product_id} | GET | Product detail | Public |
| /api/auth/register | POST | Register user | Public |
| /api/auth/login | POST | Login and create JWT | Public |
| /api/auth/forgot-password | POST | Send a reset token by configured SMTP | Public |
| /api/auth/reset-password | POST | Reset password | Public |
| /api/auth/me | GET | Current user | Bearer JWT |
| /api/admin/products | GET | Admin product list | Admin email + JWT |
| /api/admin/products | POST | Create product | Admin email + JWT |
| /api/admin/products/{product_id} | PUT | Update product | Admin email + JWT |
| /api/admin/products/{product_id} | DELETE | Soft-deactivate product | Admin email + JWT |
| /api/addresses | POST | Create address | Bearer JWT |
| /api/addresses | GET | List addresses | Bearer JWT |
| /api/cart | GET | List cart lines | Bearer JWT |
| /api/cart/items | POST | Add cart line | Bearer JWT |
| /api/cart/items/{item_id} | PUT | Change cart quantity | Bearer JWT |
| /api/cart/items/{item_id} | DELETE | Remove cart line | Bearer JWT |
| /api/checkout/create-session | POST | Create order and Stripe session | Bearer JWT |
| /api/checkout/session-status | GET | Confirm owned Stripe session | Bearer JWT |
| /api/webhooks/stripe | POST | Process signed Stripe events | Stripe signature |
| /api/orders | GET | List current user's orders | Bearer JWT |
| /api/orders/{order_id} | GET | Get current user's order | Bearer JWT |
| /api/orders/{order_id}/status | PATCH | Admin status update; paid remains Stripe-controlled | Admin email + JWT |

The original backend has no admin-wide order list route; none was invented.

## 5. Frontend

One React file changed: frontend/src/pages/ResetPasswordPage.jsx now tells users to check email for the reset token instead of server logs, because Laravel sends reset tokens by SMTP and never logs them. All API modules and request contracts remain unchanged. Set Netlify VITE_API_URL to the new Laravel HTTPS URL, align VITE_ADMIN_EMAIL, and redeploy the frontend.

## 6. Stripe

Stripe calls now use the official Stripe PHP SDK (Composer package stripe/stripe-php). The existing Checkout flow is preserved: EUR line items use database prices, metadata ties a session to its order/user, success/cancel URLs match the current React routes, session status is user-scoped, and webhook signatures/amount/currency/order ownership are checked. Stripe keys are read from environment configuration; no live key is included in source.

Stripe SDK calls were exercised with a local fake HTTP client: Checkout session payload/prices, owned session status, signed success webhook, idempotent repeat, and expired session handling passed. Real Stripe test credentials, browser redirect, and Stripe-delivered webhook remain UNVERIFIED.

## 7. Render

Use a Docker Web Service, not a native PHP runtime or static site, with root directory backend/laravel, Dockerfile path Dockerfile, build context ., image port 10000, and health check /health. The Dockerfile installs PHP 8.3 Apache, pdo_pgsql and Composer dependencies; the startup command caches Laravel config/routes and runs Apache. A separate Render PostgreSQL service is needed, preferably the existing database's internal URL from the same region.

Exact steps and variables are in backend/laravel/DEPLOYMENT.md. Docker image build and Render deployment are UNVERIFIED because Docker Desktop's Linux daemon is not running and no Render account/service was accessed.

## 8. Netlify

Set VITE_API_URL to the new Laravel Render HTTPS origin and VITE_ADMIN_EMAIL to the configured admin email, then trigger a new build/deploy. No Netlify settings were changed from this workspace. Netlify communication and CORS are UNVERIFIED.

## 9. Environment variables

Required production settings: APP_ENV, APP_KEY, APP_DEBUG, APP_URL, LOG_CHANNEL, LOG_LEVEL, SESSION_DRIVER, CACHE_STORE, PORT, DB_CONNECTION, DATABASE_URL (or DB_HOST/DB_PORT/DB_DATABASE/DB_USERNAME/DB_PASSWORD), JWT_SECRET_KEY, ACCESS_TOKEN_EXPIRE_MINUTES, ADMIN_EMAIL, CORS_ALLOWED_ORIGINS, FRONTEND_URL, STRIPE_SECRET_KEY, STRIPE_WEBHOOK_SECRET, STRIPE_CURRENCY, optional STRIPE_PAYMENT_METHOD_CONFIGURATION, MAIL_MAILER, MAIL_HOST, MAIL_PORT, optional MAIL_USERNAME/MAIL_PASSWORD/MAIL_SCHEME, MAIL_FROM_ADDRESS, MAIL_FROM_NAME.

Use APP_ENV=production and APP_DEBUG=false on Render. Keep the Stripe key in test mode until verification. No secret values are listed in this report.

## 10. Testing

- PASS: PHP syntax checks for application, routes, and migration files.
- PASS: 23 Laravel API routes listed; root and health routes listed separately.
- PASS: guarded migration against fresh in-memory SQLite.
- PASS: 9 Laravel tests, 99 assertions. The API feature suite covers auth/current user, addresses, cart/stock, admin create/update/deactivate, password reset, mocked Stripe Checkout/session status, signed paid webhook/idempotency, expired checkout, and invalid webhook signature.
- PASS: local HTTP server responded to GET /health and GET / with expected JSON.
- PASS: React/Vite production build.
- PASS: Composer metadata/lock validation.
- UNVERIFIED: Existing PostgreSQL connection and live schema comparison (active CLI PHP lacks pdo_pgsql; production database is not accessible here).
- UNVERIFIED: Real Stripe test account, browser redirect, Stripe-hosted success/cancel browser flow, live webhook delivery, and production order state.
- UNVERIFIED: Render Docker build/deploy (Docker daemon unavailable) and Netlify deploy/CORS/authentication.
- UNVERIFIED: Complete browser flow from registration through paid order.

Security review: the Laravel implementation requires a configured JWT secret, uses Laravel password hashing, scopes user data, validates server-side prices, limits CORS to configured origins, and does not log reset tokens. The retained Python backend still contains its prior weak development JWT fallback and logs reset tokens; do not keep that service publicly active after cutover, and ensure production environment secrets are configured before any rollback service is exposed.