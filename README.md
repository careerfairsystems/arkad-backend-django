# Arkad backend

This backend uses django and postgres as the database

## API

The API is documented at /api/docs

## Private/Public keys

To run the server locally the user must manually create a RS256 public/private keypair and add them in arkad/private,
With the names public.pem, private.pem

This can be done with:
```shell
openssl genpkey -algorithm RSA -out private.pem -pkeyopt rsa_keygen_bits:2048
openssl rsa -in private.pem -pubout -out public.pem
```

You can then run jwt_utils in arkad if you want to test the setup.

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

### Update company information

It is possible to automatically update the database with new information about all companies.
For example jobs, if they have studentsessions etc. 
This is done by running `python manage.py jexpo_sync --file /path/to/jexpo.json`

### Linting and formatting rules

Migrations files are excluded from ruff formatting and are only checked to be legal by mypy.
- app/migrations/*.py

Test files are excluded from typing rules but are required to be valid code and formatting is applied.
-   tests/*
-   */tests.py

api files are not required to have typed return values.
- */api.py
