# Get started with Python

## Python version
You must use Python 3.13 to run this project as we are using some very new typing features.

## First install steps

1. Install Python 3.13
2. Create a virtual environment (venv) `python3.13 -m venv venv`
3. Activate the virtual environment
    - On Windows: `venv\Scripts\activate` (If using windows please use WSL, otherwise make commands will not work)
    - On Linux/Mac: `source venv/bin/activate`
4. cd to the arkad folder `cd arkad`.
    - This is where the django project is located.
5. Install the required packages: `pip install -r requirements.txt`
6. Create a public/private keypair for JWT signing
    - With the names public.pem, private.pem, they should be in arkad/private folder
    - This can be done with:
      ```shell
      mkdir private
      openssl genpkey -algorithm RSA -out private/private.pem -pkeyopt rsa_keygen_bits:2048
      openssl rsa -in private/private.pem -pubout -out private/public.pem
      ```
7. Copy `example.env` to `.env` (Both are in arkad folder)
    - This contains the default environment variables.
8. Start the Postgres database if not running it locally.
8. Start services (database, redis, web, celery worker, celery beat) using docker: from the `arkad` folder run:
9. Create migrations: `python manage.py makemigrations`
10. Migrate the database: `python manage.py migrate`
11. Create the cache database `python manage.py createcachetable`
12. Run the server: `python manage.py runserver`
13. Open your browser and go to `http://127.0.0.1:8000/api/docs` to see the API documentation.

# Arkad backend

   - Celery beat scheduler (celery-beat)
   - Start celery using `celery -A arkad worker -l info` if not using docker compose.

## API

The API is documented at /api/docs

### Required environment variables

Required environment variables are:
- SECRET_KEY (Set this to a long secret value)
- DEBUG (Must be set to "False" in production)
- POSTGRES_PASSWORD (The postgres database password for the user arkad_db_user)

### Testing with docker
## Celery (worker + beat)
- Uses Redis for broker and result backend.
- Two services run via compose: `celery-worker` and `celery-beat`.
- Worker processes tasks; beat schedules periodic tasks.
- Run manually (outside compose):
Ran with: `docker compose up`

  celery -A arkad beat -l info
### Deployment
- Define tasks in any app `tasks.py`:
When deploying you must set DEBUG environment value to False.
Also make sure to set a secure secret key as it is otherwise possible to high-jack sessions.
You should also set a good postgres password.

### Creating a superuser in docker

Enter the bash with: `docker compose run web bash`
- Add periodic tasks by creating (or editing) `arkad/celery.py` or a dedicated module and using Celery signals, e.g.:
  ```python
  from celery.schedules import crontab
  from .celery import app

  app.conf.beat_schedule = {
      "example-task-every-minute": {
          "task": "email_app.tasks.example_task",
          "schedule": crontab(minute="*"),
          "args": (1, 2),
      }
  }
  ```
  (Adjust task path / schedule as needed.)
Follow the instructions.

### Update company information

It is possible to automatically update the database with new information about all companies.
For example jobs, if they have studentsessions etc.
This is done by running `python manage.py jexpo_sync --file /path/to/jexpo.json`

Jexpo information can also be uploaded via the admin page (this is useful primarily in production/staging).
### Linting and formatting rules

Migrations files are excluded from ruff formatting and are only checked to be legal by mypy.
- app/migrations/*.py

Test files are excluded from typing rules but are required to be valid code and formatting is applied.
-   tests/*
-   */tests.py

api files are not required to have typed return values.
- */api.py

Run the linting by standing in arkad and writing `make lint`

### Run tests

Run tests using `python manage.py test`

### CI

When pushing linting and tests will be run automatically.
And when a new commit is added to master it is auto deployed.

