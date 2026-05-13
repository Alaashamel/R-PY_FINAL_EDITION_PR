# E-Commerce System Backend

A FastAPI backend for an online store with product/category management, shopping cart, order placement, inventory updates, JWT authentication, role-based authorization, Redis cache-aside caching, logging, monitoring, API tests, Docker, and a simple frontend.

## Project Scope

The system supports two roles:

- **Admin:** manage products and categories, view all orders, update order status, deactivate products.
- **Customer:** register/login, browse products, manage cart, place orders, cancel pending orders, view own orders.

## Implemented Requirements

| Requirement | Status | Evidence |
|---|---:|---|
| Clean project structure | Done | `app/routes`, `app/models`, `app/schemas`, `app/services`, `app/core`, `app/database`, `tests` |
| RESTful API | Done | CRUD endpoints for products and categories, user/order/cart endpoints |
| Pydantic validation | Done | Request/response schemas in `app/schemas` |
| Proper status codes | Done | `201`, `204`, `400`, `401`, `403`, `404`, `422` used where appropriate |
| JWT authentication | Done | `/auth/register`, `/auth/login`, JWT validation dependencies |
| Role-based authorization | Done | Admin-only dependencies protect product/category/order admin endpoints |
| Error handling | Done | `HTTPException`, validation errors, clear service-level messages |
| Redis caching | Done | Cache-aside pattern for product/category reads with invalidation on writes |
| Measurable caching demo | Done | `scripts/cache_benchmark.py` compares first request vs cached requests |
| Logging | Done | Request/response logging, auth events, CRUD events, error logs, JSON structured logs |
| Monitoring dashboard | Done | Prometheus `/metrics`, Grafana dashboard, and simple frontend monitoring page |
| API testing | Done | Pytest + FastAPI `TestClient` tests in `tests/` |
| Docker integration | Done | `Dockerfile` and `docker-compose.yml` for app, PostgreSQL, Redis, frontend, Prometheus, Grafana |
| Frontend bonus | Done | HTML/CSS/JavaScript frontend in `frontend/` |
| Git/GitHub guidance | Done | `.gitignore`, GitHub Actions workflow, `GIT_GUIDE.md` |

## Tech Stack

- FastAPI
- SQLAlchemy
- PostgreSQL
- Redis
- JWT with `python-jose`
- Passlib/Bcrypt password hashing
- Pydantic v2
- Pytest
- Prometheus + Grafana
- Docker Compose
- HTML/CSS/JavaScript frontend

## Project Structure

```text
app/
  core/              # settings, JWT/security, dependencies, Redis client
  database/          # SQLAlchemy engine/session/base
  middleware/        # request logging and Prometheus metrics middleware
  models/            # SQLAlchemy database models
  routes/            # FastAPI routers/endpoints
  schemas/           # Pydantic request/response models
  services/          # business logic and cache invalidation
  utils/             # logging and serialization helpers
frontend/            # simple UI for customers/admins
monitoring/          # Prometheus and Grafana provisioning
tests/               # pytest test suite
scripts/             # seed and benchmark scripts
```

## Quick Start with Docker

```bash
docker compose up --build -d
```

Seed demo accounts and sample data:

```bash
docker compose exec app python scripts/seed.py
```

Open:

- Frontend: `http://localhost:8080`
- API docs: `http://localhost:8000/docs`
- API health: `http://localhost:8000/health`
- Monitoring health: `http://localhost:8000/monitoring/health`
- Prometheus metrics: `http://localhost:8000/metrics`
- Prometheus UI: `http://localhost:9090`
- Grafana: `http://localhost:3000` using `admin / admin`
- Simple monitoring page: `http://localhost:8080/monitoring.html`

Demo accounts after seeding:

| Role | Username | Password |
|---|---|---|
| Admin | `admin` | `adminpass123` |
| Customer | `customer` | `customer123` |

## Local Development

