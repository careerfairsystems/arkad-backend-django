# Arkad backend

This backend uses django and postgres as the database

## API

The API is documented at /api/docs

### Required environment variables

Required environment variables are:
- SECRET_KEY (Set this to a long secret value)
- DEBUG (Must be set to "False" in production)
- POSTGRES_PASSWORD (The postgres database password for the user arkad_db_user)
