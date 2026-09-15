frontend/
├── src/
│ ├── App.jsx
│ ├── main.jsx
│ ├── styles.css
│ ├── api/
│ │ ├── auth.js
│ │ ├── products.js
│ │ ├── cart.js
│ │ ├── orders.js
│ │ └── addresses.js
│ ├── components/
│ │ ├── Header.jsx
│ │ ├── ProductCard.jsx
│ │ ├── CartItem.jsx
│ │ └── OrderCard.jsx
│ ├── pages/
│ │ ├── HomePage.jsx
│ │ ├── ProductDetailPage.jsx
│ │ ├── LoginPage.jsx
│ │ ├── RegisterPage.jsx
│ │ ├── CartPage.jsx
│ │ ├── CheckoutPage.jsx
│ │ ├── OrderConfirmationPage.jsx
│ │ └── OrdersPage.jsx
│ └── state/
│ ├── auth.js
│ ├── cart.js
│ └── orders.js# Sprint 2 — Data Model & Backend Core

## Goal

Build the database schema and backend model foundation needed for users, products, orders, and cart logic.

## Deliverables

- SQLAlchemy models
- Database migrations or schema bootstrap
- Product seed data
- Health and config endpoints

## Scope

- User model
- Product and category models
- Variant and image models
- Order and order item models
- Cart item model
- Product seed data

## Acceptance Criteria

- Models are created in ORM layer
- Database schema is generated successfully
- Seed product data is loadable
- Basic backend health endpoint works

## Notes

This sprint is the data foundation for all later features.
