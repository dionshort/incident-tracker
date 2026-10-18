# Incident Tracker

A Django REST API for logging and tracking production incidents, built and shipped with a DevSecOps workflow: tested, containerised, security-scanned in CI/CD and deployed to AWS with least privilege.

> 🚧 Work in progress, being built in public.

## Roadmap
- [ ] Django app + REST API + PostgreSQL, with tests
- [ ] Hardened Docker image (multi-stage, non-root) + Docker Compose
- [ ] GitHub Actions pipeline: tests, Bandit, pip-audit, Gitleaks, Trivy
- [ ] Deploy to AWS (ECR, EC2, OIDC, no SSH)
- [ ] Terraform for the AWS infrastructure

## Run locally
_Coming soon._

## Tech stack
Python · Django · Django REST Framework · PostgreSQL · Docker · GitHub Actions · AWS