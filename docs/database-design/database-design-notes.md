# SkillMarket database design notes

Verified 27 October 2026. These artifacts document the existing implementation; no models, migrations, application behavior or database schema were changed.

## A. Database overview

The active backend is SQLite (`django.db.backends.sqlite3`) in the local `db.sqlite3` file. No hosted database provider or Supabase connection is configured. PostgreSQL is supported through `DATABASE_URL` and psycopg, but PostgreSQL types are not presented as the active schema. Django 5.2.18 manages the schema through migrations.

The user model is Django's built-in `auth.User`, not a custom model. Buyer and Seller are rows in `auth_group`, linked through `auth_user_groups`; there is no role column. The default application ID field is BigAutoField, while built-in auth models use AutoField. Both resolve to SQLite INTEGER primary keys; FK references to BigAutoField resolve to BIGINT. This difference is intentional and matches the inspected schema.

The PDF has three pages: marketplace ERD, authentication/permissions ERD, and integrity/index notes. Numeric min/max notation is used consistently: each child requires one parent; each parent may have zero to many children, except Offer may have zero or one Review. The User box on page 2 is a reference to the same table on page 1, showing only its key and username. It is not another entity.

## B. Table summary

| Table | Purpose | PK | Foreign keys | Important constraints |
| --- | --- | --- | --- | --- |
| auth_user | Accounts, credentials and status flags | id | None | username unique; email not unique; last_login nullable |
| marketplace_listing | Seller service listing | id | seller_id -> auth_user.id | positive price; ACTIVE/INACTIVE status |
| marketplace_offer | Buyer proposal and engagement state | id | buyer_id -> auth_user.id; listing_id -> marketplace_listing.id | positive price; four allowed statuses |
| marketplace_review | Feedback for one completed engagement | id | offer_id -> marketplace_offer.id; reviewer_id and seller_id -> auth_user.id | offer_id unique; rating between 1 and 5 |
| auth_group | Buyer/Seller roles and other possible groups | id | None | name unique |
| auth_user_groups | Account-to-role membership | id | user_id, group_id | pair unique |
| auth_permission | Model permission definitions | id | content_type_id -> django_content_type.id | content_type_id + codename unique |
| auth_group_permissions | Permission grants to groups | id | group_id, permission_id | pair unique |
| auth_user_user_permissions | Direct permission grants supported by Django | id | user_id, permission_id | pair unique |
| django_content_type | App/model identity for permissions | id | None | app_label + model unique |

`django_session`, `django_admin_log`, and migration bookkeeping exist as Django infrastructure and are intentionally outside the main ERD. Direct user permissions are supported by the existing schema; role seeding grants permissions through groups, not this direct join.

## C. Relationships and deletion

- User (seller) 1 -> 0..N Listing via seller_id.
- User (buyer) 1 -> 0..N Offer via buyer_id.
- Listing 1 -> 0..N Offer via listing_id.
- Offer 1 -> 0..1 Review via unique offer_id; every Review has exactly one Offer.
- User (reviewer) 1 -> 0..N Review via reviewer_id.
- User (seller) 1 -> 0..N Review via seller_id.
- User and Group are many-to-many through auth_user_groups; both join foreign keys are mandatory.
- Group and Permission are many-to-many through auth_group_permissions.
- User and Permission are many-to-many through auth_user_user_permissions.
- ContentType 1 -> 0..N Permission.

All marketplace FKs use Django `on_delete=PROTECT`. The auth/content-type FKs shown use Django `CASCADE`. These are Django deletion-collector behaviors, not SQL ON DELETE CASCADE/RESTRICT clauses. Live SQLite foreign-key metadata reports NO ACTION for update/delete; references are DEFERRABLE INITIALLY DEFERRED. Direct SQL must still satisfy referential integrity when foreign keys are enabled. The application enables SQLite foreign keys; inspection reported zero violations.

## D. Indexes and query purposes

The five explicit marketplace indexes are confirmed in the initial migration and live schema:

