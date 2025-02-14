.PHONY: lint type-check all

install:
	pip install -r requirements.txt

lint:
	ruff check arkad

type-check:
	dmypy status || dmypy start
	dmypy check arkad

check: lint type-check

dev:
	cd arkad && python manage.py runserver