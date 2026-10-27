# Sources and disclosure

AI assistance: OpenAI Codex generated application code, styling, test cases, documentation and report builders from the user's specification. The developer should independently review the code, explain the architecture and demonstrate the workflow. No external integration or recording is claimed complete without verification.

Original local visuals are CSS typography and geometric shapes. Demo seller names and listings are fictional. No scraped reviews, stock photography or externally sourced customer claims are used.

Direct dependencies: Python (PSF license); Django (BSD-3-Clause); Django REST Framework (BSD); psycopg (LGPL-3.0 family; consult installed distribution); dj-database-url (BSD); python-dotenv (BSD-3-Clause); WhiteNoise (MIT); Gunicorn (MIT); Tailwind CSS (MIT). Retain upstream notices. Transitive dependency license review is not a legal audit. Report generation uses the provided artifact-tool and ReportLab runtime; these are not application runtime requirements.

Primary references accessed 2026-10-25:

- Django querysets/row locking: https://docs.djangoproject.com/en/5.2/ref/models/querysets/#select-for-update
- Hostinger VPS public pricing: https://www.hostinger.com/vps-hosting
- AWS Lightsail pricing: https://aws.amazon.com/lightsail/pricing/
- AWS bundle specifications: https://docs.aws.amazon.com/lightsail/latest/userguide/amazon-lightsail-bundles.html
- Supabase pricing: https://supabase.com/pricing

The cost workbook uses public prices where marked, separates assumptions, excludes tax and engineering labor, and uses Hostinger renewal rather than introductory pricing. Region availability, checkout terms, resource suitability and large-scale budgets are not verified purchases. Django users do not consume Supabase Auth MAU quotas.

Verification: automated test output and JSON are in evidence. Tests use actual database transactions, with the engine identified in the evidence. HTML response tests do not establish visual correctness. Computer Use ended because the current browser URL could not be determined with sufficient confidence to enforce policy; visual browser QA and recording remain incomplete. Locally generated PDFs are explicitly drafts, not Lucidchart exports.
