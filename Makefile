.PHONY: run test test-e2e test-ci lint format coverage migrate build-css

build-css:
	npm run build:css

run:
	python manage.py runserver

migrate:
	python manage.py migrate

test:
	pytest

test-e2e:
	pytest -m e2e --no-cov

test-ci: build-css
	python manage.py migrate --noinput
	pytest
	python -m playwright install chromium
	pytest -m e2e --no-cov

coverage:
	coverage run -m pytest && coverage report

lint:
	ruff check apps config

format:
	black apps config
