# FieldOps - Quickstart

Steps to run, test, and explore the API.

## Tech Stack

- **Backend Framework**: Django REST Framework
- **Database**: SQLite3 (default Django database)
- **Authentication**: JWT (JSON Web Tokens)
- **API Documentation**: Swagger UI
- **Python Version**: 3.13+

## Prerequisites

- Python 3.13 or higher
- Virtual environment (recommended)

## Environment Setup

- Create a `.env` file in the root directory

## Install

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
```

Optional (create admin user):
```bash
python manage.py createsuperuser
```

## Run

```bash
python manage.py runserver
```

- API root: http://localhost:8000/api/
- Admin: http://localhost:8000/admin/
- API docs (Swagger UI): http://localhost:8000/api/docs/


## Testing

```bash
python manage.py test -v 2

# Modules
python manage.py test users.test_auth
python manage.py test service_requests.test_service_requests
python manage.py test service_requests.test_admin_assignment
python manage.py test tasks.test_worker_updates
python manage.py test dashboard.test_dashboards
```

Notes:
- Default auth is JWT: set header `Authorization: Bearer <access_token>`.
- Media uploads saved under `media/` (see `settings.MEDIA_ROOT`).
- Create a .env file in the root directory.
