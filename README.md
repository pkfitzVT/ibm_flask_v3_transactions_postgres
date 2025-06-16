# IBM Flask Transactions v3 (Postgres)

A full-stack transaction tracking application originally built for the IBM Full Stack Developer program. It demonstrates progressive development from a purely Flask-based prototype to a React front end and finally integration with a PostgreSQL database, emphasizing test-driven development and database integration skills.

---

## Table of Contents

- [Demo](#demo)
- [Project History](#project-history)
- [Key Features & Goals](#key-features--goals)
- [Tech Stack](#tech-stack)
- [Setup & Installation](#setup--installation)
  - [Prerequisites](#prerequisites)
  - [Installing Dependencies](#installing-dependencies)
  - [Environment Variables](#environment-variables)
- [API Reference](#api-reference)
- [Project Structure](#project-structure)
- [Running Tests & Lint](#running-tests--lint)
- [Contributing & Workflow](#contributing--workflow)
- [License](#license)

---

## Demo

> Local only (no hosted deployment)

---

## Project History

1. **Local-Variable Prototype (Flask Only)**

   - In-memory `transactions` list in `data/transactions.py`.
   - Core CRUD and analysis endpoints (A/B testing, regression) using local Python structures.
   - Introduced Flask routing, request handling, and Matplotlib charting.

2. **React Front End Integration**

   - React SPA (port 3000) with Axios client (`withCredentials: true`).
   - Components for listing, creating, editing, and deleting transactions.
   - UI pages for A/B testing and regression analysis.

3. **PostgreSQL Back End Migration**

   - Switched to SQLAlchemy models (`Transaction`, `User`) with Postgres.
   - CRUD and analysis endpoints rewired to query/persist in database.
   - Maintained JSON shapes for backward compatibility.

---

## Key Features & Goals

- **Test-Driven Development (TDD)**: Pytest suite covers all endpoints and error paths.
- **Database Integration**: PostgreSQL via SQLAlchemy, Flask-Migrate for migrations.
- **Full-Stack Workflow**: Flask API + React UI, CORS, session-based auth.
- **Statistical Analysis**: A/B testing (t-test + boxplot) and regression (slope, intercept, R² + trendline).

---

## Tech Stack

- **Backend:** Flask, Flask-CORS, SQLAlchemy, Flask-Migrate, statsmodels, Matplotlib
- **Frontend:** React, Axios
- **Database:** PostgreSQL
- **Dev Tools:** Pre-commit (Black, isort, Flake8), Pytest

---

## Setup & Installation

### Prerequisites

- Python 3.9+
- Node.js (12+), npm
- PostgreSQL server running locally or remotely

### Installing Dependencies

Install production dependencies:

```bash
pip install -r requirements.txt
```

> **Note:** `requirements.txt` should include pinned versions of your core libraries. You can generate it via:
>
> ```bash
> pip freeze > requirements.txt
> ```

Install development/test dependencies:

```bash
pip install -r requirements_dev.txt
```

> **Note:** `requirements_dev.txt` should list tools like pytest, flake8, black, isort, and any other dev-only packages. To generate it, you can manually list your dev packages or use:
>
> ```bash
> pip freeze > requirements_dev.txt
> ```

### Environment Variables

Create a `.env` file with:

```
FLASK_APP=main.app
FLASK_ENV=development
DATABASE_URL=postgresql://<user>:<pass>@localhost/<db>
SECRET_KEY=super-secret-key
SESSION_COOKIE_SECURE=False
```

---

## API Reference

All endpoints prefixed with `/api`. Returns JSON.

| Method | Endpoint                   | Payload / Query Params           | Returns                                         |
| ------ | -------------------------- | -------------------------------- | ----------------------------------------------- |
| POST   | `/api/register`            | `{ email, password }`            | `201 { message }` or `400 { error }`            |
| POST   | `/api/login`               | `{ email, password }`            | `200 { message }` or `401 { error }`            |
| POST   | `/api/logout`              | *(none)*                         | `200 { message }`                               |
| GET    | `/api/me`                  | *(none)*                         | `200 { id }` or `401 { error }`                 |
| GET    | `/api/transactions`        | *(none)*                         | `200 [ { id, dateTime, amount, description } ]` |
| POST   | `/api/transactions`        | `{ dateTime, amount }`           | `201 { id, dateTime, amount, description }`     |
| PUT    | `/api/transactions/<id>`   | `{ dateTime?, amount? }`         | `200 { updated txn }`                           |
| DELETE | `/api/transactions/<id>`   | *(none)*                         | `200 { message }`                               |
| GET    | `/api/analysis/abtest`     | *(none)*                         | `{ groupA, groupB, p_value, boxplot_img }`      |
| POST   | `/api/analysis/abtest`     | `{ group_by, param_a, param_b }` | same as GET + filters                           |
| GET    | `/api/analysis/regression` | `?start_date=&end_date=&period=` | `{ slope, intercept, r_squared, chart_img }`    |

---

## Project Structure

```
main/
├── api_routes.py      # Flask endpoints
├── auth/              # Authentication routes & utils
├── data/              # In-memory data (legacy)
├── migrations/        # Alembic migrations
├── models.py          # SQLAlchemy models
├── stats/             # A/B test & regression logic
└── app.py             # Flask app factory

client/                # React front-end
  └── src/
      ├── components/
      ├── pages/
      └── apiClient.js

requirements.txt       # Prod dependencies
requirements_dev.txt   # Dev & test dependencies (pytest, flake8, etc.)
```

---

## Running Tests & Lint

```bash
# Lint & formatting
pre-commit run --all-files

# Run test suite
pytest -q
```

---

## Contributing & Workflow

- **Branching**: feature/xxx for new work
- **Commits**: Conventional Commits format
- **PRs**: Open pull request; ensure CI passes

---

## License

MIT License

*Last updated: June 2025 — Skills focused on Flask, React, PostgreSQL, TDD.*

