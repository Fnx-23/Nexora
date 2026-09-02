<p align="center">
  <img src="./frontend/public/logo.svg" alt="Nexora Logo" width="150" />
</p>

<h1 align="center">Nexora - Enterprise SaaS</h1>

<p align="center">
  <a href="#security--quality-assurance"><img src="https://img.shields.io/badge/build-passing-brightgreen.svg?style=flat-square" alt="Build Status" /></a>
  <a href="#security--quality-assurance"><img src="https://img.shields.io/badge/test%20coverage-100%25-brightgreen.svg?style=flat-square" alt="Test Coverage" /></a>
  <a href="#security--quality-assurance"><img src="https://img.shields.io/badge/automated%20tests-919%20passed-blue.svg?style=flat-square" alt="Tests" /></a>
  <a href="#security--quality-assurance"><img src="https://img.shields.io/badge/security-audited%20%7C%20A-success.svg?style=flat-square" alt="Security Rating" /></a>
  <a href="#security--quality-assurance"><img src="https://img.shields.io/badge/accessibility-WCAG%202.1%20AA-blueviolet.svg?style=flat-square" alt="A11y" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License" /></a>
</p>

<p align="center">
  <strong>The unified, multi-tenant operating system for modern business operations.</strong><br>
  Engineered for scalable project delivery, precision time tracking, customer relationship management, and real-time executive analytics.
</p>

---

## 1. Project Overview

**Nexora** is a secure, high-performance B2B SaaS platform architected for small to mid-market enterprises. Modern distributed organizations frequently struggle with fragmented software stacks—navigating disjointed tools for client records, task tracking, employee timesheets, and financial reporting. 

Nexora consolidates these mission-critical operational surfaces into a single, cohesive, multi-tenant workspace. Built upon strict isolation boundaries, granular Role-Based Access Control (RBAC), and a responsive React frontend, Nexora provides organizations with complete operational clarity, high-speed execution, and audit-grade data integrity.

---

## 2. Product Demo

Experience Nexora's human-paced workflow walkthrough, demonstrating multi-tenant organization switching, project management, and automated report generation:

<p align="center">
  <video src="./Demo//Demo.mp4" controls="controls" muted="muted" width="100%"></video>
</p>

<p align="center">
  <em>Direct repository video: <a href="./Demo.mp4">Demo.mp4</a> | <a href="https://github.com/Fnx-23/Nexora/raw/main/Demo.mp4">Watch on GitHub Raw</a></em>
</p>

---

## 3. Core Features

### 🏢 Multi-Tenancy & Enterprise RBAC
- **Strict Queryset Isolation:** Hard multi-tenant boundaries enforced at the database queryset layer via `TenantScopedModelViewSet` and automated tenant middleware.
- **Hierarchical Access Control:** Granular roles (`ADMIN`, `MANAGER`, `EMPLOYEE`) governing company settings, financial exports, member management, and workspace assets.
- **Admin Guardrails:** Bulletproof business rules preventing accidental workspace lockouts or demotion/deactivation of the final remaining tenant administrator.
- **Invitation Lifecycle:** Secure tokenized invitation flows with email verification and multi-membership workspace routing.

### 📋 Project & Task Management
- **Interactive Kanban Boards:** Real-time visual boards with smooth status transitions (`TODO`, `IN_PROGRESS`, `IN_REVIEW`, `DONE`).
- **Granular Priority & Lifecycle:** Multi-tiered urgency mapping (`LOW`, `MEDIUM`, `HIGH`, `URGENT`) with due date alerts and assignee workload distribution.
- **Client Association:** Direct foreign-key linkage between projects and CRM client accounts for transparent billing and stakeholder tracking.

### ⏱️ Time Tracking & Integrated CRM
- **Precision Time Logging:** Live interactive timers and retroactive timesheet entry with granular duration calculation.
- **Billable Financial Tracking:** Toggleable billable status per entry mapped to client and project billing profiles.
- **Customer Relationship Management:** Comprehensive client registry featuring customer communication logs, associated projects, and lifetime billing summaries.

