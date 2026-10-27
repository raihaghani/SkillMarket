# SkillMarket API specification

Base URL: `/api/`. JSON requests/responses. SessionAuthentication only. Log in through `/login/`, retaining the session cookie. Send the current `csrftoken` cookie as `X-CSRFToken` for writes. Login itself requires the hidden form CSRF token. CSRF tokens rotate on login: read the cookie again. Postman should retain cookies and set the CSRF header. No bearer tokens are issued.

Lists return `{count, next, previous, results}` with 12 records per page. Pass `page=2` to paginate. Decimal prices are JSON strings with two decimal places. Timestamps are UTC ISO-8601. IDs are database-generated. Usernames are public seller identities; emails, passwords and session details are never returned.

| Method | Route | Access / behavior |
|---|---|---|
| GET | `/api/listings/?q=website&category=Web%20Development` | Public, active listings only; title/description search and exact category |
| GET | `/api/listings/{id}/` | Public active listing; drafts return 404 |
| POST | `/api/listings/` | Seller; seller identity assigned from session |
| PATCH | `/api/listings/{id}/` | Owning seller only |
| DELETE | `/api/listings/{id}/` | Owning seller; 204 without history, 400 if offers exist |
| GET | `/api/offers/` | Buyer sees own; seller sees received offers |
| POST | `/api/offers/` | Buyer; active listing from another user |
| POST | `/api/offers/{id}/accept/` | Owner; PENDING to ACCEPTED |
| POST | `/api/offers/{id}/reject/` | Owner; PENDING to REJECTED |
| POST | `/api/offers/{id}/complete/` | Owner; ACCEPTED to COMPLETED |
| POST | `/api/reviews/` | Associated buyer; completed engagement; once only |
| GET | `/api/listings/{id}/reviews/` | Public reviews of active listing |

## Examples

Create listing (201):
```json
{"title":"Build a Django website","description":"A carefully crafted website for your small business.","category":"Web Development","starting_price":"150.00","status":"ACTIVE"}
```
Response includes those fields plus `id`, `seller`, `seller_name`, `created_at`, `updated_at`. `status` defaults to ACTIVE; INACTIVE means Draft.

Submit offer (201):
```json
{"listing":1,"offered_price":"120.00","message":"Please build a portfolio website with three pages."}
```
Response:
```json
{"id":1,"listing":1,"buyer":2,"offered_price":"120.00","message":"Please build a portfolio website with three pages.","status":"PENDING","created_at":"2026-10-25T10:00:00Z","updated_at":"2026-10-25T10:00:00Z"}
```
IDs and timestamps here are illustrative, not evidence. Accept/reject/complete need an empty body and return the updated offer (200). Repeating accept is a 400; the original accepted state is preserved. Repeated creation of an offer is a new offer, not an idempotent retry.

Review (201):
```json
{"offer":1,"rating":5,"comment":"Excellent communication and thoughtful work."}
```
Response adds `id`, `reviewer`, `seller`, `created_at`. Reviewers and sellers are derived from the session/engagement, not client identity fields. Reviews are publicly readable with the listing. There is no user-facing review edit/delete endpoint; moderation is in Django Admin.

## Validation and errors

Prices: 0.01 through 99,999,999.99 with at most two decimal places. Title: 5–200 characters. Description: 20–10,000. Offer message: 10–5,000. Review comment: 10–2,000. Rating: integer 1–5. Forms and serializers trim text; blank values are rejected. Categories are the six documented choices. Listing and offer statuses have database constraints. Identity and lifecycle fields are read-only in serializers.

- 400: field validation, archived listing offer, invalid transition, duplicate review, attempted deletion of history.
- 403: unauthenticated session writes, CSRF rejection, wrong role, listing ownership failure, unrelated review. SessionAuthentication normally uses 403 rather than a bearer-style 401 challenge.
- 404: missing or non-public listing; private offer outside the caller's queryset. An invalid foreign key in a create body is a 400 serializer error.
- 405: unsupported method (for example PATCH on offers or GET on a status-action route).

Field errors use `{"rating":["Ensure this value is less than or equal to 5."]}`. Permission/missing-object errors use `{"detail":"..."}`. Service errors may be a list of human-readable messages. Clients must not depend on exact wording.

Private offer filtering and shared service authorization apply independently. Admin oversight is provided by Django Admin, not a bypass in the marketplace API.
