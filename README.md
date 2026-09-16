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

For direct local development, copy `backend/.env.example` to `backend/.env` and
`frontend/.env.example` to `frontend/.env`, then start the API and frontend in
separate terminals:

```bash
cd backend
uvicorn app.main:app --reload --port 8001

cd frontend
npm install
npm run dev
```

The admin product screen is available at `/admin/products` after logging in
with the email configured by `ADMIN_EMAIL`.

For Docker development, create a root `.env` with a strong `JWT_SECRET_KEY`
and `POSTGRES_PASSWORD`, then run:

```bash
docker compose up --build
```

## Production Deployment

- Frontend: Vercel or Netlify
- Backend: Render or Railway
- Database: Managed PostgreSQL

Before deployment, set `DATABASE_URL`, `JWT_SECRET_KEY`, `ADMIN_EMAIL`,
`POSTGRES_PASSWORD`, and the frontend `VITE_API_URL` in the hosting provider's
secret/environment settings. Never commit a real `.env` file.

## Notes

This is a scaffold for the architecture and sprint plan, not a full implementation. The app is intentionally structured to support a realistic portfolio-grade e-commerce app.