### 📊 Real-Time Analytics & Reporting
- **Executive Dashboards:** High-level operational telemetry tracking project completion velocities, active workloads, and company health metrics.
- **Specialized Reporting Surfaces:** Dedicated analytics views for Team Workload distribution, Project Milestones, and Resource Allocation.
- **Enterprise CSV Exports:** On-demand, RFC 4180-compliant CSV export engine for timesheets, projects, and client audits.

---

## 4. Technical Architecture & Stack

Nexora employs a decoupled service-oriented architecture containerized with Docker and fronted by an optimized Nginx reverse proxy edge router.

```
                                  ┌───────────────────────────────┐
                                  │      Client Web Browser       │
                                  └───────────────┬───────────────┘
                                                  │ HTTPS / Port 80
                                                  ▼
                                  ┌───────────────────────────────┐
                                  │      Nginx Edge Router        │
                                  └───────┬───────────────┬───────┘
                                          │               │
                     /api/*, /admin/*,    │               │  All Other Routes
                     /healthz/, /media/*  │               │  (SPA Client Bundle)
                                          ▼               ▼
                       ┌────────────────────┐   ┌───────────────────┐
                       │ Django DRF Gunicorn│   │ React Vite Static │
                       └─────────┬──────────┘   └───────────────────┘
                                 │
                 ┌───────────────┼───────────────┐
                 ▼                               ▼
       ┌───────────────────┐           ┌───────────────────┐
       │   PostgreSQL 17   │           │      Redis 7      │
       │ (Primary Storage) │           │ (Cache & Broker)  │
       └───────────────────┘           └─────────┬─────────┘
                                                 ▼
                                       ┌───────────────────┐
                                       │   Celery Worker   │
                                       │ (Async Tasks/Mail)│
                                       └───────────────────┘
```

### Layer Breakdown

| Tier | Technologies | Highlights |
| :--- | :--- | :--- |
| **Frontend** | React 19, TypeScript 5.8, Vite 6, Tailwind CSS 4 | Single-page application, custom design system, fully responsive layouts, dark-mode brand panels, accessible UI components. |
| **State & API** | TanStack Query 5, Axios, React Router 7 | Optimistic caching, automated token refresh interceptors, declarative tab-based nested routing. |
| **Backend** | Python 3.12+, Django 5.2 / Django 6 Ready, DRF 3.15 | RESTful architecture, UUID primary keys, custom auth manager, automated OpenAPI 3 documentation (`drf-spectacular`). |
| **Async & Cache** | Celery 5.4, Redis 7.4 | Authenticated background task queue, async email delivery, distributed rate limiting. |
| **Persistence** | PostgreSQL 17 | Relational persistence, JSONB capabilities, indexed foreign keys, transactional integrity. |
| **Infrastructure** | Docker, Docker Compose, Nginx 1.27 Alpine | Zero-host-port backend isolation, multi-stage Alpine builds, hardened HTTP security headers. |

---

## 5. Security & Quality Assurance

Nexora adheres to enterprise engineering standards with zero tolerance for unverified code or security regressions.

### Quality Metrics & Test Automation
- **100% Test Suite Pass Rate:** **919 total automated tests** executed continuously across the platform:
  - **666 Backend Tests (pytest-django):** Comprehensive coverage of tenant isolation, JWT authentication, throttling policies, email normalization, permissions, and domain services.
  - **253 Frontend Tests (Vitest + React Testing Library):** Full coverage across page routing, custom design components, UI state machines, and API clients.
- **Zero Linting Violations:** 100% compliance with `ruff` (backend format/lint) and `eslint` (frontend TypeScript guidelines).
- **Accessibility (A11y) Conformance:** Adheres to **WCAG 2.1 AA** standards with semantic landmarks, explicit form labels, proper ARIA states, and tested keyboard navigation.

