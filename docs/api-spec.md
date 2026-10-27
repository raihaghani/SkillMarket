# SkillMarket REST API

Verified against the implementation and isolated SQLite tests on 27 October 2026. Local base URL: `http://127.0.0.1:8000`. Paths below include trailing slashes. Examples use JSON (`Content-Type: application/json`, `Accept: application/json`); IDs, names and timestamps are illustrative.

## 1. API overview

Django REST Framework exposes listings, offers and reviews under `/api/`. Relationships are integer IDs, money is serialized as a decimal string, and timestamps are ISO 8601 UTC strings. There is no JWT/token endpoint, REST registration/login endpoint, payment API or notification API.

| Method / path | Purpose and access | Request | Success | Relevant failures |
| --- | --- | --- | --- | --- |
| GET `/api/` | API discovery; authenticated account | No body | 200; links to listings, offers, reviews | 403 without session |
| GET `/api/listings/` | Public published catalog | Optional q, category, page | 200; paginated Listing objects | 404 invalid page |
| POST `/api/listings/` | Create; Seller | Listing input below | 201; Listing | 400 invalid fields; 403 auth/role/CSRF |
| GET `/api/listings/{id}/` | Public published listing | No body | 200; Listing | 404 missing/draft or excluded by filters |
| PATCH `/api/listings/{id}/` | Edit; owning Seller | Any writable listing fields | 200; Listing | 400 invalid fields; 403 auth/role/ownership/CSRF; 404 missing |
| DELETE `/api/listings/{id}/` | Delete unused listing; owning Seller | No body | 204; empty body | 400 listing has offers; 403 auth/role/ownership/CSRF; 404 missing |
| GET `/api/listings/{id}/reviews/` | Public reviews for a published listing | Optional page (and listing q/category filters) | 200; paginated Review objects | 404 missing/draft/filtered listing or invalid page |
| GET `/api/offers/` | Private offers; authenticated | Optional page | 200; paginated Offer objects | 403 without session; 404 invalid page |
| POST `/api/offers/` | Submit; Buyer | Offer input below | 201; Offer with PENDING status | 400 invalid input/listing eligibility; 403 auth/role/CSRF |
| POST `/api/offers/{id}/accept/` | Accept; owning Seller | No fields; `{}` or empty body | 200; Offer with ACCEPTED status | 400 wrong current state; 403 auth/role/CSRF; 404 inaccessible/missing |
| POST `/api/offers/{id}/reject/` | Reject; owning Seller | No fields; `{}` or empty body | 200; Offer with REJECTED status | Same as accept |
| POST `/api/offers/{id}/complete/` | Complete; owning Seller | No fields; `{}` or empty body | 200; Offer with COMPLETED status | Same as accept |
| POST `/api/reviews/` | Review own completed offer; Buyer | Review input below | 201; Review | 400 invalid input/not completed/duplicate; 403 auth/role/ownership/CSRF |

The authenticated API root returns:

```json
{"listings":"http://127.0.0.1:8000/api/listings/","offers":"http://127.0.0.1:8000/api/offers/","reviews":"http://127.0.0.1:8000/api/reviews/"}
```

Framework routes: HEAD is available on GET-capable paths (same access checks, no response body); OPTIONS supplies DRF metadata. Listing OPTIONS requires authentication, even though listing GET is public. Other OPTIONS requests inherit the authenticated default. DefaultRouter also creates format-suffix aliases such as `/api/listings.json`; they are representations of the same endpoints, not new features.

Not implemented: PUT listing replacement; GET/PATCH/DELETE `/api/offers/{id}/`; GET `/api/reviews/`; review detail/edit/delete routes. An existing route with an unsupported method returns 405 after applicable permission checks; an absent route returns 404. Unknown routes may use Django HTML errors rather than DRF JSON.

## 2. Authentication

The API uses **Django session authentication** and the `sessionid` cookie. Establish a session through the HTML `/login/` form; `/register/` creates an account and assigns the selected Buyer or Seller group. These are HTML flows, not JSON authentication APIs. The HTML logout endpoint accepts POST.

For session-authenticated POST, PATCH and DELETE requests, send a valid CSRF token (typically the `csrftoken` cookie value in `X-CSRFToken`) along with the session cookie. Obtain the token from a rendered form page; use the current token after login. HTTPS origin/referer checks also apply where configured. A client may use separate Buyer and Seller sessions; one session is not implicitly switched by sending a different buyer/seller ID.

Public listing GET operations permit anonymous access. Protected anonymous requests return **403**, not 401, because SessionAuthentication does not issue a WWW-Authenticate challenge. Invalid CSRF and failed role/ownership checks also return 403. There is no automatic admin/superuser bypass for marketplace API business rules.

