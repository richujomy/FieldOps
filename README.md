# FieldOps - Quickstart

Steps to run, test, and explore the API.

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

## Auth (JWT)

```http
POST /api/users/auth/register/
POST /api/users/auth/login/
POST /api/users/auth/refresh/
GET  /api/users/profile/  (requires Bearer token)
```

## Core Endpoints

Service Requests:
```http
GET  /api/service-requests/
POST /api/service-requests/
GET  /api/service-requests/{id}/
PATCH/DELETE /api/service-requests/{id}/
POST /api/service-requests/{id}/assign/
POST /api/service-requests/{id}/rate/
```

Tasks:
```http
GET  /api/tasks/
GET  /api/tasks/{id}/
POST /api/tasks/{id}/set-status/
POST /api/tasks/{id}/upload-proof/
```

Dashboards:
```http
GET /api/dashboard/admin/
GET /api/dashboard/worker/
GET /api/dashboard/customer/
```

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
