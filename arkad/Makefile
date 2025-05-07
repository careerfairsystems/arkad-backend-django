.PHONY: install check ruff mypy mypy-strict mypy-server clean dev lint

# Project configuration
PROJECT_DIR = .
CONFIG_FILE = pyproject.toml

# Installation
install:
	pip install -r ../requirements.txt

# Development server
dev:
	cd $(PROJECT_DIR) && python manage.py runserver

# Linting and formatting
ruff:
	cd $(PROJECT_DIR) && ruff check . --fix
	cd $(PROJECT_DIR) && ruff format .

# Type checking
mypy:
	@if command -v dmypy >/dev/null 2>&1; then \
		cd $(PROJECT_DIR) && dmypy run -- --config-file $(CONFIG_FILE) .; \
	else \
		cd $(PROJECT_DIR) && mypy --config-file $(CONFIG_FILE) .; \
	fi

mypy-strict:
	@if command -v dmypy >/dev/null 2>&1; then \
		cd $(PROJECT_DIR) && dmypy run -- --config-file $(CONFIG_FILE) . --follow-imports=skip; \
	else \
		cd $(PROJECT_DIR) && mypy --config-file $(CONFIG_FILE) . --follow-imports=skip; \
	fi

mypy-server:
	@if command -v dmypy >/dev/null 2>&1; then \
		cd $(PROJECT_DIR) && dmypy start -- --config-file $(CONFIG_FILE); \
	else \
		echo "dmypy not found - install with: pip install mypy>=1.0.0"; \
		exit 1; \
	fi

# Cleanup
clean:
	@if command -v dmypy >/dev/null 2>&1; then \
		dmypy stop; \
	fi


# Combined checks
check: ruff mypy
lint: mypy