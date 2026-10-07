# Laravel API: local setup and Render deployment

The Laravel API lives in backend/laravel/. The Python backend remains at backend/ for rollback while production verification is pending. The API maps to the existing ten-table PostgreSQL schema and exposes the same paths and JSON structures used by the React app.

## Local development

Prerequisites: PHP 8.3+, Composer, and PHP extensions openssl, mbstring, pdo_pgsql, bcmath, and curl. For SQLite-only feature tests, enable pdo_sqlite.

~~~powershell
cd C:\laragon\www\mijn_webshop\backend\laravel
Copy-Item .env.example .env
composer install
php artisan key:generate
~~~

Set .env values for DB_CONNECTION=pgsql, DB_HOST, DB_PORT, DB_DATABASE, DB_USERNAME, and DB_PASSWORD, or use DATABASE_URL. Generate JWT_SECRET_KEY separately with:

~~~powershell
php -r "echo bin2hex(random_bytes(32)), PHP_EOL;"
~~~

Set ADMIN_EMAIL, FRONTEND_URL=http://localhost:5173, and local CORS origins. For password reset email, use a local SMTP catcher such as Mailpit (MAIL_HOST=127.0.0.1, MAIL_PORT=1025, MAIL_MAILER=smtp). Set Stripe test credentials only when testing checkout.

Compare the target PostgreSQL catalog with app/Models and database/migrations/2026_10_07_000000_create_legacy_store_tables.php before any migration. The migration only creates absent tables and its down() intentionally drops nothing. It does not alter partially matching existing tables. With a fresh local database, apply it using:

~~~powershell
php artisan migrate
php artisan serve --host 127.0.0.1 --port 8000
~~~

Set the React build variable to VITE_API_URL=http://localhost:8000 (the existing frontend direct dev example currently uses port 8001). Start Vite at frontend/ with npm run dev -- --host 0.0.0.0.

## Render production service

Render does not provide a native PHP runtime. Create a Web Service with the Docker runtime, not a static site or Python service. Create or select the PostgreSQL service separately. When connecting an existing production database, use its internal URL from the same Render region and do not provision a second empty database by mistake.

For this repository, set:

- Repository: the existing mijn_webshop repository.
- Root Directory: backend/laravel.
- Dockerfile Path: Dockerfile.
- Docker build context: .
- Build command: leave blank; the Dockerfile runs composer install --no-dev --prefer-dist --no-interaction --optimize-autoloader.
- Start command: leave blank; the image starts start-laravel, which caches Laravel configuration/routes and starts Apache.
- Port: 10000 (PORT=10000); health check path: /health.
- Pre-deploy command: leave blank until the existing database schema has been compared and backed up. Never run migrations from normal container startup.

The image uses PHP 8.3 Apache with pdo_pgsql; Apache serves only Laravel public/ and listens on Render port 10000. Render terminates HTTPS and provides the public https://<service>.onrender.com URL.

### Render environment variables

Set these in the Web Service Environment page. Never commit their values.

| Variable | Production value |
|---|---|
| APP_NAME | Sneaker Shop API |
| APP_ENV | production |
| APP_KEY | Generate with php artisan key:generate --show; keep stable across deploys |
| APP_DEBUG | false |
| APP_URL | Public HTTPS Render service URL |
| LOG_CHANNEL | stderr |
| SESSION_DRIVER | file |
| CACHE_STORE | file |
| LOG_LEVEL | info |
| PORT | 10000 |
| DB_CONNECTION | pgsql |
| DATABASE_URL | Internal URL for the existing Render PostgreSQL database, same region |
| JWT_SECRET_KEY | Strong independent random secret of at least 32 characters; keep stable to preserve active tokens |
| ACCESS_TOKEN_EXPIRE_MINUTES | 30 unless intentionally changed |
| ADMIN_EMAIL | Exact admin account email |
| CORS_ALLOWED_ORIGINS | Exact production Netlify origin, e.g. https://sneaker-shop-ck.netlify.app |
| FRONTEND_URL | Exact production Netlify URL, no trailing slash |
| STRIPE_SECRET_KEY | Stripe test secret (sk_test_...) during verification |
| STRIPE_WEBHOOK_SECRET | Signing secret from the Stripe test webhook endpoint |
| STRIPE_CURRENCY | eur |
| STRIPE_PAYMENT_METHOD_CONFIGURATION | Optional Stripe configuration ID; leave unset if unused |
| MAIL_MAILER | smtp |
| MAIL_HOST, MAIL_PORT | SMTP provider host and port |
| MAIL_USERNAME, MAIL_PASSWORD | SMTP credentials, if required |
| MAIL_SCHEME | Optional SMTP scheme (for example, smtps) |
| MAIL_FROM_ADDRESS, MAIL_FROM_NAME | Verified sender identity |

The Stripe webhook endpoint is https://<service>.onrender.com/api/webhooks/stripe. Configure it in Stripe test mode for checkout.session.completed, checkout.session.async_payment_succeeded, checkout.session.expired, and checkout.session.async_payment_failed. The API uses EUR and never accepts prices from the browser. Keep test keys in place until a full successful/cancelled checkout and webhook flow is verified.

### Existing database rollout

1. Back up the current PostgreSQL database.
2. Compare its actual tables, types, nullability, constraints, indexes, and sequences with the SQLAlchemy model inventory and Laravel migration. The repository has no database dump or migration history, so this comparison cannot be performed from source alone.
3. Point Laravel at the same database and run read-only catalog inspection first.
4. Only after review, run php artisan migrate --force once. The included migration skips each existing table and only creates missing tables; it never drops/renames tables or changes columns. Verify IDs/sequences and foreign keys afterward.
5. Keep the old Render Python service available until the full API and Stripe workflows pass against the same data.

## Netlify frontend

Keep the existing React app. In Netlify, set the build environment variable VITE_API_URL to the new Render HTTPS service URL and keep VITE_ADMIN_EMAIL aligned with backend ADMIN_EMAIL. Trigger a new deploy because Vite embeds these variables at build time. Verify preflight/CORS, login, products, cart, and checkout against Laravel. The only React change is the password-reset instruction described above; all API modules and request contracts remain unchanged.

## Local verification status

The new Laravel routes, migration, and API compatibility tests are checked in. ResetPasswordPage.jsx changes its post-request instruction from server logs to email because Laravel sends reset tokens by SMTP. PHP syntax checks, in-memory SQLite migration, feature tests, and the existing Vite production build pass. Live PostgreSQL, real Stripe payments/webhook delivery, Render deployment, and Netlify deployment still require credentials and external services and are not verified here.