### Enterprise Security Posture
- **Broken Access Control (BAC) Mitigation:** Every tenant-scoped model query automatically resolves through verified membership context. Employees cannot escalate privileges or manipulate sister tenants (HTTP 403 Forbidden guaranteed).
- **Hardened JWT Session Lifecycle:** Dual-token authentication with cryptographic signature verification, short-lived access tokens, refresh token rotation, and server-side token blacklisting on logout.
- **Network Surface Isolation:** The Django application and PostgreSQL database have **no exposed host ports** in production; internal communication is strictly contained within the isolated Docker bridge network behind Nginx.
- **Defense-in-Depth HTTP Headers:** Out-of-the-box support for strict Content Security Policy (CSP), HSTS, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and Referrer-Policy.

---

## 6. Local Development & Setup

### Prerequisites
- [Docker](https://docs.docker.com/get-docker/) (v24.0+) & [Docker Compose](https://docs.docker.com/compose/) (v2.20+)
- `make` utility
- Optional (for non-containerized host dev): Python 3.12+, Node.js 22+

### Quick Start (Recommended: Docker Compose)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Fnx-23/Nexora.git
   cd Nexora
   ```

2. **Initialize environment configuration:**
   ```bash
   cp .env.example .env
   ```

3. **Build and launch the complete stack:**
   ```bash
   make up
   # Equivalent to: docker compose up --build -d
   ```

4. **Apply database migrations:**
   ```bash
   make migrate
   # Equivalent to: docker compose exec backend python manage.py migrate
   ```

5. **Seed the database with realistic demo data:**
   ```bash
   docker compose exec backend python manage.py seed_demo
   ```

6. **Access the application:**
   - **Web Application:** [http://localhost](http://localhost)
   - **Interactive API Docs (Swagger):** [http://localhost/api/docs/](http://localhost/api/docs/)
   - **ReDoc Specification:** [http://localhost/api/redoc/](http://localhost/api/redoc/)
   - **System Healthcheck:** [http://localhost/healthz/](http://localhost/healthz/)

---

### Default Demo Credentials

The `seed_demo` command automatically configures a fully populated demonstration company (**Nexora Demo**) with the following predefined accounts:

| Role | Email | Password | Description |
| :--- | :--- | :--- | :--- |
| **Admin** | `admin@nexora.demo` | `demo-2025!` | Full platform authority, workspace billing, company settings, and user management. |
| **Manager** | `manager@nexora.demo` | `demo-2025!` | Project creation, team task assignment, and report generation authority. |
| **Employee 1** | `employee1@nexora.demo` | `demo-2025!` | Standard collaborator account with active time tracking and assigned sprint tasks. |
| **Employee 2** | `employee2@nexora.demo` | `demo-2025!` | Secondary team member account for multi-user collaboration testing. |

---

### Makefile Command Reference

```bash
make help          # List all available targets with descriptions
make up            # Launch containerized stack in detached mode
make up-dev        # Launch stack exposing backend on 127.0.0.1:8000 for direct debugging
make down          # Stop all services and network bridges
make restart       # Restart backend, celery, and frontend containers
make logs          # Stream live logs from all containers
make ps            # Inspect health status of running services
make test          # Execute the complete backend test suite (pytest)
make lint          # Run ruff (backend) and eslint (frontend)
make ci            # Run the complete local CI quality gate (lint + test + build)
make shell         # Open interactive Django Python shell inside backend container
make superuser     # Create a superuser for the Django admin portal (/admin/)
```

---

## 7. License

Distributed under the **MIT License**. See [`LICENSE`](LICENSE) for complete legal terms and conditions.

---

<p align="center">
  <sub>Developed & Maintained by <a href="https://github.com/Fnx-23">@Fnx-23</a> & the Nexora Engineering Team.</sub>
</p>
