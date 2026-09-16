# Sneaker Shop Portfolio Project

This repository is the project scaffold for a sneaker webshop portfolio project using:

- Frontend: React + Vite
- Backend: Python + FastAPI
- Database: PostgreSQL + SQLAlchemy
- Auth: JWT + bcrypt
- Infrastructure: Docker + Docker Compose
- CI/CD: GitHub Actions
- Deployment: Vercel/Netlify + Render/Railway

## Structure

- `frontend/` - React frontend application
- `backend/` - FastAPI backend application
- `docs/` - sprint planning and project notes
- `.github/workflows/` - CI/CD pipeline definitions
- `docker-compose.yml` - local development environment

## Sprint Plan

See the sprint documentation in `docs/sprints/`.

## Local Development

There are two ways to run the project locally:

1. Direct development with Python and Node.js. This is best while coding because
   Vite and FastAPI reload when files change.
2. Docker Compose. This is closer to the production setup because it runs the
   frontend, backend, and PostgreSQL in containers.

### Option A: Direct local development

#### 1. Check prerequisites

Install these tools first:

- Python 3.12 or newer
- Node.js and npm
- PostgreSQL, or use the PostgreSQL container from Option B

#### 2. Configure the backend environment

From PowerShell, run:

```powershell
cd C:\laragon\www\mijn_webshop
Copy-Item backend\.env.example backend\.env
```

Open `backend/.env` and set values suitable for your computer. For a local
PostgreSQL installation, the file can look like this:

```env
DATABASE_URL=postgresql+psycopg2://postgres:your-password@localhost:5432/sneaker_shop
JWT_SECRET_KEY=use-a-long-random-secret-here
ADMIN_EMAIL=admin@example.com
```

If you are using SQLite for quick backend testing, you can use:

```env
DATABASE_URL=sqlite:///./app.db
JWT_SECRET_KEY=use-a-long-random-secret-here
ADMIN_EMAIL=admin@example.com
```

#### 3. Install backend dependencies

```powershell
cd C:\laragon\www\mijn_webshop\backend
python -m pip install -r requirements.txt
```

#### 4. Start the backend

Use port `8001` for the direct local setup used by this project:

```powershell
cd C:\laragon\www\mijn_webshop\backend
python -m uvicorn app.main:app --reload --port 8001
```

Check that it works by opening:

```text
http://localhost:8001/health
```

You should see a JSON response saying that the backend is running.

#### 5. Configure the frontend environment

In a second terminal, run:

```powershell
cd C:\laragon\www\mijn_webshop
Copy-Item frontend\.env.example frontend\.env
```

The direct local frontend file should contain:

```env
VITE_API_URL=http://localhost:8001
VITE_ADMIN_EMAIL=admin@example.com
```

`VITE_API_URL` must point to the running FastAPI server. Vite reads variables
starting with `VITE_` when it builds or starts the frontend.

#### 6. Install and start the frontend

```powershell
cd C:\laragon\www\mijn_webshop\frontend
npm install
npm run dev -- --host 0.0.0.0
```

Open the website at:

```text
http://localhost:5173
```

If you change `frontend/.env`, restart Vite so it reads the new value.

#### 7. Test the admin area locally

The admin email is controlled by `ADMIN_EMAIL`. Register a user with that exact
email, log in, and open:

```text
http://localhost:5173/admin/products
```

From there, an admin can add products, edit products, or hide products from the
public catalog. Hiding is a soft delete: the database record remains available
for existing orders.

### Option B: Docker Compose

#### 1. Create the root environment file

Docker Compose reads its variables from a `.env` file in the project root:

```powershell
cd C:\laragon\www\mijn_webshop
```

Create `.env` with values like these:

```env
JWT_SECRET_KEY=replace-this-with-a-long-random-secret
POSTGRES_PASSWORD=replace-this-with-a-strong-database-password
ADMIN_EMAIL=admin@example.com
```

Do not commit this file. It contains secrets and is ignored by Git.

#### 2. Start all services

```powershell
docker compose up -d --build
```

Docker starts:

- Frontend at `http://localhost:5173`
- Backend at `http://localhost:8000`
- PostgreSQL on port `5432`

The frontend JavaScript runs in your browser, so its Docker API URL must be
`http://localhost:8000`. Do not use `http://backend:8000` for `VITE_API_URL`:
that service name works between containers but cannot be resolved by a browser
running on your host machine. Docker starts Vite with the `docker` mode, which
loads `frontend/.env.docker` and keeps this Docker URL separate from the direct
local-development URL in `frontend/.env`.

#### 3. Stop the services

```powershell
docker compose down
```

The PostgreSQL data remains in the `postgres_data` Docker volume. To remove the
database volume as well, use `docker compose down -v`.

### Environment variables explained

