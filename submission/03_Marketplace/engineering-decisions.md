# Engineering decisions

| Decision | Choice and rationale | Alternatives / trade-offs | Security and risk |
|---|---|---|---|
| Backend | Django 5.2 LTS; built-in ORM, auth, admin and migrations | Flask/FastAPI require more assembly | Keep supported patch releases current |
| Frontend | Server-rendered Django templates | SPA adds a second app and auth boundary | Autoescape and CSRF remain enabled |
| Styling | Compiled Tailwind 4 with reusable component CSS | CDN runtime is simpler but adds a runtime dependency | Serve committed output through WhiteNoise |
| Database | PostgreSQL for deployment; explicit SQLite offline mode | SQLite simplifies evaluation but does not validate row locking | PostgreSQL tests and integration verification must be distinguished |
| Hosting | Supabase PostgreSQL configuration | Self-managed DB has more operational burden | TLS, restricted DB credentials, no public Data API exposure |
| ORM | Django ORM | Raw SQL adds maintenance and injection risk | Constraints guard local invariants; ORM does not replace authorization |
| Authentication | Django password hashing and sessions | JWT unnecessary for same-origin app | Secure cookies and HTTPS in production; no credential logging |
| Roles | Built-in Buyer/Seller groups with model permissions | Custom role field would duplicate auth infrastructure | Role chosen once at registration; ownership checked in services |
| Admin | Django Admin, controlled offer actions | Custom dashboard duplicates mature tooling | Staff access only; immutable engagement identity/status fields |
| Workflow | Offers only; pending → accepted → completed or rejected | Checkout needs payments/refunds/orders | Row locks and atomic writes; invalid retries rejected |
| Reviews | One review per completed offer | Multiple reviews complicate trust and aggregation | Offer lock plus unique constraint; seller derived server-side |
| Deletion | Protect referenced data; archive listings with offers | Cascades erase engagement evidence | Intentional limitation: only unused listings can be deleted |
| Search | ORM title/description icontains and category | Full-text/trigram useful later | B-tree title index does not accelerate arbitrary substring matching |
| Architecture | Monolith; one domain app and shared services | Microservices multiply deployment and consistency work | Single release and database transaction boundary; single-node outage risk |

The HTML and API layers validate input shape, then call services for authorization and state changes. Transaction boundaries are in services. Authentication, validation and template rendering use Django defaults wherever practical. Admin offers are read-only with explicit actions; administrators act through controlled transitions, using the listing owner context. Audit logging of these custom actions is a future improvement.

Implemented: local database-backed workflows, session auth, model constraints/indexes/migrations, role and ownership restrictions, compiled styling, REST APIs, tests and local reports. Configured but not connected: Supabase production database and Linux Gunicorn/WhiteNoise deployment. Proposed only: load balancing, CDN, cache, workers, replicas, advanced search and larger instances. No billing, messaging, analytics tracking or paid integration is implemented.

Operational gaps: no login rate limiter, password-reset email flow, email verification, production load test, alerting or restore drill. These were outside the specified MVP; assess them before a public launch. No claim is made that sample costs establish production capacity. One million registered users requires workload measurements, staged load tests, connection limits, cache strategy and a database growth/retention plan.

CI configuration uses GitHub Actions with an ephemeral PostgreSQL service container to reproduce the required database tests. This is test infrastructure only; the application itself does not require Docker. The workflow is prepared but has not run on GitHub because no repository connection is configured.
