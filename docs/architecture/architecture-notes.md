# SkillMarket system architecture

Verified on 27 October 2026 for the FalconXoft Weekend Engineering Assignment.

## Deliverables and status

- `architecture.pdf`: two-page vector PDF. Page 1 shows implementation and deployment boundaries; page 2 traces the four required request/response flows.
- `architecture.drawio`: editable, uncompressed draw.io XML with matching pages, rectangles, text and directional connectors.
- `build_architecture.py`: reproducible generator for both artifacts (ReportLab, pypdfium2 and Windows Arial fonts required).

This is a locally generated PDF preview, **not a Lucidchart export**. No editable Lucidchart URL has been created. For a Lucidchart-finalized submission, open the source in diagrams.net, save/export it as a draw.io XML file, import that export into Lucidchart, check both pages and export the final PDF as `architecture.pdf`. Lucid documents draw.io import support but requires files exported from draw.io; direct import of this generated source has not been tested. See [Lucid's import instructions](https://help.lucid.co/hc/en-us/articles/16389149809428-Import-files-into-Lucidchart).

## Actual deployment and database

The effective Django settings resolve to `django.db.backends.sqlite3`, using `db.sqlite3` in the project root. A read-only `SELECT 1` succeeded. The current environment has `SKILLMARKET_DEBUG=True`, `USE_SQLITE=True`, and no nonempty `DATABASE_URL`. Credentials and secret values are intentionally omitted from these artifacts.

No Supabase connection is configured. The existing code supports PostgreSQL through `DATABASE_URL`, dj-database-url and psycopg. A Linux Gunicorn entry point exists in `Procfile`; that is deployment support, not evidence of a running hosted instance. No remote deployment was verified. Application and database are therefore shown within the **Local Development Environment**, with a nested local database-storage boundary rather than an invented separate database host.

The client-device boundary is logical: the browser can run on the same workstation as the development server. Local traffic is HTTP. HTTPS production hosting is not depicted as already deployed.

## Components and movement

- **Presentation:** Django renders templates into HTML. The browser loads compiled Tailwind CSS and vanilla JavaScript. `static/app.js` only adds form confirmation prompts; it is not a SPA or an API client. Django staticfiles handles development assets; WhiteNoise and compressed manifest storage are configured for static serving after collection.
- **Routing and validation:** `config/urls.py` dispatches to HTML views, the DRF router or Django Admin. HTML forms and API serializers validate inputs. The DRF API exposes listings, offers and reviews.
- **Shared business logic:** `marketplace/services.py` implements listing discovery/mutations, authorized offer transitions and eligible reviews. HTML and API writes call these functions. Read-only views/viewsets also query the ORM directly. The diagram's service-to-ORM layer is not a claim that every database query passes through services.
- **Authentication and authorization:** Django sessions and authentication identify users. Middleware provides CSRF protection; DRF uses session authentication. Buyer/Seller groups and Django model permissions are provisioned by migration. Marketplace access mainly uses explicit role, ownership and lifecycle checks, rather than automatically applying model permissions to every API call. Admin enforces staff/model permissions. These are cross-cutting controls in the Django process, not a standalone authentication service.
- **Data:** Django ORM manages Listing, Offer and Review along with built-in user, group, permission and session records. Offer/review writes use atomic transactions. SQLite does not provide PostgreSQL's row-level `select_for_update()` locking semantics.
- **Administration:** ModelAdmin manages listings and review moderation. Offers are read-only in the edit form, with controlled status actions calling `services.transition()` using the listing seller as the domain actor. Admin cannot add/delete offers or add reviews through these registered admin screens.

The second page explicitly shows browsing, offer submission, REST API requests and administration, including return paths. Flow boxes group several in-process operations; they are not independently deployed services. Bidirectional data arrows represent queries/results. The dashed line on page 1 shows the presentation response; dashed return paths on page 2 show responses. The authentication panel describes controls applied across handlers without adding crossing policy connectors.

## Verified technologies and source inventory

| Technology / concern | Verified implementation or configuration |
| --- | --- |
| Python 3.12; Django 5.2.18 installed | `.venv`, `requirements.txt`, `requirements-lock.txt`, `manage.py` |
| Django REST Framework 3.16.1 installed | `marketplace/api.py`, `config/urls.py`, `config/settings.py` |
| Django templates / HTML | `templates/base.html`, `home.html`, `detail.html`, `buyer.html`, `seller.html`, `form.html`, `login.html` |
| Tailwind CSS 4 | `package.json`, `package-lock.json`, `assets/input.css`, compiled `static/app.css` |
| Vanilla JavaScript | `static/app.js`, script reference in `templates/base.html` |
| HTML handlers and forms | `marketplace/views.py`, `marketplace/forms.py`, `marketplace/context.py` |
| Role / ownership / offer / review logic | `marketplace/services.py`, `marketplace/migrations/0002_roles.py` |
| ORM models and schema | `marketplace/models.py`, `marketplace/migrations/0001_initial.py` |
| Django Admin | `marketplace/admin.py`, `/admin/` route in `config/urls.py` |
| SQLite active | Effective `config/settings.py`, redacted `.env` inspection and read-only connection check |
| PostgreSQL support; psycopg 3.3.6 installed | `requirements.txt`, `config/settings.py`; not the active backend |
| python-dotenv 1.2.4; dj-database-url 3.1.2 installed | `config/settings.py`, `.env.example`; `.env` values inspected without exposing secrets |
| WhiteNoise 6.12.0 installed | Middleware and static storage settings in `config/settings.py` |
| Gunicorn deployment support | `Procfile`, `config/wsgi.py`, non-Windows dependency in `requirements.txt`; not claimed running |

## Exclusions and validation

No runtime external service was found in the inspected implementation. GitHub, Postman and Lucidchart are development/documentation tools and are excluded from the runtime architecture. There are no implemented payment providers, external authentication providers, background workers, message brokers, separate frontend servers or external object storage in this diagram.

The earlier `submission/03_Marketplace/architecture.pdf` is a separate draft and was not overwritten. This new diagram reflects the currently active SQLite configuration. Application functionality and settings were not modified. Checks for this documentation are source comparison, effective-settings inspection, a read-only database query, XML parsing and rendered-PDF visual inspection; no load test, deployment verification or Lucidchart import validation is claimed.
