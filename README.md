# CODING AI — Academic Registration Portal

A **single-file HTML frontend** (Tailwind CDN + Vanilla JS + jsPDF only) connected to a **Django + PostgreSQL** backend.
The wizard runs **1 DETAILS → 2 SCAN → 3 SUBMIT**. The certificate image is converted to PDF inside the browser, then sent with the four fields in **one** `multipart/form-data` POST request.

> **UI language & theme:** all interface text is in **English** and the interface is **dark-only** — there is no light mode and no theme switch. The page direction is LTR.

> **Logo note:** the `image.png` mentioned in the original brief was not attached to the workspace, so it was redrawn from the description (blue `<` + red `>` with light circuit dots and red "CODING AI" text) and saved as `image.png`. It is **embedded in `index.html` as a base64 data URI**, so the frontend stays a single file with no external image dependency. To use your original logo, replace `image.png` and update the `src` of `.brand-logo` and `.success-logo` (snippet at the bottom).

## Files

```
.
├── index.html                      # Full UI (HTML + CSS + JS + embedded logo)
├── image.png                       # Reference logo (also embedded in index.html)
├── README.md                       # This file
└── backend/
    ├── manage.py
    ├── requirements.txt            # Django + psycopg + django-cors-headers
    ├── .env.example                # Environment variables
    ├── config/
    │   ├── settings.py             # PostgreSQL + CORS + MEDIA + upload limits
    │   ├── urls.py                 # /api/ + media serving in development
    │   ├── wsgi.py / asgi.py
    │   └── __init__.py
    └── registrations/
        ├── models.py               # Registration + organized upload path
        ├── views.py                # POST /api/registrations/ (validation + save + JSON)
        ├── urls.py
        ├── apps.py
        └── migrations/0001_initial.py
```

## 1) Prepare PostgreSQL

```sql
CREATE DATABASE coding_ai;
CREATE USER coding_user WITH PASSWORD 'strong-password';
ALTER ROLE coding_user SET client_encoding TO 'utf8';
GRANT ALL PRIVILEGES ON DATABASE coding_ai TO coding_user;
```

## 2) Run the backend (Django)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

# Environment variables (or copy .env.example to .env, then: set -a; source .env; set +a)
export POSTGRES_DB=coding_ai
export POSTGRES_USER=coding_user
export POSTGRES_PASSWORD=strong-password
export POSTGRES_HOST=localhost
export POSTGRES_PORT=5432
export CORS_ALLOWED_ORIGINS=http://localhost:5500,http://127.0.0.1:5500

python manage.py makemigrations        # migration is already included; safe to re-run
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

`settings.py` also reads `DJANGO_SECRET_KEY`, `DJANGO_DEBUG`, `DJANGO_ALLOWED_HOSTS`, and `CSRF_TRUSTED_ORIGINS` (defaults to `CORS_ALLOWED_ORIGINS`). For production: `DJANGO_DEBUG=0`, a random secret key, a strict `ALLOWED_HOSTS`, and HTTPS.

## 3) Run the frontend

Do **not** open the file via `file://` (the `null` origin is blocked by CORS). Use a tiny local server:

```bash
cd ..                                   # folder containing index.html
python -m http.server 5500 --directory .
# then open: http://localhost:5500/index.html
```

The single integration point at the top of the `index.html` script:

```js
const API_ENDPOINT = "http://localhost:8000/api/registrations/";
```

Change it to your real server address on deployment and add the frontend origin to `CORS_ALLOWED_ORIGINS`. If the UI is served from the same origin as Django, the request becomes same-origin and CORS settings are unnecessary.

> The browser needs internet access to load Tailwind CDN and jsPDF from their CDNs. The rest of the UI (logo, core layout, navigation) still works offline thanks to embedded CSS. For a fully self-contained production build, replace Tailwind Play CDN with a precompiled CSS file and bundle jsPDF locally.

## 4) API contract

**`POST /api/registrations/`** — `multipart/form-data`

| Field | Type | Notes |
|---|---|---|
| `full_name` | text | required, ≤ 150 chars |
| `department` | text | required, ≤ 150 chars |
| `school_year` | text | required, one of `1` … `6` |
| `email` | email | required, valid format, **unique** |
| `certificate_pdf` | file | required, PDF only, ≤ 15MB, `.pdf` extension and `%PDF-` signature |

Success `201`:

```json
{"success": true, "message": "Your CODING AI registration was saved successfully.", "id": 1,
 "certificate_url": "http://localhost:8000/media/certificates/2026/10/<uuid>/certificate_....pdf",
 "created_at": "2026-10-25T14:00:00.000000+00:00"}
```

Failure `400` (or `405` / `500`):

```json
{"success": false, "message": "The request data is incomplete or invalid.",
 "errors": {"email": "Invalid email address format.", "certificate_pdf": "..."}}
```

## Technical decisions (documented in code)

- **Duplicates:** `email` is unique and stored lowercase; a repeated registration returns a clear `400`, with an `IntegrityError` fallback for races.
- **CSRF:** the view is marked `@csrf_exempt` with an inline explanation (standalone single-file UI from another origin + exactly one request). This is compensated by restricted CORS origins and full input validation. The frontend sends `X-CSRFToken` automatically when the cookie exists, and `django-cors-headers` answers the preflight request. To move the UI onto the Django origin, remove the decorator and use `ensure_csrf_cookie`.
- **Files:** `MEDIA_ROOT = backend/media`, path `certificates/YYYY/MM/<uuid>/<name>.pdf`, served via `static()` in development. In production swap in `django-storages` (S3/GCS) without touching the model or view.
- **Security:** MIME type + extension + `%PDF-` signature + size checks. Non-images and HEIC/SVG are rejected in the browser before conversion.
- **Dependencies:** the frontend uses only Tailwind CDN and jsPDF; fonts are system fonts and icons are inline SVGs.

## Replacing the logo (optional)

```bash
python - <<'PY'
import base64, pathlib
uri = "data:image/png;base64," + base64.b64encode(pathlib.Path("image.png").read_bytes()).decode()
print(uri[:80] + "...")   # paste the full string into the src of .brand-logo and .success-logo
PY
```