| Index | Columns | Supported access pattern |
| --- | --- | --- |
| marketplace_status_a6670d_idx | Listing(status, category) | Published catalog with category filtering |
| marketplace_seller__639ce1_idx | Listing(seller_id, status) | Seller-owned listings, optionally filtered by status |
| marketplace_title_7bdd5a_idx | Listing(title) | Title ordering/equality; not a general accelerator for arbitrary icontains search |
| marketplace_buyer_i_b1e5a0_idx | Offer(buyer_id, status) | Buyer dashboard and optional status filtering |
| marketplace_listing_6b4340_idx | Offer(listing_id, status) | Offers for a listing and optional status filtering |

Foreign-key indexes support joins, related-object retrieval and parent-deletion checks. Unique indexes enforce membership pairs, permission identity, usernames/group names, and one review per offer. A composite index is not evidence of separate standalone indexes on each component: there is no explicit category-only or offer-status-only index. Query benefit depends on plans and workload; no performance benchmark is claimed. SQLite INTEGER PRIMARY KEY aliases the rowid, using its B-tree without a separate PK index.

### Confirmed constraint/index inventory

The inventory below includes indexes and unique constraints returned by Django introspection. `__unnamed_constraint_*__` are Django inspection identifiers for inline unique constraints, not literal SQLite index names; SQLite backs these with autoindexes. Full DDL, column metadata, foreign keys and introspected constraints are retained in `schema-verification.json` (schema only; no account rows or secrets).

#### auth_permission

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| auth_permission_content_type_id_2f476e4b | content_type_id | No |
| auth_permission_content_type_id_codename_01ab375a_uniq | content_type_id, codename | Yes |

#### auth_group_permissions

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| auth_group_permissions_permission_id_84c5c92e | permission_id | No |
| auth_group_permissions_group_id_b120cbf9 | group_id | No |
| auth_group_permissions_group_id_permission_id_0cd325b0_uniq | group_id, permission_id | Yes |

#### auth_group

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| __unnamed_constraint_1__ | name | Yes |

#### auth_user_groups

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| auth_user_groups_group_id_97559544 | group_id | No |
| auth_user_groups_user_id_6a12ed8b | user_id | No |
| auth_user_groups_user_id_group_id_94350c0c_uniq | user_id, group_id | Yes |

#### auth_user_user_permissions

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| auth_user_user_permissions_permission_id_1fbb5f2c | permission_id | No |
| auth_user_user_permissions_user_id_a95ead1b | user_id | No |
| auth_user_user_permissions_user_id_permission_id_14a6b632_uniq | user_id, permission_id | Yes |

#### auth_user

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| __unnamed_constraint_1__ | username | Yes |

#### django_content_type

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| django_content_type_app_label_model_76bd3d3b_uniq | app_label, model | Yes |

#### marketplace_listing

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| marketplace_title_7bdd5a_idx | title | No |
| marketplace_seller__639ce1_idx | seller_id, status | No |
| marketplace_status_a6670d_idx | status, category | No |
| marketplace_listing_seller_id_56a0f16d | seller_id | No |

#### marketplace_offer

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| marketplace_listing_6b4340_idx | listing_id, status | No |
| marketplace_buyer_i_b1e5a0_idx | buyer_id, status | No |
| marketplace_offer_listing_id_ab2831b2 | listing_id | No |
| marketplace_offer_buyer_id_c8d440ec | buyer_id | No |

#### marketplace_review

| Index / unique constraint | Columns | Unique |
| --- | --- | --- |
| __unnamed_constraint_2__ | offer_id | Yes |
| marketplace_review_seller_id_eb282ce5 | seller_id | No |
| marketplace_review_reviewer_id_b90e91d7 | reviewer_id | No |

## E. Integrity: database versus application

Database checks verified in SQLite DDL:

- `listing_positive_price`: starting_price > 0.
- `listing_valid_status`: status IN ('ACTIVE', 'INACTIVE').
- `offer_positive_price`: offered_price > 0.
- `offer_valid_status`: status IN ('PENDING', 'ACCEPTED', 'REJECTED', 'COMPLETED').
- `review_rating_range`: rating >= 1 AND rating <= 5. PositiveSmallIntegerField additionally produces a rating >= 0 check.
- Review.offer_id is UNIQUE; all marketplace columns and FKs are NOT NULL.

Username and group name are unique. The three auth joins have unique FK pairs. Permission identity is unique by content type and codename; content type identity is unique by app label and model. `last_login` is the only nullable column among the depicted tables. `blank=True` allows form-level empty input without making a database column nullable; empty email is allowed and email is not unique.

