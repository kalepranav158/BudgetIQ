# Setup Instructions

## Local Development
1. Create virtual environment.
2. Install packages with `pip install -r requirements.txt`.
3. Copy `.env.example` to `.env` and update DB settings.
4. Run `python manage.py makemigrations`.
5. Run `python manage.py migrate`.
6. Start FastAPI service on port `8001`.
7. Start Django service on port `8000`.

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