| Variable            | Used by              | Purpose                                                                                                                                 |
| ------------------- | -------------------- | --------------------------------------------------------------------------------------------------------------------------------------- |
| `JWT_SECRET_KEY`    | Backend              | Secret used to sign and verify login tokens. Use a long random value. Never expose it in frontend code.                                 |
| `POSTGRES_PASSWORD` | PostgreSQL/Docker    | Password for the PostgreSQL database user. Use a strong unique value.                                                                   |
| `DATABASE_URL`      | Backend              | Complete database connection address. It tells SQLAlchemy which database engine, host, port, database, and credentials to use.          |
| `ADMIN_EMAIL`       | Backend and frontend | Email address allowed to use product management. The backend enforces access; the frontend only uses this value to show the admin link. |
| `VITE_API_URL`      | Frontend             | Public base URL of the FastAPI API, for example `http://localhost:8001` locally or your deployed API URL in production.                 |

#### Important hosting note

Hosting providers do not use your local `.env` files automatically. Add these
variables in the provider's Environment Variables or Secrets section:

- Backend service: `JWT_SECRET_KEY`, `DATABASE_URL`, and `ADMIN_EMAIL`
- Database service: `POSTGRES_PASSWORD`, if the provider manages the database
- Frontend service: `VITE_API_URL` and `VITE_ADMIN_EMAIL`

Set frontend variables before the frontend build because Vite embeds `VITE_`
values into the generated JavaScript. Also update the backend CORS allowed
origin from `http://localhost:5173` to the real deployed frontend URL before
production use.

### Useful development commands

Run the backend tests:

```powershell
cd C:\laragon\www\mijn_webshop\backend
python -m pytest -q
```

Build the frontend for production:

```powershell
cd C:\laragon\www\mijn_webshop\frontend
npm run build
```

Preview the production frontend locally:

```powershell
npm run preview
```

## Project File Map

This section explains the important files in simple terms. The project has two
applications: the React frontend that the customer sees, and the FastAPI
backend that owns the data and business rules.

### Root files

| File or folder       | Purpose                                                              |
| -------------------- | -------------------------------------------------------------------- |
| `frontend/`          | React/Vite customer interface.                                       |
| `backend/`           | FastAPI server, database models, authentication, and business logic. |
| `docs/`              | Sprint plans and project documentation.                              |
| `docker-compose.yml` | Starts the frontend, backend, and PostgreSQL together.               |
| `README.md`          | Setup, deployment, and project explanation.                          |
| `.env`               | Local Docker secrets and URLs. Do not commit it.                     |

### Frontend map

#### Entry and routing

| File                      | Purpose                                                                                         |
| ------------------------- | ----------------------------------------------------------------------------------------------- |
| `frontend/index.html`     | The single HTML shell that loads the React application.                                         |
| `frontend/src/main.jsx`   | Starts React, imports the global CSS, and wraps the app with routing, auth, and cart providers. |
| `frontend/src/App.jsx`    | Defines the browser URLs and connects each URL to a page component.                             |
| `frontend/src/styles.css` | Global visual design, layout, colors, responsive rules, forms, cards, and alerts.               |
| `frontend/package.json`   | Lists frontend dependencies and commands such as `npm run dev` and `npm run build`.             |
| `frontend/vite.config.js` | Configures Vite, the frontend development and build tool.                                       |
| `frontend/.env.example`   | Template for frontend API and admin configuration.                                              |

#### API files

| File                            | Purpose                                                                                                                                          |
| ------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------ |
| `frontend/src/api/client.js`    | Shared `fetch` helper. It adds the API base URL, JSON headers, JWT header, and common error handling.                                            |
| `frontend/src/api/auth.js`      | Calls register, login, and current-user authentication endpoints.                                                                                |
| `frontend/src/api/products.js`  | Loads public products and calls admin create, edit, and deactivate endpoints. It also converts backend field names into frontend-friendly names. |
| `frontend/src/api/cart.js`      | Calls the server cart endpoints.                                                                                                                 |
| `frontend/src/api/orders.js`    | Calls checkout and order history/detail endpoints.                                                                                               |
| `frontend/src/api/addresses.js` | Creates and loads saved delivery addresses.                                                                                                      |

#### State files

| File                           | Purpose                                                                                                          |
| ------------------------------ | ---------------------------------------------------------------------------------------------------------------- |
| `frontend/src/state/auth.js`   | Keeps the logged-in user and JWT in React state and local storage. It checks `/api/auth/me` when the app starts. |
| `frontend/src/state/cart.js`   | Keeps the current cart visible, loads server cart data, and handles add, quantity, and remove actions.           |
| `frontend/src/state/orders.js` | Reserved state area for future shared order state. Current order pages load through the API directly.            |

#### Components and pages