Offers are scoped before object lookup: accounts in Seller group see offers for their listings; otherwise the queryset is limited to offers where they are the buyer. Accounts in both groups follow the Seller branch. This scoping explains why another seller gets 404. A Buyer accepting their own visible offer instead reaches the Seller-role check and gets 403. A Buyer targeting someone else's offer gets 404.

## 3. Listings

### Input and validation

Create requires title, description, category and starting_price. Status is optional and defaults to ACTIVE. PATCH accepts any subset; omitted fields retain their values. Owner can PATCH/DELETE drafts, but REST retrieval of drafts returns 404 even to the owner.

| Writable field | Validation |
| --- | --- |
| title | Nonblank string, 5–200 characters |
| description | Nonblank string, 20–10,000 characters |
| category | Web Development, Graphic Design, Content Writing, Video Editing, SEO, or Digital Marketing |
| starting_price | Decimal >= 0.01; 10 total digits, at most 2 decimal places (at most 8 whole digits) |
| status | ACTIVE (published) or INACTIVE (draft) |

Create example, `POST /api/listings/`:

```json
{"title":"Build a portfolio website","description":"A custom portfolio website for your independent business.","category":"Web Development","starting_price":"150.00","status":"ACTIVE"}
```

Listing response (201 create, 200 retrieve/edit; list pages contain the same objects):

```json
{
  "id": 1, "seller": 2, "seller_name": "api_seller",
  "title": "Build a portfolio website",
  "description": "A custom portfolio website for your independent business.",
  "category": "Web Development", "starting_price": "150.00", "status": "ACTIVE",
  "created_at": "2026-10-27T12:00:00Z", "updated_at": "2026-10-27T12:00:00Z"
}
```

PATCH example: `{"status":"INACTIVE"}` archives the listing and returns its updated full object. DELETE succeeds only if there are no offers, returning 204 without JSON. If offers exist, it returns 400; archive instead to retain history. `id`, `seller`, `seller_name`, `created_at` and `updated_at` are read-only. Seller is derived from the authenticated user, never trusted from input.

For `GET /api/listings/` and `GET /api/listings/{id}/reviews/`, use the pagination envelope in section 6. The reviews endpoint returns Review objects documented below; no rating aggregate is added by these serializers.

## 4. Offers

### Create and list

`POST /api/offers/` requires an authenticated Buyer and all three writable fields:

```json
{"listing":1,"offered_price":"100.00","message":"Please build a portfolio website."}
```

- listing: existing listing ID. A nonexistent related ID is a serializer 400, not a detail-route 404.
- offered_price: decimal >= 0.01, 10 digits total and at most 2 decimal places. Zero, negative, nonnumeric/nonfinite values and excess precision fail with 400.
- message: nonblank string, 10–5,000 characters.

The listing must be ACTIVE and belong to someone other than the buyer. Invalid eligibility returns 400. The service starts an atomic transaction, rereads the listing, validates the model and inserts an Offer. It requests select_for_update locking, but SQLite does not supply PostgreSQL row locks.

Success is 201 with this Offer representation:

```json
{
  "id":1,"listing":1,"buyer":1,"offered_price":"100.00",
  "message":"Please build a portfolio website.","status":"PENDING",
  "created_at":"2026-10-27T12:00:00Z","updated_at":"2026-10-27T12:00:00Z"
}
```

`id`, `buyer`, `status`, `created_at` and `updated_at` are read-only. Supplying buyer/status does not override the authenticated buyer or initial PENDING state. Multiple offers on one listing are allowed. `GET /api/offers/` returns only the current user's scoped offers in the standard pagination envelope, newest first.

### Status actions

Each action accepts an empty body or `{}`. Success is **200** with the full Offer object above, updated status and updated_at. No other response wrapper or notification is added.

| Current status | Action endpoint | New status |
| --- | --- | --- |
| PENDING | POST `/api/offers/{id}/accept/` | ACCEPTED |
| PENDING | POST `/api/offers/{id}/reject/` | REJECTED |
| ACCEPTED | POST `/api/offers/{id}/complete/` | COMPLETED |

All other transitions return 400, including pending-to-completed, rejected-to-completed and repeated accept. The service rereads the offer in an atomic transaction, checks Seller role and listing ownership, checks its current status, then saves status and updated_at. There is no cancellation, reopen, retry-as-success, or general offer-update endpoint.

## 5. Reviews

`POST /api/reviews/` requires an authenticated Buyer reviewing their own completed offer. Required input:

```json
{"offer":1,"rating":5,"comment":"Excellent communication and thoughtful work."}
```

offer must identify an existing offer; rating must be an integer from 1 through 5; comment must be nonblank and 10–2,000 characters. A missing/nonexistent offer or invalid fields returns 400; another buyer's offer returns 403; an incomplete or already-reviewed offer returns 400.

Success is 201:

