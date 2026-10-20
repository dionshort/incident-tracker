# Incident Tracker

![Tests](https://github.com/dionshort/incident-tracker/actions/workflows/tests.yml/badge.svg)

A Django REST API for reporting and triaging production incidents, built in public as a DevSecOps project. Tested and gated by CI today; Docker, security scans and AWS deployment are next.

> 🚧 Work in progress, being built in public.

## Features
- Users report incidents with a title and description; severity defaults to medium and status to open.
- Users only see the incidents they reported.
- Staff see every incident and can manage them in the Django admin, with filters and search.
- The reporter is recorded automatically and can't be changed by anyone.
- Incidents are resolved, never deleted, so the history stays intact.
- A public `/health/` endpoint reports whether the app can reach its database.

## Security decisions
- Closed by default: every API endpoint requires login unless it deliberately opts out, and only `/health/` does.
- Reporter can't be spoofed: on create, the server sets it from the logged-in user and ignores any value sent; on update, it's read-only. Each defence has its own test.
- Users only see their own incidents: asking for someone else's returns 404, not 403, so users can't tell which ids exist.
- No hard deletes: incidents are a record of what happened. `DELETE` returns 405, only partial updates (`PATCH`) are allowed, and the Django admin has no delete option, even for superusers.
- Explicit API fields: the serializer lists its fields instead of using `__all__`, so new model fields are never exposed by accident.
- Health check that reveals nothing: `/health/` is public so load balancers can call it, but it only returns ok or unavailable.
- No secrets in the repo: settings come from environment variables, and `SECRET_KEY` has no default, so the app won't start without one.

## API
| Method | Path | Who | What it does |
| --- | --- | --- | --- |
| `GET` | `/api/incidents/` | Logged-in users | Lists incidents (own only; staff see all) |
| `POST` | `/api/incidents/` | Logged-in users | Reports an incident; the reporter is set automatically |
| `GET` | `/api/incidents/<id>/` | Reporter or staff | Shows one incident; 404 for anyone else |
| `PATCH` | `/api/incidents/<id>/` | Reporter or staff | Updates an incident; the reporter can't change |
| `PUT`, `DELETE` | `/api/incidents/<id>/` | — | Not allowed (405) |
| `GET` | `/health/` | Anyone | 200 if the database is reachable, 503 if not |

## Tech stack
- Now: Python 3.14, Django, Django REST Framework, PostgreSQL 17 (running in Docker locally), GitHub Actions
- Planned: Docker Compose, Bandit, pip-audit, Gitleaks, Trivy, AWS (ECR, EC2), Terraform

## Run locally
Requirements: Python 3.14 and Docker.

1. Clone the repo and create a virtual environment:
```bash
   git clone https://github.com/dionshort/incident-tracker.git
   cd incident-tracker
   python3 -m venv .venv
   source .venv/bin/activate
   pip install -r requirements-dev.txt
```
2. Create your `.env` from the example, then replace every `change-me` value:
```bash
   cp .env.example .env
```
   To generate a `SECRET_KEY`:
```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```
3. Start PostgreSQL in Docker:
```bash
   docker run -d --name incident-tracker-postgres --env-file .env -p 127.0.0.1:5432:5432 -v incident-tracker-pgdata:/var/lib/postgresql/data postgres:17
```
4. Set up the database and an admin user, then start the server:
```bash
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py runserver
```
5. Open http://127.0.0.1:8000/api/ for the API and http://127.0.0.1:8000/admin/ for the admin.

## Running the tests
```bash
python manage.py test -v 2
```
- Coverage: 22 tests for the model, admin, API, permissions and health check.
- CI: GitHub Actions runs the suite on every pull request against a fresh PostgreSQL 17 database, and `main` won't merge anything that fails.
- Tests that can fail: every security rule was checked by breaking the code and confirming its test went red.

## Roadmap
- [x] Django app + REST API + PostgreSQL, with tests
- [x] GitHub Actions: tests on every pull request, required to merge
- [ ] Hardened Docker image (multi-stage, non-root) + Docker Compose
- [ ] Security scans in CI: Bandit, pip-audit, Gitleaks, Trivy
- [ ] Deploy to AWS (ECR, EC2, OIDC, no SSH)
- [ ] Terraform for the AWS infrastructure