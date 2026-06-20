.PHONY: dev prod stop logs test lint shell clean build

dev:
	docker compose up --build

prod:
	docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

stop:
	docker compose down -v

logs:
	docker compose logs -f

test:
	docker compose run --entrypoint "pytest" app

lint:
	docker compose run --entrypoint "ruff check" app

shell:
	docker compose exec app /bin/bash

clean:
	docker compose down -v
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	find . -type d -name "__pycache__" -exec rm -r {} +