| File or folder                                                | Purpose                                                                       |
| ------------------------------------------------------------- | ----------------------------------------------------------------------------- |
| `frontend/src/components/Header.jsx`                          | Main navigation, login links, logout button, and admin product link.          |
| `frontend/src/components/Footer.jsx`                          | Shared footer.                                                                |
| `frontend/src/components/ProtectedRoute.jsx`                  | Redirects users to login when a route needs authentication.                   |
| `frontend/src/components/Alert.jsx`                           | Reusable success and error message component.                                 |
| `frontend/src/components/ProductCard.jsx`                     | Displays one product in the catalog grid.                                     |
| `frontend/src/components/CartItem.jsx`                        | Displays one cart line and its quantity controls.                             |
| `frontend/src/components/AddressForm.jsx`                     | Creates a delivery address during checkout.                                   |
| `frontend/src/components/OrderCard.jsx`                       | Displays a short order summary.                                               |
| `frontend/src/pages/HomePage.jsx`                             | Product catalog, search, brand/category filters, and price sorting.           |
| `frontend/src/pages/ProductDetailPage.jsx`                    | Product image, description, variant selection, stock, and add-to-cart action. |
| `frontend/src/pages/LoginPage.jsx` and `RegisterPage.jsx`     | Customer authentication screens.                                              |
| `frontend/src/pages/CartPage.jsx`                             | Cart review and quantity management.                                          |
| `frontend/src/pages/CheckoutPage.jsx`                         | Saved/new address selection, payment method, order review, and checkout.      |
| `frontend/src/pages/OrderConfirmationPage.jsx`                | Shows the result of a successful checkout.                                    |
| `frontend/src/pages/OrdersPage.jsx` and `OrderDetailPage.jsx` | Order history and detailed order view.                                        |
| `frontend/src/pages/AdminProductsPage.jsx`                    | Admin-only add, edit, and hide product screen.                                |

### Backend map

| File                       | Purpose                                                                                     |
| -------------------------- | ------------------------------------------------------------------------------------------- |
| `backend/app/main.py`      | Creates the FastAPI app, seeds demo products, configures CORS, and defines the HTTP routes. |
| `backend/app/config.py`    | Reads environment variables and provides application settings.                              |
| `backend/app/db.py`        | Creates the SQLAlchemy database engine, sessions, and base model class.                     |
| `backend/app/models.py`    | Defines database tables such as users, products, variants, carts, addresses, and orders.    |
| `backend/app/schemas.py`   | Defines and validates the JSON shape accepted and returned by the API.                      |
| `backend/app/crud.py`      | Contains database operations and business logic for users, products, carts, and orders.     |
| `backend/app/auth.py`      | Hashes passwords, creates JWTs, and verifies JWTs.                                          |
| `backend/app/.env.example` | Template for database, JWT, and admin settings.                                             |
| `backend/Dockerfile`       | Builds the backend container and starts Uvicorn.                                            |
| `backend/requirements.txt` | Lists Python packages required by the backend.                                              |

### Backend tests

| File                                   | Purpose                                                         |
| -------------------------------------- | --------------------------------------------------------------- |
| `backend/tests/conftest.py`            | Creates a clean test database for each test and seeds products. |
| `backend/tests/test_products.py`       | Tests public product endpoints.                                 |
| `backend/tests/test_auth.py`           | Tests registration, login, JWT, and `/api/auth/me`.             |
| `backend/tests/test_cart.py`           | Tests adding, updating, and removing cart items.                |
| `backend/tests/test_orders.py`         | Tests checkout, stock validation, order details, and statuses.  |
| `backend/tests/test_admin_products.py` | Tests admin product create, edit, hide, and permission rules.   |

### How a request moves through the project

For example, when a customer adds a shoe to the cart:

1. `ProductDetailPage.jsx` collects the selected variant.
2. `state/cart.js` calls the cart API function.
3. `api/cart.js` sends the request through `api/client.js`.
4. `main.py` receives the HTTP request and checks the JWT.
5. `crud.py` validates stock and writes the cart item through SQLAlchemy.
6. `models.py` describes the database table being changed.
7. `schemas.py` validates the request and response data.
8. The updated cart is returned to the React state and displayed by `CartPage.jsx`.

## Production Deployment

- Frontend: Vercel or Netlify
- Backend: Render or Railway
- Database: Managed PostgreSQL

Before deployment, set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_EMAIL`,
`POSTGRES_PASSWORD`, and the frontend `VITE_API_URL` in the hosting provider's
secret/environment settings. Never commit a real `.env` file.

## Notes

This repository contains a working portfolio-grade webshop foundation with a
React storefront, FastAPI backend, JWT authentication, cart and checkout flow,
orders, PostgreSQL support, and protected product management. Payment
processing, production hosting, and advanced administration can be added later.