```json
{
  "id":1,"offer":1,"reviewer":1,"seller":2,"rating":5,
  "comment":"Excellent communication and thoughtful work.",
  "created_at":"2026-10-27T12:05:00Z"
}
```

id, reviewer, seller and created_at are read-only. The service derives reviewer and seller, checks eligibility inside an atomic transaction and creates the review. OneToOneField uniqueness enforces at most one review per offer. Read reviews through `GET /api/listings/{id}/reviews/`; there is no separate review collection GET or mutation API beyond creation.

## 6. Search and filtering

`GET /api/listings/?q=portfolio&category=Web%20Development&page=1` combines title/description case-insensitive substring search with exact category matching. Only ACTIVE listings are returned, newest first. No full-text search, price filter, seller filter, arbitrary ordering or client-controlled page size is configured.

The same listing queryset applies to retrieve and listing-reviews routes: q/category can exclude the requested listing and cause 404. Listing PATCH/DELETE use an unfiltered queryset followed by ownership checks. Offers expose no status filter; their queryset is scoped to the account. Reviews are ordered newest first by their model.

All collection GET responses are paginated, 12 objects per page:

```json
{"count":0,"next":null,"previous":null,"results":[]}
```

With results, the array contains the corresponding Listing, Offer or Review objects. next/previous are absolute page URLs or null. Invalid/out-of-range page values return 404 with `{"detail":"Invalid page."}`. The API root is not paginated.

## 7. HTTP status codes

| Status | Actual use |
| --- | --- |
| 200 | Reads, root discovery, listing PATCH, offer actions; OPTIONS metadata |
| 201 | Listing, offer and review creation |
| 204 | Successful listing deletion; empty response |
| 400 | Serializer/model/business validation; invalid transitions, duplicate review, protected listing deletion; malformed JSON |
| 403 | Protected anonymous request, missing role, visible object ownership failure, or CSRF failure |
| 404 | Missing/inaccessible object, draft/filtered listing, invalid page, or absent route |
| 405 | Unsupported method on an existing route, after permission checks |
| 406 / 415 | DRF unsupported response representation / request media type |

401 normally denotes a challenge-based authentication failure. This application configures only SessionAuthentication, so protected anonymous requests are 403. Other-seller offer access is deliberately 404, masking objects outside the scoped queryset. Error precedence depends on where the request fails: authentication/CSRF occur before handler validation; serializer errors can precede service role checks.

## 8. Error handling

There is no custom error envelope. Permission and not-found exceptions return a `detail` object; serializer/model field errors generally return arrays keyed by field; non-field service ValidationError messages can be a top-level array.

Verified examples:

```json
{"detail":"Authentication credentials were not provided."}
```

403 for protected anonymous access.

```json
{"detail":"A seller account is required."}
```

403 when a Buyer attempts to accept their own visible offer.

```json
{"detail":"No Offer matches the given query."}
```

404 when another Seller attempts to accept an offer outside their queryset. `services.transition()` is not called and no status write occurs.

```json
["This action is not valid for the current offer status."]
```

400 for an invalid/repeated transition. Other service failures include `Offers require an active listing from another seller.`, `Complete the engagement before reviewing it.`, and `This engagement already has a review.` (400 arrays). Review ownership failure returns `{"detail":"You can only review your own engagement."}` (403).

Typical required-field error: `{"message":["This field is required."]}` (400). Multiple field errors may appear together. CSRF failures return 403 with a `detail` beginning `CSRF Failed:`; wording depends on the failure. Error messages reflect the configured English locale and may vary with dependency versions; clients should use status/field structure rather than exact strings.

### Verification and diagram source

Sources: `config/urls.py`, `config/settings.py`, `marketplace/api.py`, `services.py`, `models.py`, `tests.py`, and installed DRF router/serializer behavior. All 30 existing tests passed in an isolated SQLite test database. Additional isolated probes confirmed 201 create, 200 accept/complete, 403 Buyer acceptance, 404 other-Seller acceptance, 400 repeated acceptance, root authentication, and 405 review collection GET. The other-seller rejection left the offer PENDING. Production data was not used or changed.

`api-workflows.pdf` contains the two requested workflows. Editable source and the generator are in `api-workflows-source/`. Authentication, permissions and business logic lifelines are logical portions of the same Django process, not microservices. Internal query-result arrows are selectively omitted for readability; reads/writes and externally observable responses are explicit.

The PDF is a locally generated preview, not a Lucidchart export. Open the draw.io source in diagrams.net, save/export as XML, import that export into Lucidchart, review and export the final PDF. The required editable Lucidchart link and final Lucidchart export remain to be created there; no URL is fabricated. See [Lucid's supported import workflow](https://help.lucid.co/hc/en-us/articles/16389149809428-Import-files-into-Lucidchart). Direct Lucidchart import has not been tested.
