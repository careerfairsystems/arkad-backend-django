.PHONY: lint type-check all

install:
	pip install -r requirements.txt

lint:
	ruff check arkad --fix
	ruff format arkad --fix

type-check:
	dmypy status || dmypy start
	dmypy check arkad

check: lint type-check

dev:
	cd arkad && python manage.py runserver