```bash
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

For local development without Docker, update `.env` if PostgreSQL or Redis use different hostnames.

## Run Tests

```bash
pytest -q
```

The tests set their own SQLite environment variables in `tests/conftest.py`, so they do not require PostgreSQL.

## Cache-Aside Pattern

The application uses Redis for frequently accessed reads:

- `GET /products/`
- `GET /products/{product_id}`
- `GET /categories/`
- `GET /categories/{category_id}`

Flow:

1. Try Redis first.
2. If cache miss, read from database.
3. Store the result in Redis with TTL.
4. Invalidate related cache keys after create/update/delete/stock changes.

Measure cache improvement:

```bash
docker compose exec app python scripts/cache_benchmark.py --username customer --password customer123 --path /products/
```

Example output format:

```text
First request: 35.20 ms
Cached average over 5 runs: 8.40 ms
Estimated improvement: 76.1%
```

Actual numbers depend on your machine and dataset size.

## Logging and Monitoring

Logs are written to:

- `logs/api_YYYY-MM-DD.log` for readable API logs
- `logs/error_YYYY-MM-DD.log` for recent errors
- `logs/structured_YYYY-MM-DD.json` for machine-readable structured logs

Prometheus metrics exposed by middleware:

- `http_requests_total`
- `http_request_duration_seconds`

Monitoring dashboard coverage:

- API request counts
- Response times / latency
- Error rates by status code
- System health status
- Recent error logs via `/monitoring/recent-errors` and `frontend/monitoring.html`

## Main API Endpoints

### Authentication and Users

| Method | Endpoint | Access |
|---|---|---|
| POST | `/auth/register` | Public |
| POST | `/auth/login` | Public |
| GET | `/users/me` | Authenticated |

### Products

| Method | Endpoint | Access |
|---|---|---|
| GET | `/products/` | Authenticated customer/admin |
| GET | `/products/{product_id}` | Authenticated customer/admin |
| POST | `/products/` | Admin |
| PUT | `/products/{product_id}` | Admin |
| DELETE | `/products/{product_id}` | Admin |

Supports search/filter/pagination:

```text
GET /products/?search=phone&category_id=1&min_price=100&max_price=1000&skip=0&limit=20
```

### Categories

| Method | Endpoint | Access |
|---|---|---|
| GET | `/categories/` | Authenticated customer/admin |
| GET | `/categories/{category_id}` | Authenticated customer/admin |
| POST | `/categories/` | Admin |
| PUT | `/categories/{category_id}` | Admin |
| DELETE | `/categories/{category_id}` | Admin |

### Cart

| Method | Endpoint | Access |
|---|---|---|
| GET | `/cart/` | Customer/Admin |
| POST | `/cart/add/{product_id}?quantity=1` | Customer/Admin |
| PUT | `/cart/update/{product_id}?quantity=2` | Customer/Admin |
| DELETE | `/cart/remove/{product_id}` | Customer/Admin |
| DELETE | `/cart/clear` | Customer/Admin |

### Orders

| Method | Endpoint | Access |
|---|---|---|
| POST | `/orders/` | Customer/Admin |
| GET | `/orders/` | Own orders |
| GET | `/orders/{order_id}` | Owner/Admin |
| POST | `/orders/{order_id}/cancel` | Owner/Admin, pending only |
| GET | `/orders/all` | Admin |
| PUT | `/orders/{order_id}/status?status=confirmed` | Admin |

### Monitoring

| Method | Endpoint | Access |
|---|---|---|
| GET | `/health` | Public |
| GET | `/metrics` | Public/Prometheus |
| GET | `/monitoring/health` | Public |
| GET | `/monitoring/recent-errors` | Admin |
| GET | `/monitoring/dashboard-summary` | Admin |

## Business Rules

- Duplicate usernames/emails are rejected.
- Passwords must contain letters and numbers and cannot contain spaces.
- Only admins can create/update/delete products and categories.
- Category names must be unique.
- A category with products cannot be deleted.
- Product stock cannot be negative.
- Orders cannot be created if stock is insufficient.
- Creating an order decreases stock.
- Cancelling a pending order restores stock.
- Product delete is implemented as a soft delete to preserve historical order items.

## Team Roles for Submission

Update this section with real names before submitting:

| Member | Role | Suggested Branch |
|---|---|---|
| Member 1 | Auth + Users | `feature/auth-users` |
| Member 2 | Products + Categories | `feature/products-categories` |
| Member 3 | Cart + Orders | `feature/cart-orders` |
| Member 4 | Redis + Logging + Monitoring | `feature/cache-monitoring` |
| Member 5 | Tests + Docker + README | `feature/tests-docker-docs` |

Important: each member must push meaningful commits from their own GitHub account. Do not submit only one final bulk commit.

## GitHub Submission

See `GIT_GUIDE.md` for the recommended branch strategy, pull request flow, and commit examples.
