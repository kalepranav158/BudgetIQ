# BrainIQ Frontend

## Setup

1. Copy `.env.example` to `.env`.
2. Install dependencies with `npm install`.
3. Ensure Django is running on `127.0.0.1:8000` and FastAPI on `127.0.0.1:8001`.
4. Run the dev server with `npm run dev`.

## Environment Variables

- `VITE_DJANGO_URL=http://127.0.0.1:8000`
- `VITE_FASTAPI_URL=http://127.0.0.1:8001`

## Scripts

- `npm run dev` - start the Vite development server
- `npm test` - run frontend unit tests
- `npm run build` - build the production bundle
- `npm run preview` - preview the production build

## Notes

- In development, API calls use Vite proxies (`/django-api`, `/fastapi-api`) to avoid browser CORS issues.
- Health cards still display the real target backend URLs from environment variables.

## Routes

- `/upload`
- `/transactions`
- `/summaries/daily`
- `/summaries/monthly`
- `/mappings`
- `/health`
