# Transaction API (Flask Back End)

A Flask-based REST API that powers the Transaction App React front end.  
Provides user authentication, CRUD for transactions, A/B testing, and regression analysis.

---

## Table of Contents

- [Demo](#demo)  
- [Features](#features)  
- [Tech Stack](#tech-stack)  
- [Getting Started](#getting-started)  
  - [Prerequisites](#prerequisites)  
  - [Installation](#installation)  
  - [Environment Variables](#environment-variables)  
  - [Available Commands](#available-commands)  
- [API Reference](#api-reference)  
- [CORS & Authentication](#cors--authentication)  
- [Project Structure](#project-structure)  
- [Contributing](#contributing)  
- [License](#license)  

---

## Demo

> (If deployed, link your live API here; otherwise “Local only”)

---

## Features

- **User Auth**: register, log in, log out (session-based)  
- **Transactions**  
  - List / Create / Update / Delete  
  - Date/time stored as Python `datetime` and serialized to ISO strings  
- **A/B Testing**  
  - Group transactions by half, weekday, time, or month  
  - Returns t-test statistics + boxplot (base64 PNG)  
- **Regression Analysis**  
  - Filter by date range & period (all / morning / noon / afternoon)  
  - Returns slope, intercept, R² + trend-line chart (base64 PNG)  

---

## Tech Stack

- **Flask** web framework  
- **Flask-CORS** for cross-origin requests  
- **Werkzeug** security for password hashing  
- **Matplotlib** for charts  
- **NumPy** & **SciPy** for statistics  

---

## Getting Started

### Prerequisites

- Python 3.9+  
- `pip` (or `poetry` / `pipenv`)  

### Installation

1. Clone the repo:  
   ```bash
   git clone https://github.com/<your-org>/transaction-api-flask.git
   cd transaction-api-flask
   ```
2. Create & activate a virtual environment:  
   ```bash
   python -m venv venv
   source venv/bin/activate   # (Windows: venv\Scripts\activate)
   ```
3. Install dependencies:  
   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Create a `.env` file in the project root:

```ini
FLASK_APP=main.app  
FLASK_ENV=development   # or production  
SECRET_KEY=your-secret-key  
SESSION_COOKIE_SECURE=False  # True if HTTPS  
```

### Available Commands

```bash
flask run         # Start dev server on http://127.0.0.1:5000
pytest            # Run tests (if any)
```

---

## API Reference

All endpoints are under `/api` and return JSON. Except where noted, they require an authenticated session.

| Method | Endpoint                         | Payload / Query Params                         | Returns                                      |
|--------|----------------------------------|------------------------------------------------|----------------------------------------------|
| POST   | `/api/register`                  | `{ "email": "", "password": "" }`              | `201 { message }` or `400 { error }`         |
| POST   | `/api/login`                     | `{ "email": "", "password": "" }`              | `200 { message }` or `401 { error }`         |
| POST   | `/api/logout`                    | _no body_                                      | `200 { message }`                            |
| GET    | `/api/me`                        | _no body_                                      | `200 { id, email }` or `401 { error }`       |
| GET    | `/api/transactions`              | _none_                                         | `200 [ { id, dateTime, amount } ]`           |
| POST   | `/api/transactions`              | `{ "dateTime":"YYYY-MM-DDTHH:MM", "amount":num }` | `201 { id, dateTime, amount }`            |
| PUT    | `/api/transactions/<id>`         | `{ "dateTime":"…", "amount":… }`               | `200 { updated txn }`                        |
| DELETE | `/api/transactions/<id>`         | _no body_                                      | `200 { message }`                            |
| GET    | `/api/analysis/abtest`           | _none_                                         | `{ groupA, groupB, t_score, p_value, boxplot_img }` |
| POST   | `/api/analysis/abtest`           | `{ group_by, param_a, param_b }`               | same as GET + filters                        |
| GET    | `/api/analysis/regression`       | `?start_date=YYYY-MM-DD&end_date=&period=`     | `{ slope, intercept, r_squared, chart_img }` |

---

## CORS & Authentication

- **CORS**: allowed origin `http://localhost:3000`  
- **Sessions**: cookie-based; React axios calls use `withCredentials: true`  

---

## Project Structure

```
main/
├── api_routes.py       
├── data.py             
├── stats/
│   ├── abtest.py       
│   └── regression.py   
├── auth/
│   ├── routes.py       
│   └── utils.py        
└── app.py              
```

---

## Contributing

1. Fork & clone  
2. Create a branch: `git checkout -b feature/xyz`  
3. Commit: `git commit -m "feat(api): add new endpoint"`  
4. Push & open PR  

---

## License
