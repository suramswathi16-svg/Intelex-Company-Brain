# React + Vite

This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules.

Currently, two official plugins are available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Oxc](https://oxc.rs)
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/)

## React Compiler

The React Compiler is not enabled on this template because of its impact on dev & build performances. To add it, see [this documentation](https://react.dev/learn/react-compiler/installation).

## Expanding the ESLint configuration

If you are developing a production application, we recommend using TypeScript with type-aware lint rules enabled. Check out the [TS template](https://github.com/vitejs/vite/tree/main/packages/create-vite/template-react-ts) for information on how to integrate TypeScript and [`typescript-eslint`](https://typescript-eslint.io) in your project.
# intelex Company Brain — Backend

FastAPI + PostgreSQL backend for the enterprise knowledge platform hackathon
project. Covers authentication, RBAC, and the core API surface (uploads,
chat, dashboard, alerts, analytics).

## Project structure

```
backend/
├── main.py         # App entrypoint, CORS, startup seeding
├── auth.py         # Password hashing, JWT, RBAC dependencies
├── routes.py       # All API endpoints
├── database.py     # SQLAlchemy engine/session setup
├── models.py       # ORM models (users, uploads, chat, alerts, analytics)
├── schemas.py      # Pydantic request/response models
├── requirements.txt
└── .env.example
```

## 1. Setup

```bash
# from the backend/ folder
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Create a PostgreSQL database:

```sql
CREATE DATABASE company_brain;
```

Copy the env file and fill in your DB credentials / secret key:

```bash
cp .env.example .env
```

## 2. Run

```bash
uvicorn main:app --reload
```

- API root: http://localhost:8000/
- Interactive docs (Swagger UI): http://localhost:8000/docs

On first run, the app automatically creates all tables and seeds three
demo accounts:

| username   | password      | role     |
|------------|---------------|----------|
| admin      | Admin@123     | admin    |
| employee1  | Employee@123  | employee |
| analyst1   | Analyst@123   | analyst  |

It also seeds a few sample alerts and employee-analysis metrics so the
dashboard/analytics endpoints return real-looking data immediately.

## 3. Auth flow

1. `POST /register` — create an account (`username`, `email`, `password`, `role`)
2. `POST /login` — returns `{ access_token, token_type, role }`
3. For every protected endpoint, send:
   `Authorization: Bearer <access_token>`

## 4. Endpoints & required roles

| Method | Path                 | Roles allowed          | Notes                                  |
|--------|----------------------|-------------------------|-----------------------------------------|
| POST   | /register            | public                  | Creates a user                          |
| POST   | /login               | public                  | Returns JWT                             |
| GET    | /users               | admin                   | List all users                          |
| POST   | /upload              | admin, employee         | multipart/form-data file upload         |
| POST   | /chat                | any authenticated role  | Sends message, gets mock AI reply       |
| GET    | /dashboard           | admin, analyst          | Aggregated stats                        |
| GET    | /alerts              | any authenticated role  | List alerts                             |
| POST   | /alerts              | admin                   | Create an alert                         |
| GET    | /employee-analysis   | admin, analyst          | Raw analytics rows                      |

## 5. Example: login + call a protected route (curl)

```bash
# Login
curl -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "Admin@123"}'

# Use the returned token
curl http://localhost:8000/dashboard \
  -H "Authorization: Bearer <TOKEN_HERE>"
```

## 6. Extending this backend

- **RAG search**: In `routes.py`, replace `generate_mock_response()` inside
  `/chat` with a real retrieval step (vector DB query) + LLM call.
- **File storage**: In the `/upload` handler, stream `file.file` to S3 /
  local disk in addition to storing metadata, then trigger embedding.
- **Migrations**: Swap `Base.metadata.create_all()` for Alembic once the
  schema stabilizes.
- **Production hardening**: restrict CORS origins, rotate `JWT_SECRET_KEY`
  via a secrets manager, add rate limiting, and use HTTPS everywhere.
