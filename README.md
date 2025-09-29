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
9. Start services (database, redis, web, celery worker, celery beat) using docker: from the `arkad` folder run:
    ```shell
    docker compose up
    ```
10. Create migrations: `python manage.py makemigrations`
11. Migrate the database: `python manage.py migrate`
12. Create the cache database `python manage.py createcachetable`
13. Run the server: `python manage.py runserver`
14. Open your browser and go to `http://127.0.0.1:8000/api/docs` to see the API documentation.

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


## Scheduling tasks

- Celery beat is used to schedule periodic tasks which can be created from the admin interface at /admin under "Periodic tasks".
- The tasks which are to be created must be defined in a tasks.py file in any app.
- The tasks must be decorated with `@shared_task` from celery.
- There is an example task in arkad/arkad/celery.py.

### Testing with docker
## Celery (worker + beat)
- Uses Redis for broker and result backend.
- Two services run via compose: `celery-worker` and `celery-beat`.
- Worker processes tasks; beat schedules periodic tasks.
- Run manually (outside compose):
Ran with: `docker compose up`
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

# General Django Tips

## DB

- To create a new app: `python manage.py startapp app_name`
- To create migrations: `python manage.py makemigrations`: This will create migration files for any changes in models.
- To migrate the database: `python manage.py migrate`: This will apply the migrations to the database.

### Creating new fields

When creating new fields in models it is important to set a default value or allow null values.
Otherwise, the migration will fail if there are existing rows in the database.

#### Adding fields to existing models

Adding fields to existing models is very simple in django, simply go to the model, for example `class User(AbstractBaseUser)`
And add the new field, for example:
```python
    push_token = models.CharField(max_length=255, blank=True, null=True)
```

## Admin Interface

Django comes with an admin interface from where data can be edited, created or deleted. It is also possible to create new users and assign them to groups with different permissions.

An additional feature of the admin interface is that it is possible to create actions for each table. For example, it is possible to create an action to email all selected users.

### Actions

Actions are created by defining a function and adding it to the `actions` list in the admin class.
For more information see the [Django documentation](https://docs.djangoproject.com/en/5.2/ref/contrib/admin/actions/).

It is also possible to create actions which take input, they can be seen here: [Stack Overflow](https://stackoverflow.com/a/63644851/11836881).