`services.py` enforces role membership, listing ownership, active listings from another seller, allowed offer transitions, and reviews only by the offer buyer after completion. It sets Review.reviewer and Review.seller from the engagement. Those cross-table consistency rules are not database constraints. Full model validation and forms/serializers add min/max lengths, category choices, decimal precision and value validators. Plain model save or direct SQL does not automatically apply full_clean.

Listing.status defaults to ACTIVE and Offer.status to PENDING at the Django level. created_at uses auto_now_add; updated_at uses auto_now. User flags default to is_superuser=False, is_staff=False and is_active=True; date_joined defaults to Django timezone.now. Nullable last_login can be NULL. String fields can receive implicit empty strings through Django. The inspected tables have no persistent database DEFAULT clauses for these values and no timestamp-update triggers. Primary keys use SQLite AUTOINCREMENT; these are generated keys rather than ordinary column defaults.

Atomic transactions wrap offer transitions and reviews. PostgreSQL-style select_for_update row locks are not provided by SQLite. Uniqueness still protects against duplicate Review rows.

## F. Known gaps and differences from a conceptual design

- SQLite is configured, not hosted PostgreSQL/Supabase. DecimalField(10,2) is declared as DECIMAL in SQLite; SQLite does not enforce scale/precision like PostgreSQL NUMERIC(10,2). VARCHAR and TextField length limits are validated by Django, not enforced by this SQLite schema.
- Category values are application choices without a database CHECK. Listing/offer statuses do have database CHECKs.
- No database constraint ensures Review.reviewer equals Offer.buyer or Review.seller equals Listing.seller, nor that the offer is completed. Normal service calls enforce these requirements.
- No database constraint forces one role per user, restricts group names to Buyer/Seller, or requires the seller/buyer FK target to hold that role. Registration assigns one selected group; authorization checks group membership.
- There is no unique buyer/listing offer pair, so multiple offers by the same buyer on the same listing are permitted. Only duplicate reviews for a single offer are prevented.
- Auth model permissions are seeded, while marketplace services chiefly enforce explicit role and ownership rules. A foreign key is not an authorization boundary.
- No missing migrations were detected. All applied migrations and schema checks were inspected; this is not a data-consistency audit of business rules, load test or production deployment validation.

## G. Verification sources and reproduction

Inspected project sources:

- `marketplace/models.py` (the only application models.py)
- `marketplace/migrations/0001_initial.py` (all domain fields, relationships, checks and five explicit indexes)
- `marketplace/migrations/0002_roles.py` (Buyer/Seller groups and permission grants)
- `marketplace/services.py`, `marketplace/forms.py`, `marketplace/api.py`, `marketplace/admin.py`
- `config/settings.py`, `requirements.txt`, `.env.example`; effective environment inspected without recording secrets
- Installed Django auth/contenttypes model metadata and auto-created many-to-many through models
- Live SQLite `sqlite_master`, `PRAGMA table_info`, `PRAGMA foreign_key_list`, and Django constraint introspection

Verification commands: `manage.py showmigrations --plan` showed every migration applied; `manage.py makemigrations --check --dry-run` reported No changes detected; MigrationExecutor reported zero pending migrations; PRAGMA foreign_key_check returned no rows. Field names/types/nullability, FK targets, checks and indexes were compared with models and migrations. The PDF is rendered to PNG and visually reviewed; the editable XML is parsed and checked for three pages.

To regenerate from the committed schema snapshot, run `.\.venv\Scripts\python.exe docs/database-design/build_erd.py` from the project root. It requires ReportLab, pypdfium2 and Windows Arial fonts. It reads the schema snapshot and writes documentation only; refresh the snapshot after schema changes before rebuilding.

## H. Lucidchart finalization

`database-design.drawio` is editable uncompressed draw.io XML with three matching pages. The PDF was generated locally, not exported from Lucidchart. No Lucidchart URL is claimed. Open the source in diagrams.net and save/export as draw.io XML, then import that export into Lucidchart, inspect the layout and export as `database-design.pdf`. Direct import has not been tested. Lucid requires draw.io-exported files; see its [import instructions](https://help.lucid.co/hc/en-us/articles/16389149809428-Import-files-into-Lucidchart).
