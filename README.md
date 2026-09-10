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

```bash
docker compose up --build
```

## Production Deployment

- Frontend: Vercel or Netlify
- Backend: Render or Railway
- Database: Managed PostgreSQL

## Notes

This is a scaffold for the architecture and sprint plan, not a full implementation. The app is intentionally structured to support a realistic portfolio-grade e-commerce app.
