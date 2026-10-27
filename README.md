# SkillMarket

A compact Django marketplace: sellers publish services, buyers propose offers, sellers accept/reject and complete engagements, and buyers review completed work. There are no payments, carts, real-time messages or external authentication providers.

## Run locally

Requires Python 3.12. Node.js is only required when changing CSS; compiled CSS is committed.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe manage.py migrate
.\.venv\Scripts\python.exe manage.py createsuperuser
.\.venv\Scripts\python.exe manage.py runserver
```

Open http://127.0.0.1:8000/. Register separate Buyer and Seller accounts. The `.env.example` explicitly enables SQLite for offline evaluation. The production database is PostgreSQL; set `DATABASE_URL` to use it. `SKILLMARKET_DEBUG` overrides `DEBUG` because some development environments already define a non-boolean DEBUG variable.

Optional fictional demo data:

```powershell
$env:DEMO_PASSWORD='choose-a-local-password-at-least-12-characters'
.\.venv\Scripts\python.exe manage.py seed_demo
```

This creates six sellers and `demo.buyer`, with the supplied password. Existing passwords are not changed. Demo seeding is disabled outside debug mode. Seeded services are real database rows, explicitly marked fictional.

## Verify

```powershell
.\.venv\Scripts\python.exe manage.py test marketplace
.\.venv\Scripts\python.exe scripts/run_tests.py
.\.venv\Scripts\python.exe manage.py check
.\.venv\Scripts\python.exe manage.py makemigrations --check --dry-run
npm.cmd ci
npm.cmd run build:css
.\.venv\Scripts\python.exe manage.py collectstatic --noinput
```

The evidence runner writes per-case results and a transcript under `submission/03_Marketplace/evidence/`. All 30 tests passed on both SQLite and an isolated local PostgreSQL 18 instance. Tests cover browser forms and APIs, roles, ownership, CSRF, lifecycle, invalid content/prices/ratings, retries and duplicate reviews. Latest evidence uses PostgreSQL; the separate `*-sqlite` files retain the earlier run. This verifies sequential transactions, not a concurrent load test or a Supabase connection.

## Stack and structure

Python 3.12, Django 5.2 LTS, Django REST Framework, Django templates, Tailwind CSS 4, vanilla JavaScript, psycopg, PostgreSQL, WhiteNoise and Gunicorn on Linux. `config/` owns settings and URLs. `marketplace/models.py` defines three domain models. `services.py` centralizes authorized transactional writes. HTML views and DRF endpoints call those same functions. Django's built-in User, Groups and Permissions are retained. `0002_roles` provisions the Buyer/Seller groups and model permissions.

Public listing discovery is paginated. Dashboards are intentionally simple and load the user's records; dashboard pagination is a future scaling improvement. Title/description substring search uses the ORM. The title B-tree index is not claimed to optimize arbitrary `icontains`; consider PostgreSQL trigram indexes after measuring search workloads.

## Supabase and production

1. Use the existing SkillMarket Supabase project. Obtain the PostgreSQL connection string from its Connect panel and put it in the ignored `.env` or the hosting secret manager. Do not use a Supabase API key as a database password. URL-encode special characters in credentials.
2. Prefer a direct or session-pooler connection for migrations and normal Django sessions. Use `sslmode=require`. Server-side cursors are disabled for pooler compatibility. The app uses Django authentication, not Supabase Auth.
3. Set `SKILLMARKET_DEBUG=False`, a random `SECRET_KEY`, `ALLOWED_HOSTS` and HTTPS `CSRF_TRUSTED_ORIGINS`. Set `USE_SQLITE=False`. Production refuses to start without a database URL or secret key. Never use the sample secret in production.
4. Install dependencies, run `migrate`, then `collectstatic --noinput`. On Linux run `gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 2` behind an HTTPS reverse proxy. Configure the proxy and forwarded-protocol trust deliberately; the project does not blindly trust forwarded headers.
5. Run `manage.py check --deploy`. Verify HTTPS, cookies, database backups, a restore procedure, admin access and the full offer workflow before opening access.
6. Keep Django-managed tables inaccessible to Supabase anon/authenticated Data API roles. This app accesses PostgreSQL server-side. Disable the Data API or explicitly revoke access to its exposed application schema; Django permissions do not secure a separately exposed Supabase API.

Offer transitions lock database rows inside atomic transactions. Reviews lock the related offer and use a database one-to-one constraint. Listings with offers cannot be deleted: archive them as Draft. Draft listing details are private to their owner. Admins moderate listings/reviews and use controlled offer actions. Direct database writes remain a privileged administrative operation.

## Submission and honest gaps

See `submission/submission-index.md` and `submission/03_Marketplace/links.md`. The local source, migrations, automated tests, API specification, engineering decisions, cost workbook and test workbook are provided. Diagram PDFs are clearly marked local drafts: they are not Lucidchart exports, and editable Lucidchart links still require account access. GitHub publishing, Supabase project connection, Drive upload and the accessible 3–5 minute recording are not claimed complete. Browser visual verification was blocked by the Computer Use URL-confidence policy. No load test or production security audit has been performed.

The source is prepared for the existing SkillMarket repository, whose owner/URL was not supplied. No remote repository or hosted database was guessed or modified.
