# Sanaap — Backend API Challenge

> A production-ready RESTful API built with Django, containerized with Docker, and designed for scalability.

---

## Table of Contents

- [Overview](#overview)
- [Tech Stack](#tech-stack)
- [Architecture](#architecture)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Environment Variables](#environment-variables)
  - [Run with Docker](#run-with-docker)
  - [Service URL](#service-urls)
- [API Reference](#api-reference)
- [Design Decisions](#design-decisions)
- [Roadmap](#roadmap)

---

## Overview

This project is a backend API submission for the **Sanaap engineering code challenge**. It implements a fully containerized Django REST API with a focus on production-readiness, clean architecture, and SOLID principles.

Key highlights:

- **Django 6.0.5 / Python 3.12.3** — latest stable versions
- **PostgreSQL** as the primary relational database
- **MinIO** (S3-compatible) for object storage — all file and image handling is decoupled from the application server
- **Redis** for caching — structured to be extended as a Celery task broker
- **Nginx** as a reverse proxy — serves static files directly and proxies all other traffic, with no public exposure of internal services

---

## Tech Stack

| Layer | Technology | Version |
|---|---|---|
| Language | Python | 3.12.3 |
| Framework | Django | 6.0.5 |
| Database | PostgreSQL | 17 (Alpine) |
| Cache | Redis | 7 (Alpine) |
| Object Storage | MinIO | Latest |
| Reverse Proxy | Nginx | Alpine |
| Containerization | Docker + Docker Compose | — |

---

## Architecture



### Why MinIO instead of local media storage?

Traditional Django media storage ties files to a single server's filesystem, which breaks horizontal scaling. MinIO provides an S3-compatible object storage layer that:

- Decouples file storage from application logic
- Scales independently from the API server
- Allows pre-signed URL generation — clients download files directly from MinIO without Django acting as a middleman
- Is a drop-in replacement for AWS S3 in production (just swap the endpoint URL)

---

## Project Structure

```
.
├── backend/                    # Django application source
│   ├── project/                 # Project settings, URLs, WSGI/ASGI
│   │   ├── asgi.pi
│   │   ├── settings.py
│   │   └── urls.py
│   │   ├── wsgi.pi
│   ├── apps/                   # Django apps (each feature is its own app)
│   └── manage.py
│
├── dockerfiles/
│   ├── dev/
│   │   └── backend/
│   │       └── Dockerfile      # Development Django image
│   └── prod/
│       └── backend/
│           └── Dockerfile      # Nginx image
│           
│
├── docker-compose.yml          # Full stack orchestration
├── .env.example                # Environment variable template
├── requirements.txt            # requirements file
└── README.md
```

---

## Getting Started

### Prerequisites

- [Docker](https://docs.docker.com/get-docker/) `>= 24`
- [Docker Compose](https://docs.docker.com/compose/) `>= 2.20`

No local Python installation is required — everything runs inside Docker.

---

### Environment Variables

Copy the example file and fill in your values:

```bash
cp .env.example .env
```

`.env.example`:

```env
# -------- Django related secret --------
DEBUG=True if in development environment
SECRET_KEY=your_super_secure_password


# -------- Database related secret --------
POSTGRES_DB=your_db_name
POSTGRES_USER=your_db_user
POSTGRES_PASSWORD=super_secret_password


# -------- MinIO related secret --------
MINIO_ENDPOINT=http://minio:9000    **replace service name in docker compose**
MINIO_PUBLIC_ENDPOINT_URL=http://localhost:9000     
MINIO_ACCESS_KEY=your_minio_access_key
MINIO_SECRET_KEY=your_minio_secret_key
MINIO_BUCKET_NAME=sanaap-media


# -------- Redis related environment --------
DEFAULT_REDIS_URL=redis://redis:6379/0
DOCUMENT_CACHE_TTL=2700
```

> **Security note:** The `.env` file is listed in `.gitignore` and must never be committed to version control.

---

### Run with Docker

**Start all services:**

```bash
docker compose -f docker-compose-prod.yml up --build
```

**Run in detached mode:**

```bash
docker compose -f docker-compose-prod.yml up --build -d
```

**Apply database migrations:**

> **note:** No need to apply migrations manually.

**Collect static files** (required for Nginx to serve them):

> **note:** No need to apply migrations manually.

**Create a superuser:**

> **note:** This will also handled with docker you should just provide superuser credentials in .env.

**Stop all services:**

```bash
docker compose down
```

**Stop and remove volumes** (full reset):

```bash
docker compose down -v
```

---

### Service URLs

Once running, the following are accessible:

| Service | URL | Notes |
|---|---|---|
| Django API | `http://localhost/` | Proxied through Nginx |
| Django Admin | `http://localhost/admin/` | |
| MinIO Console | `http://localhost/minio/` | Object storage admin UI |

---

## API Reference

> Base URL: `http://localhost/api/v1/`

> swagger Documentation URL: `http://localhost/api/v1/docs/`


<!-- 
  ✏️  Fill in your actual endpoints below.
  Example format shown — replace with real routes.
-->

<!-- ### Authentication

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `POST` | `/api/v1/auth/register/` | Register a new user | No |
| `POST` | `/api/v1/auth/login/` | Obtain JWT token pair | No |
| `POST` | `/api/v1/auth/token/refresh/` | Refresh access token | No | -->

<!-- ### Resources

| Method | Endpoint | Description | Auth Required |
|---|---|---|---|
| `GET` | `/api/v1/...` | ... | Yes |
| `POST` | `/api/v1/...` | ... | Yes |
| `GET` | `/api/v1/.../id/` | ... | Yes |
| `PUT` | `/api/v1/.../id/` | ... | Yes |
| `DELETE` | `/api/v1/.../id/` | ... | Yes | -->

<!-- ### Response format

All responses follow a consistent envelope:

```json
{
  "status": "success",
  "data": { },
  "message": ""
}
```

Error responses:

```json
{
  "status": "error",
  "errors": {
    "field_name": ["This field is required."]
  }
}
``` -->

<!-- --- -->

## Design Decisions

### 1. MinIO over Django's default `FileSystemStorage`

Django's default media handling stores files on the local filesystem. This works for single-server setups but creates tight coupling between the API server and storage. MinIO (S3-compatible) makes the storage layer completely independent, meaning:

- The API server can be scaled horizontally without any shared filesystem concerns
- Migrating to AWS S3 in a live environment requires only an environment variable change — no code changes

### 2. Redis as cache (with Celery in mind)

Redis is configured as a caching backend. The service and its connection pooling are intentionally set up to also serve as a Celery broker without any infrastructure changes — only a configuration addition is needed when async tasks are introduced.

### 3. Nginx in front of everything

Nginx handles three distinct responsibilities:
- **Static file serving** — bypasses Django entirely, served from a shared Docker volume
- **MinIO proxying** — keeps MinIO internal, all traffic routed through a single port
- **Django proxying** — passes `X-Forwarded-For` and `X-Real-IP` headers for accurate request logging and rate limiting

### 4. Health checks on every dependent service

Every service that `web` depends on (`db`, `redis`, `minio`) has a Docker health check. The Django container will not start until all three pass — preventing connection errors during cold starts.

---

## Roadmap

Features not yet implemented but planned for the next iteration:

- [ ] **Celery** — async task queue using Redis as the broker (worker and beat scheduler)
- [ ] **Unit Test**
- [ ] **Django Chennels**
- [ ] **Audit Logging**
<!-- - [ ] **Flower** — Celery monitoring dashboard -->
<!-- - [ ] **HTTPS / TLS** — Nginx SSL termination with Let's Encrypt (Certbot) -->
<!-- - [ ] **Rate limiting** — Nginx-level `limit_req_zone` per IP -->
<!-- - [ ] **API documentation** — Swagger / ReDoc via `drf-spectacular` -->
<!-- - [ ] **CI/CD pipeline** — GitHub Actions for lint, test, and build on push -->

---

## Author

Developed as a backend engineering code challenge submission for **Sanaap**.