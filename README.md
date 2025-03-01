# Arkad backend

This backend uses django and postgres as the database

## API

The API is documented at /api/docs

### Required environment variables

Required environment variables are:
- SECRET_KEY (Set this to a long secret value), Used for signing JWT and sessions.
- DEBUG (Must be set to "False" in production)
- POSTGRES_PASSWORD (The postgres database password for the user arkad_db_user)

### Testing with docker

If testing locally using docker debug should be True.

Can be built using: `docker compose build`
Ran with: `docker compose up`

### Deployment

When deploying you must set DEBUG environment value to False.
Also make sure to set a secure secret key as it is otherwise possible to high-jack sessions.
You should also set a good postgres password.

### Creating a superuser in docker

Enter the bash with: `docker compose run web bash`
Enter the shell utility: `python manage.py createsuperuser`
Follow the instructions.