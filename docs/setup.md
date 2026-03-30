# Setup Instructions

## Local Development
1. Create virtual environment.
2. Install packages with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and update DB settings.
4. Run `python manage.py makemigrations`.
5. Run `python manage.py migrate`.
6. Start FastAPI service on port `8001`:
	`uvicorn backend.fastapi_service.main:app --host 127.0.0.1 --port 8001 --reload`
7. Start Django service on port `8000`:
	`python manage.py runserver 127.0.0.1:8000`

## Documentation Workflow
- Track execution status in `docs/sprint_tracker.md` using checklist marks.
- Record key milestone completion in `docs/progress_log.md`.
- Keep endpoint and dataflow references synchronized in `docs/api.md` and `docs/architecture.md`.

## PostgreSQL Configuration
Set the following values in `.env`:
- `DB_ENGINE=postgres`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `POSTGRES_HOST`
- `POSTGRES_PORT`

## SQLite Development Mode
Set:
- `DB_ENGINE=sqlite`
- `SQLITE_PATH=./db.sqlite3`
